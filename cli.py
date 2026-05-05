import argparse
import sys
import os
from auto_agent.core.backend import build_backend
from auto_agent.tools.filesystem import Workspace
from auto_agent.engine.executor import ActionExecutor
from auto_agent.engine.loop import ExecutionLoop

def main():
    parser = argparse.ArgumentParser(description="Auto-Agent: A local, LLM-powered autonomous CLI coding agent.")
    parser.add_argument("task", type=str, help="The task for the agent to perform.")
    parser.add_argument("--backend", type=str, choices=["ollama", "llamacpp"], default="ollama", help="LLM backend to use.")
    parser.add_argument("--model", type=str, default="gemma", help="Model name (for Ollama).")
    parser.add_argument("--url", type=str, help="Base URL for the LLM backend.")
    parser.add_argument("--workspace", type=str, default="./aether_workspace", help="Path to the workspace directory.")
    parser.add_argument("--max-iter", type=int, default=5, help="Maximum number of iterations.")

    args = parser.parse_args()

    # 1. Setup Backend
    backend_kwargs = {}
    if args.url:
        backend_kwargs["base_url"] = args.url
    if args.backend == "ollama":
        backend_kwargs["model"] = args.model
    
    try:
        backend = build_backend(args.backend, **backend_kwargs)
    except Exception as e:
        print(f"Error initializing backend: {e}")
        sys.exit(1)

    # 2. Setup Tools & Executor
    workspace = Workspace(args.workspace)
    executor = ActionExecutor(workspace)

    # 3. Initialize and run loop
    loop = ExecutionLoop(backend, executor, max_iterations=args.max_iter)
    
    # Pre-load context: Directory listing and Memory
    try:
        files = workspace.list_directory(".")
        initial_context = f"Current directory contains: {', '.join(files)}"
        
        # Check for MEMORY.md
        if "MEMORY.md" in files:
            memory_content = workspace.read_file("MEMORY.md")
            # Strip the line numbers from the memory content for the model's benefit
            clean_memory = "\n".join([line.split(": ", 1)[1] if ": " in line else line for line in memory_content.splitlines()])
            initial_context += f"\n\nProject Memory (MEMORY.md):\n{clean_memory}"
    except Exception:
        initial_context = ""

    try:
        loop.run(args.task, initial_context=initial_context)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
