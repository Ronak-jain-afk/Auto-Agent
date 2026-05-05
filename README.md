# Auto-Agent CLI 🤖

Auto-Agent is a **local, LLM-powered autonomous coding assistant** designed to run in your terminal. It leverages local inference engines like **Ollama** or **llama.cpp** to interpret natural language instructions and convert them into structured, executable actions on your file system.

Built with security, autonomy, and ease of use in mind, Auto-Agent can create, edit, search, and validate code entirely within a secure sandbox.

---

## ✨ Features

- 🧠 **Autonomous Planning:** Breaks down complex tasks into multiple steps.
- 🛡️ **Security Sandbox:** All operations are restricted to a specific workspace directory.
- 🔒 **Hardened Execution:**
  - Mandatory user confirmation for destructive actions (delete/overwrite).
  - Whitelisted shell commands to prevent injection.
  - Protection against path traversal and symlink attacks.
- ✅ **Automated Validation:** Automatically runs syntax checks on Python files after every edit.
- 🔍 **Advanced Search:** Integrated regex search and Python symbol discovery.
- 📑 **Context Management:** Intelligent history summarization to handle long-running tasks without losing context.
- 📦 **Professional CLI:** Interactive REPL with beautiful terminal formatting via [Rich](https://github.com/Textualize/rich).

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) or [llama.cpp](https://github.com/ggerganov/llama.cpp) running locally.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/auto-agent.git
   cd auto-agent
   ```

2. Install the tool:
   ```bash
   pip install .
   ```

---

## 🛠️ Usage

Simply run the command to start the interactive wizard:

```bash
auto-agent
```

The wizard will help you configure your backend and workspace. Once set up, you can enter tasks like:
- *"Create a task manager with a SQLite backend"*
- *"Add a login function to models.py and verify syntax"*
- *"Search the project for all instances of 'API_KEY'"*

---

## 🔒 Security Measures

Auto-Agent is built to be safe:
- **Confirmation Required:** Every `delete_file`, `overwrite`, or `run_command` requires manual 'y' confirmation.
- **No Self-Tampering:** The agent is physically blocked from accessing or modifying its own source code.
- **Hidden File Block:** Access to `.env`, `.git`, and other sensitive hidden files is strictly restricted.
- **Logging:** Every action taken by the agent is recorded in `agent_actions.log` for auditing.

---

## 🏗️ Architecture

- **Core:** Path validation, backend adapters (Ollama/LlamaCpp), and structured JSON parsing.
- **Engine:** Iterative execution loop with feedback and context summarization.
- **Tools:** Filesystem operations, shell execution, and code validation.

---

## 👤 Author

**Ronak Jain**  
📧 [ronakjain4448@gmail.com](mailto:ronakjain4448@gmail.com)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
