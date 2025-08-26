import os
import datetime
from typing import Dict, Generator

from .llm_handler import LLMHandler
from .sandbox import CodeSandbox
from database.database import get_db
from database.models import Session, Message
from visualizer.image_generator import ImageGenerator


class SelfCorrectingAgent:
    """
    An agent that attempts to solve a problem by generating code, testing it, and correcting it based on the results.
    """

    def __init__(self, model: str, max_attempts: int) -> None:
        """
        Initializes the SelfCorrectingAgent.

        Args:
            model: The name of the language model to use.
            max_attempts: The maximum number of attempts to solve the problem.
        """
        self.llm_handler = LLMHandler(model=model)
        self.sandbox = CodeSandbox()
        self.image_generator = ImageGenerator()
        self.max_attempts = max_attempts
        self.db_session = next(get_db())

    def save_final_code(self, code: str, session_id: int) -> str:
        """
        Saves the final corrected code to a file.

        Args:
            code: The final corrected code.
            session_id: The ID of the session.

        Returns:
            The path to the saved file.
        """
        output_dir = "outputs/code"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_path = os.path.join(output_dir, f"solution_session_{session_id}.py")
        with open(file_path, "w") as f:
            f.write(code)
        return file_path

    def run(self, problem: str, test_cases: str) -> Generator[Dict, None, None]:
        """
        Runs the self-correcting agent on a given problem and test cases.

        Args:
            problem: The problem statement.
            test_cases: The test cases for the problem.

        Yields:
            A dictionary containing information about the agent's progress.
        """
        session = Session(problem_statement=problem, test_cases=test_cases)
        self.db_session.add(session)
        self.db_session.commit()
        self.db_session.refresh(session)
        session_id = session.id

        yield {'type': 'start', 'session_id': session_id, 'problem': problem}

        current_code = ""
        last_error = {}  # Initialize to an empty dictionary

        for attempt in range(1, self.max_attempts + 1):
            yield {'type': 'status', 'message': f"Attempt {attempt}/{self.max_attempts}: Thinking..."}

            try:
                if attempt == 1:
                    # Generate initial code for the first attempt
                    thought, code = self.llm_handler.generate_initial_code(problem, test_cases)
                else:
                    # Correct the code based on the previous error
                    stdout, stderr = last_error.get('stdout', ''), last_error.get('stderr', '')
                    thought, code = self.llm_handler.correct_code(problem, current_code, stdout, stderr)

                if not code:
                    yield {'type': 'error', 'message': "LLM failed to generate code. Aborting."}
                    break  # Exit the loop if the LLM fails to generate code
                current_code = code
            except Exception as e:
                yield {'type': 'error', 'message': f"Error calling LLM: {e}. Aborting."}
                session.status = "failed"
                self.db_session.commit()
                return  # Exit the function if there's an error calling the LLM

            yield {'type': 'thought', 'content': thought}

            image_path = self.image_generator.generate_image_from_thought(thought, session_id, attempt)
            if image_path:
                yield {'type': 'image', 'path': image_path}

            message = Message(session_id=session_id, attempt=attempt, thought=thought, generated_code=code,
                              image_path=image_path)
            self.db_session.add(message)
            self.db_session.commit()

            yield {'type': 'code', 'content': code}
            yield {'type': 'status', 'message': f"Attempt {attempt}: Executing code in sandbox..."}

            result = self.sandbox.run(code, test_cases)
            last_error = result

            message.execution_result = result
            self.db_session.commit()

            yield {'type': 'result', 'data': result}

            if result['success']:
                # If the code passes all tests, mark the session as completed and save the code
                yield {'type': 'status', 'message': "✅ All tests passed! Problem solved."}
                session.status = "completed"
                session.end_time = datetime.datetime.utcnow()
                session.final_code = current_code
                self.db_session.commit()
                saved_path = self.save_final_code(current_code, session_id)
                yield {'type': 'done', 'final_code': current_code, 'saved_path': saved_path}
                return  # Exit the function if the problem is solved

        # If the loop finishes without solving the problem, mark the session as failed
        yield {'type': 'error', 'message': f"Agent failed to solve the problem after {self.max_attempts} attempts."}
        session.status = "failed"
        session.end_time = datetime.datetime.utcnow()
        self.db_session.commit()