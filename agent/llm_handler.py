import litellm
import re
from .prompts import SYSTEM_PROMPT, INITIAL_USER_PROMPT, CORRECTION_PROMPT

def parse_llm_response(response: str) -> (str, str):
    """Parses the LLM's response to extract thought and code."""
    thought_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    code_match = re.search(r'```python(.*?)```', response, re.DOTALL)
    code = code_match.group(1).strip() if code_match else ""

    if not code: # Fallback if no ```python ``` block is found
        # Assume the remaining part of the response is code
        code = response.split('</thinking>')[-1].strip()

    return thought, code

class LLMHandler:
    def __init__(self, model: str):
        self.model = model

    def generate_initial_code(self, problem: str, test_cases: str) -> (str, str):
        """Generates the first version of the code."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": INITIAL_USER_PROMPT.format(problem=problem, test_cases=test_cases)}
        ]
        response = litellm.completion(model=self.model, messages=messages)
        content = response.choices[0].message.content
        return parse_llm_response(content)

    def correct_code(self, problem: str, code: str, stdout: str, stderr: str) -> (str, str):
        """Generates a corrected version of the code based on errors."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": CORRECTION_PROMPT.format(problem=problem, code=code, stdout=stdout, stderr=stderr)}
        ]
        response = litellm.completion(model=self.model, messages=messages)
        content = response.choices[0].message.content
        return parse_llm_response(content)
