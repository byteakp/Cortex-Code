import os
import datetime

from .llm_handler import LLMHandler
from .sandbox import CodeSandbox
from database.database import get_db
from database.models import Session, Message
from visualizer.image_generator import ImageGenerator


class SelfCorrectingAgent:
    """
    A self-correcting agent that iteratively generates and refines code 
    to solve a given problem based on test cases.
    """
    def __init__(self, model: str, max_attempts: int):
        """
        Initializes the SelfCorrectingAgent.

        Args:
            model (str): The name of the LLM model to use.
            max_attempts (int): The maximum number of attempts to solve the problem.
        """
        self.llm_handler = LLMHandler(model=model)
        self.sandbox = CodeSandbox()
        self.image_generator = ImageGenerator()
        self.max_attempts = max_attempts
        self.db_session = next(get_db())

    def save_final_code(self, code: str, session_id: int) -> str:
        """
        Saves the final generated code to a file.

        Args:
            code (str): The final code to save.
            session_id (int): The ID of the current session.

        Returns:
            str: The path to the saved code file.
        """
        os.makedirs("outputs/code", exist_ok=True)  # Create directory if it doesn't exist
        file_path = f"outputs/code/solution_session_{session_id}.py"
        with open(file_path, "w") as f:
            f.write(code)
        return file_path

    def run(self, problem: str, test_cases: str):
        """
        Runs the self-correcting agent to solve a given problem.

        Args:
            problem (str): The problem statement.
            test_cases (str): The test cases for the problem.

        Yields:
            dict: A dictionary containing information about the agent's progress.
        """
        session = Session(problem_statement=problem, test_cases=test_cases)
        self.db_session.add(session)
        self.db_session.commit()
        self.db_session.refresh(session)
        session_id = session.id

        yield {'type': 'start', 'session_id': session_id, 'problem': problem}

        current_code = ""
        last_error = {}

        for attempt in range(1, self.max_attempts + 1):
            yield {'type': 'status', 'message': f"Attempt {attempt}/{self.max_attempts}: Thinking..."}

            try:
                if attempt == 1:
                    thought, code = self.llm_handler.generate_initial_code(problem, test_cases)
                else:
                    thought, code = self.llm_handler.correct_code(problem, current_code, last_error.get('stdout', ''), last_error.get('stderr', ''))

                if not code:
                    yield {'type': 'error', 'message': "LLM failed to generate code. Aborting."}
                    break
                current_code = code
            except Exception as e:
                yield {'type': 'error', 'message': f"Error calling LLM: {e}. Aborting."}
                session.status = "failed"
                self.db_session.commit()
                return

            yield {'type': 'thought', 'content': thought}

            image_path = self.image_generator.generate_image_from_thought(thought, session_id, attempt)
            if image_path:
                yield {'type': 'image', 'path': image_path}

            message = Message(session_id=session_id, attempt=attempt, thought=thought, generated_code=code, image_path=image_path)
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
                yield {'type': 'status', 'message': "✅ All tests passed! Problem solved."}
                session.status = "completed"
                session.end_time = datetime.datetime.utcnow()
                session.final_code = current_code
                self.db_session.commit()
                saved_path = self.save_final_code(current_code, session_id)
                yield {'type': 'done', 'final_code': current_code, 'saved_path': saved_path}
                return

        yield {'type': 'error', 'message': f"Agent failed to solve the problem after {self.max_attempts} attempts."}
        session.status = "failed"
        session.end_time = datetime.datetime.utcnow()
        self.db_session.commit()