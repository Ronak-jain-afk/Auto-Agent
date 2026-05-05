import argparse
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from auto_agent.core.backend import build_backend
from auto_agent.tools.filesystem import Workspace
from auto_agent.engine.executor import ActionExecutor
from auto_agent.engine.loop import ExecutionLoop

console = Console()

def startup_wizard():
    console.clear()
    console.print(Panel(Text("Auto-Agent Setup Wizard", style="bold magenta", justify="center")))
    
    backend_type = Prompt.ask("Select LLM Backend", choices=["ollama", "llamacpp"], default="ollama")
    
    url = None
    if Confirm.ask("Do you want to specify a custom Base URL?"):
        default_url = "http://localhost:11434" if backend_type == "ollama" else "http://localhost:8080"
        url = Prompt.ask("Enter Base URL", default=default_url)
        
    model = "gemma"
    if backend_type == "ollama":
        model = Prompt.ask("Enter Ollama Model Name", default="gemma")
        
    workspace_path = Prompt.ask("Enter Workspace Path", default="./aether_workspace")
    
    return {
        "backend": backend_type,
        "url": url,
        "model": model,
        "workspace": workspace_path
    }

def main():
    config = startup_wizard()
    
    # 1. Setup Backend
    backend_kwargs = {}
    if config["url"]:
        backend_kwargs["base_url"] = config["url"]
    if config["backend"] == "ollama":
        backend_kwargs["model"] = config["model"]
    
    try:
        with console.status("[bold green]Initializing backend..."):
            backend = build_backend(config["backend"], **backend_kwargs)
    except Exception as e:
        console.print(f"[bold red]Error initializing backend:[/bold red] {e}")
        sys.exit(1)

    # 2. Setup Tools & Executor
    workspace = Workspace(config["workspace"])
    executor = ActionExecutor(workspace)

    # 3. Initialize Loop
    loop = ExecutionLoop(backend, executor, max_iterations=10)
    
    console.print(f"\n[bold green]Ready![/bold green] Workspace: [cyan]{config['workspace']}[/cyan]")
    console.print("Type your task below. Type [bold red]'exit'[/bold red] or [bold red]'quit'[/bold red] to leave.\n")

    # REPL Setup
    session = PromptSession(style=Style.from_dict({
        'prompt': 'bold magenta',
    }))

    while True:
        try:
            # Multi-line input for complex tasks
            user_input = session.prompt("Auto-Agent ❯ ", multiline=False).strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                console.print("[bold yellow]Goodbye![/bold yellow]")
                break

            # Pre-load context per command
            try:
                files = workspace.list_directory(".")
                initial_context = f"Current directory contains: {', '.join(files)}"
                if "MEMORY.md" in files:
                    memory_content = workspace.read_file("MEMORY.md")
                    clean_memory = "\n".join([line.split(": ", 1)[1] if ": " in line else line for line in memory_content.splitlines()])
                    initial_context += f"\n\nProject Memory (MEMORY.md):\n{clean_memory}"
            except Exception:
                initial_context = ""

            loop.run(user_input, initial_context=initial_context)
            console.print("\n" + "─" * console.width + "\n")

        except KeyboardInterrupt:
            continue # Clear line on Ctrl+C
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
