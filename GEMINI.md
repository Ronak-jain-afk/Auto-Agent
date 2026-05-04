You are an senior AI Agent Engineer, building a CLI AI Agent.

You are building a **local, LLM-powered autonomous CLI coding agent** that leverages a model like Gemma 4 (served via a local inference engine such as llama.cpp) to interpret natural language instructions and convert them into structured, executable actions on a constrained file system. The system operates through a command-line interface, where user prompts are processed by the model to generate tool-oriented outputs (e.g., create, modify, or delete files), which are then executed by a controlled orchestration layer written in Python. It incorporates sandboxing, path validation, and permission checks to ensure safe interaction with the environment, and follows an iterative feedback loop to refine outputs, enabling semi-autonomous software development workflows within a secure, locally hosted context.

#### Core Architecture
```
User input(CLI)
    |
    |
    ▼
Planner (LLM thinking)
    |
    |
    ▼
Tool executor (your Python code)
    |
    |
    ▼
Feedback loop
```
```
CLI (Python)
   ↓
Local model server (Ollama / llama.cpp)
   ↓
Gemma 4
```
#### Must Haves(MVP)

- File create/edit/delete
- Directory awareness
- Prompt → structured JSON actions
- Execution loop
- Before editing a file, always read it first

#### Structured JSON actions example:
```
{
  "action": "create_file",
  "path": "string",
  "content": "string",
  "instruction": "..."
}
```
create_file - this action creates a file
edit_file - this action edits a file
delete_file - this action deletes a file after confirmation
read_file - this action lets the model read the file to build up context
```
{
  "create_file": ["path", "content"],
  "edit_file": ["path", "instruction"],
  "read_file": ["path"],
  "delete_file": ["path"]
}
```
#### Diff Based Editing
```
{
  "action": "edit_file",
  "path": "app.py",
  "instruction": "Add a login function with username and password validation"
}
```
#### logging format
```
{
  "timestamp": "...",
  "action": "...",
  "path": "...",
  "status": "success/fail"
}
```

#### Advanced Features For Future Scope

- Context awareness (read existing files)
- Error fixing loop
- Command execution (pip install, run code)
- Memory (project understanding)
- Diff-based editing (not full rewrite)

#### Security Measures
- Path restrictions (no system folders)
- Sandbox (project-only directory)
- Confirmation for delete actions
- Logging every action

- Define a fixed root directory (e.g. ~/aether_workspace)
- Every file operation must:
    - Resolve absolute path
    - Check it starts with your root
**Extra protections**
1. Block:
    /, C:\, system dirs
    hidden files (.env, .git)
2. Require confirmation for:
    delete
    overwrite
3. Log every action

#### Tech Stack
Python
- File handling → pathlib, os, shutil
- CLI → Typer (clean) or argparse
- LLM calls → easy HTTP / bindings
- JSON parsing → built-in

llama.cpp

---

## LLM Interface

### Canonical Internal Format

Your entire agent communicates only through this uniform interface. No part of the agent logic should depend on which backend is running underneath.

**Request:**
```json
{
  "prompt": "string",
  "system": "string",
  "max_tokens": 512,
  "temperature": 0.2
}
```

**Response:**
```json
{
  "text": "model output"
}
```

Low temperature (`0.2`) is the correct default for structured JSON output — you want determinism, not creativity.

---

### Backend Adapters

Use an abstract base class so the agent holds a reference to any `LLMBackend` without conditionals anywhere in agent logic.

```python
from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        raise NotImplementedError
```

---

#### Adapter 1 — Ollama

Endpoint: `POST /api/generate`

Ollama supports a native `system` field — use it directly instead of concatenating into the prompt string. Concatenation loses the structural separation the model was trained to expect (especially important for instruction-tuned models like Gemma 4).

```python
import requests

class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "gemma", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        res = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": system,        # native system field — do NOT concatenate
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            },
            timeout=60
        )
        res.raise_for_status()
        data = res.json()
        if "response" not in data:
            raise ValueError(f"Unexpected Ollama response shape: {data}")
        return data["response"]
```

---

#### Adapter 2 — llama.cpp

Endpoint: `POST /completion`

llama.cpp has no native system field, so prepend it manually.

