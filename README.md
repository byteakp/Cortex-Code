#  Cortex: A Self-Correcting Code Agent

An autonomous AI agent that reasons, writes, tests, and debugs Python code in a secure sandbox.

---<img width="1689" height="693" alt="Screenshot from 2025-08-20 08-14-56" src="https://github.com/user-attachments/assets/3e9bac52-6e4e-40a2-b758-778e2d758b02" />
<img width="839" height="447" alt="Screenshot from 2025-08-20 09-06-49" src="https://github.com/user-attachments/assets/80552f0f-0fa5-4e86-bdca-d2b50db17272" />



## ✨ How It Works
Cortex operates on a few core principles to autonomously solve programming challenges.

| Concept                | Description                                                                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| 🧠 Autonomous Reasoning | Utilizes a ReAct (Reason + Act) framework to think step-by-step, analyzing errors and planning corrections without human intervention.        |
| 🛡️ Secure Execution    | All generated code is executed in an isolated Docker container, preventing any access to your local system and ensuring safety.               |
| 🎨 Thought Visualization | Translates its internal monologue into abstract art using the FLUX.1 image model, offering a unique glimpse into the AI's "Chain of Thought". |
| 🔌 LLM Agnostic         | Powered by LiteLLM, Cortex is compatible with over 100 LLMs, including specialized models like Mistral Codestral and high-speed providers like Groq. |

---

## 🛠️ Quickstart

**Prerequisites:** Python 3.9+ and Docker must be installed and running.

1. **Clone & Configure**  
   Clone the repository and set up your environment file.  
   Add your API key (e.g., `GROQ_API_KEY` or `MISTRAL_API_KEY`) inside `.env`.

2. **Build the Sandbox**  
   Build the secure Docker image for code execution (one-time setup).

3. **Install & Run**  
   Create a virtual environment, install dependencies, and launch the application.

---

## 💻 Tech Stack
This project is built with a modern, powerful stack:
- **Python 3.9+**  
- **Docker (Isolated Sandbox)**  
- **LiteLLM (Multi-LLM Compatibility)**  
- **Mistral Codestral / Groq (High-Performance LLMs)**  
- **FLUX.1 (Thought-to-Art Model)**  
