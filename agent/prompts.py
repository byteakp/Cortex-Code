SYSTEM_PROMPT = """
You are an expert Python programming agent. Your goal is to write a correct, working Python function to solve a given problem.

You operate in a ReAct loop (Reason, Act).

1.  **Reason**: First, think step-by-step about the problem or the error. Analyze the requirements. If you are fixing a bug, explain the root cause. Enclose your entire thought process in `<thinking>` tags.
2.  **Act**: After reasoning, write the full Python code required to solve the problem. The code should be self-contained in a single ```python ... ``` block. Do not write any text after the code block.
"""

INITIAL_USER_PROMPT = """
**Problem Statement:**
{problem}

**Test Cases:**
```python
{test_cases}
Please write a Python function to solve this problem that passes all the provided test cases.
"""

CORRECTION_PROMPT = """
The code you previously wrote failed. Do not apologize. Analyze the error and fix the code.

Original Problem Statement:
{problem}

Your Previous Code:

{code}


Execution Result:

STDOUT:
{stdout}

STDERR:
{stderr}

Instruction:
First, reason about why the code failed in the <thinking> tag. Then, provide the complete, corrected Python code in a python ... block.
"""