# 🚀 Self-Correcting Code Writer Agent

This project is a fully autonomous AI agent that can write, test, and debug Python code to solve programming problems. It uses a **ReAct (Reason + Act)** framework, a secure **Docker sandbox** for execution, and a powerful **Chain of Thought (CoT)** visualization feature that generates images representing its thought process.

![Agent in Action](https://i.imgur.com/example.gif) ## ✨ Features

-   **Autonomous Correction:** Automatically fixes runtime and logic errors.
-   **Secure Execution:** Code is run in an isolated Docker container to prevent security risks.
-   **Chain of Thought Visualization:** The agent's reasoning is turned into an image using the `FLUX.1-schnell` model.
-   **Persistent Logging:** Every step of the process is saved to an SQLite database.
-   **LLM Agnostic:** Built with `litellm` to support a wide range of models.
    -   ✅ **Mistral Codestral**: Optimized for code generation.
    -   ✅ **Groq API**: Blazing-fast inference for models like Llama3.
    -   ✅ OpenAI, Anthropic, Google Gemini, and 100+ more.

## 🛠️ Setup and Installation

### Prerequisites

-   Python 3.9+
-   Docker installed and running.
-   An LLM API Key from a supported provider (Mistral, Groq, OpenAI, etc.).

### Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd self_correcting_code_agent
    ```

2.  **Set up environment variables:**
    -   Copy the example `.env` file:
        ```bash
        cp .env.example .env
        ```
    -   **Edit the `.env` file and choose ONE provider** by uncommenting its section and adding your API key.

    -   **Example for Mistral Codestral:**
        ```
        # MISTRAL_API_KEY="your_mistral_api_key_here"
        # LLM_MODEL="codestral/codestral-latest"
        ```

    -   **Example for Groq:**
        ```
        # GROQ_API_KEY="your_groq_api_key_here"
        # LLM_MODEL="groq/llama3-8b-8192"
        ```

3.  **Install dependencies:**
    -   It's highly recommended to use a virtual environment.
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
        ```
    -   Install the required packages:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Build the Docker image:**
    -   The agent needs a sandbox environment to run code. Build it once with this command:
        ```bash
        docker build -t python_sandbox .
        ```

## 🏃‍♀️ How to Run

Simply execute the main script:

```bash
python main.py