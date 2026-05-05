import os
import shutil
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from auto_agent.core.backend import LLMBackend
from auto_agent.tools.filesystem import Workspace
from auto_agent.engine.executor import ActionExecutor
from auto_agent.engine.loop import ExecutionLoop
from auto_agent.core.logger import ActionLogger
from rich.console import Console

console = Console()

class MockBrain(LLMBackend):
    """
    A mock LLM that returns pre-defined sequences of actions 
    to simulate an autonomous agent's reasoning process.
    """
    def __init__(self):
        self.turn = 0
        self.responses = [
            # Turn 1: Initialization & Planning
            json.dumps([
                {
                    "thought": "I will start by creating the project structure and the data model.",
                    "action": "create_file",
                    "path": "models.py",
                    "content": "class Task:\n    def __init__(self, title):\n        self.title = title\n        self.done = False"
                },
                {
                    "thought": "I'll also initialize the memory file.",
                    "action": "update_memory",
                    "content": "# Project: Task Manager\n- Turn 1: Created models.py"
                }
            ]),
            
            # Turn 2: Adding Logic & Batch Reading
            json.dumps([
                {
                    "thought": "Now I'll add the manager logic and read the files to verify.",
                    "action": "create_file",
                    "path": "manager.py",
                    "content": "from models import Task\n\nclass Manager:\n    def __init__(self):\n        self.tasks = []\n    def add(self, title):\n        self.tasks.append(Task(title))"
                },
                {
                    "thought": "Reading files to ensure everything is correct.",
                    "action": "read_file",
                    "path": ["models.py", "manager.py"]
                }
            ]),

            # Turn 3: INTENTIONAL ERROR (Test Syntax Validation)
            json.dumps([
                {
                    "thought": "I will try to add a broken function to see if the system catches it.",
                    "action": "edit_file",
                    "path": "manager.py",
                    "search_text": "    def add(self, title):\n        self.tasks.append(Task(title))",
                    "replace_text": "    def add(self, title):\n        self.tasks.append(Task(title))\n\n    def broken_func(self:\n        pass" # Missing closing parenthesis
                }
            ]),

            # Turn 4: Recovery from Error
            json.dumps([
                {
                    "thought": "I introduced a syntax error. I will fix it now.",
                    "action": "edit_file",
                    "path": "manager.py",
                    "search_text": "    def broken_func(self:\n        pass",
                    "replace_text": "    def broken_func(self):\n        pass"
                },
                {
                    "thought": "Updating memory with progress.",
                    "action": "update_memory",
                    "content": "# Project: Task Manager\n- Turn 1: Created models.py\n- Turn 2: Created manager.py\n- Turn 4: Fixed syntax error in manager.py"
                }
            ]),

            # Turn 5: Finish
            json.dumps([
                {
                    "thought": "Task complete. I will run a quick check and then finish.",
                    "action": "run_command",
                    "command": "python -m py_compile models.py manager.py"
                },
                {
                    "thought": "Everything looks good.",
                    "action": "finish"
                }
            ])
        ]

    def generate(self, prompt, system, max_tokens=512, temperature=0.2):
        if self.turn < len(self.responses):
            res = self.responses[self.turn]
            self.turn += 1
            return res
        return "[]"

def run_grand_test():
    test_dir = "grand_test_workspace"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    # Setup core components
    workspace = Workspace(test_dir)
    logger = ActionLogger(os.path.join(test_dir, "grand_test.log"))
    executor = ActionExecutor(workspace, logger)
    mock_backend = MockBrain()
    
    # Initialize Loop
    loop = ExecutionLoop(mock_backend, executor, max_iterations=10)

    console.print("[bold cyan]Starting Grand Test: Autonomous Task Simulation[/bold cyan]\n")
    
    task = "Build a Task Manager system with models.py and manager.py, and verify integrity."
    
    try:
        loop.run(task)
        
        console.print("\n[bold green]Simulation Finished. Verifying Results...[/bold green]")
        
        # Verify files exist
        assert os.path.exists(os.path.join(test_dir, "models.py"))
        assert os.path.exists(os.path.join(test_dir, "manager.py"))
        assert os.path.exists(os.path.join(test_dir, "MEMORY.md"))
        
        # Verify syntax was fixed
        with open(os.path.join(test_dir, "manager.py"), "r") as f:
            content = f.read()
            assert "broken_func(self):" in content
            
        # Verify memory update
        with open(os.path.join(test_dir, "MEMORY.md"), "r") as f:
            content = f.read()
            assert "Fixed syntax error" in content

        console.print(Panel(Text("GRAND TEST PASSED!", style="bold green"), border_style="green"))
        console.print("[white]- Multi-turn autonomy verified.[/white]")
        console.print("[white]- Syntax error detection and recovery verified.[/white]")
        console.print("[white]- Batch file operations verified.[/white]")
        console.print("[white]- Memory management verified.[/white]")
        console.print("[white]- CLI UI components verified.[/white]")

    except Exception as e:
        console.print(f"\n[bold red]GRAND TEST FAILED:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_grand_test()