```python
import requests

class LlamaCppBackend(LLMBackend):
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        full_prompt = f"{system}\n\n{prompt}"
        res = requests.post(
            f"{self.base_url}/completion",
            json={
                "prompt": full_prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
            },
            timeout=60
        )
        res.raise_for_status()
        data = res.json()
        if "content" not in data:
            raise ValueError(f"Unexpected llama.cpp response shape: {data}")
        return data["content"]
```

---

### Wiring the Agent

Select backend at startup via CLI flag or config — the agent never changes:

```python
# agent.py
def build_backend(backend: str) -> LLMBackend:
    if backend == "ollama":
        return OllamaBackend()
    elif backend == "llamacpp":
        return LlamaCppBackend()
    else:
        raise ValueError(f"Unknown backend: {backend}")

# Usage inside any agent component — backend-agnostic
output = backend.generate(prompt=user_task, system=SYSTEM_PROMPT)
```

---

###### SYSTEM PROMPT (CORE BRAIN) for the local model

```
You are an autonomous CLI coding agent.

Your job is to convert user instructions into structured JSON actions that operate on a local file system.

You MUST follow these rules strictly:

### ROLE
- You act as a planner, not an executor.
- You DO NOT execute code, only return actions.

### OUTPUT FORMAT
- You MUST always return valid JSON.
- No explanations, no markdown, no extra text.
- Only a JSON array of actions.

### AVAILABLE ACTIONS
1. create_file
2. read_file
3. edit_file
4. delete_file
5. list_directory
6. finish

### ACTION SCHEMA
Each action must follow this structure:
{
  "action": "<action_name>",
  "path": "<relative_path>",
  "content": "<string, only for create_file in the basic MVP>",
  "instruction": "<edit instruction for diff-based edits>"
}

### RULES
- All paths must be relative (no absolute paths).
- Do NOT access files outside the working directory.
- Prefer editing files instead of recreating them.
- Use minimal changes (diff-based edits).
- Break complex tasks into multiple small actions.

### SAFETY
- Never delete files unless explicitly required.
- Avoid modifying hidden or system files.
- Do not generate dangerous commands.

### THINKING
- Analyze the task step-by-step internally.
- Only output final JSON actions.

### EXAMPLE OUTPUT
[
  {
    "action": "create_file",
    "path": "app.py",
    "content": "print('Hello World')"
  }
]
```

#### OUTPUT CONSTRAINTS (STRICT CONTROL)
Hard constraints
- Must be valid JSON
- Must be array of actions
- No text outside JSON
- Only allowed actions

If the model tries to perform an undefined action reject it, so Validation is done hardcodedly. If invalid: Reject response, Send error back to model (retry)

#### Feedback loop Stopping conditions
1. When does it stop?
    - Model returns:
        ```
        []
        ```
    - OR explicit action:
        ```
        { "action": "finish" }
        ```
    - OR max iterations reached
2. Max iterations
    ```
    Max iterations = 5 (MVP)
    Max iterations = 10 (advanced)
    ```
    To:
    - Prevent infinite loops
    - Keep system fast
**Execution flow**
```
User input
   ↓
LLM generates actions
   ↓
Validate actions
   ↓
Execute actions
   ↓
Collect results/errors
   ↓
Send feedback to LLM
   ↓
Repeat (until stop)
```
#### rate/control on file size

**if**:
    file is 10,000 lines?

**You should define**:
    max read size
    truncation strategy

#### ERROR HANDLING STRATEGY

1. Validation error
    - Invalid JSON
    - Invalid action
    Response to LLM:
    ```
    ERROR: Invalid action format. Fix your JSON output.
    ```
2. Execution error
    - File not found
    - Permission denied
    Response:
    ```
    ERROR: File 'app.py' not found. Suggest creating it first.
    ```
3. Security violation
    - Path outside sandbox
    Response:
    ```
    ERROR: Access denied. Path outside allowed directory.
    ```

#### Retry logic
**Rules**:
Max file read size: 3000 lines OR 50KB
If exceeded:
- Return first N lines
- Include "...truncated..."

#### Retry prompt format

Send back to model:
```
The previous action failed.
ERROR:
File 'app.py' not found.
Fix your approach and return corrected JSON actions.
```
### ADAPTIVE BEHAVIOR
- If a file does not exist → create it
- If edit fails → read file first, then retry
- Always verify before modifying