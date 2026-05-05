# Auto-Agent CLI

Auto-Agent is a professional-grade, autonomous coding assistant designed for local development environments. It utilizes Large Language Models (LLMs) to interpret natural language instructions and execute structured actions—such as file creation, modification, and system commands—within a secure, sandboxed workspace.

The system supports both local inference engines for data privacy and high-performance cloud-based APIs for advanced reasoning capabilities.

---

## Core Features

*   **Autonomous Planning:** Deconstructs complex user requirements into sequential, multi-step execution plans.
*   **Security Sandbox:** Restricts all file operations to a designated workspace directory to prevent unauthorized system access.
*   **Hardened Execution:**
    *   Mandatory user authorization for destructive operations (file deletion and overwrites).
    *   Command whitelist and shell-less execution to mitigate injection risks.
    *   Integrated protection against path traversal and symbolic link attacks.
*   **Automated Validation:** Automatic syntax verification for Python source code following every modification.
*   **Comprehensive Search:** Native support for regular expression pattern matching and Python symbol discovery.
*   **Context Management:** Sophisticated history summarization logic to maintain long-term task coherence within model context limits.
*   **Interactive REPL:** A structured Command Line Interface providing real-time feedback and iterative task management.

---

## Supported Backends

Auto-Agent offers a modular backend architecture supporting the following providers:

### Local Providers
*   **Ollama:** Integration with local GGUF models.
*   **Llama.cpp:** Support for high-performance local inference.

### Cloud Providers
*   **Google Gemini:** Support for Gemini 1.5 Pro and Flash.
*   **OpenAI:** Integration with GPT-4o and legacy GPT-4 models.
*   **Anthropic:** Support for the Claude 3.5 model family.
*   **OpenRouter:** Unified access to a wide array of specialized LLMs via a single API.

---

## Installation

### Prerequisites
*   Python 3.8 or higher.
*   (Optional) A local instance of Ollama or Llama.cpp for local-only operation.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/ronakjain/auto-agent.git
   cd auto-agent
   ```

2. Install the package:
   ```bash
   pip install .
   ```

---

## Usage

Initialize the interactive configuration wizard by running:

```bash
auto-agent
```

The wizard will guide you through selecting a backend, providing necessary API credentials, and defining the target workspace. Once initialized, the agent will accept complex development tasks via the interactive prompt.

---

## Security Architecture

Auto-Agent implements a multi-layered security model:
*   **Access Control:** The agent is explicitly blocked from accessing or modifying its own source code or sensitive system directories.
*   **Resource Protection:** File creation is limited to 5MB to prevent disk exhaustion attacks.
*   **Audit Logging:** All agent actions, paths, and execution statuses are recorded in `agent_actions.log` for post-execution review.
*   **Credential Handling:** API keys are processed in-memory and are never persisted to disk by the application.

---

## Author

**Ronak Jain**  
[ronakjain4448@gmail.com](mailto:ronakjain4448@gmail.com)

---

## License

This project is licensed under the MIT License.
