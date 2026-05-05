import logging
import json
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.live import Live
from rich.text import Text
from auto_agent.core.backend import LLMBackend
from auto_agent.core.prompt import SYSTEM_PROMPT
from auto_agent.core.validator import parse_and_validate_actions
from auto_agent.engine.executor import ActionExecutor

console = Console()

class ExecutionLoop:
    def __init__(self, backend: LLMBackend, executor: ActionExecutor, max_iterations: int = 5):
        self.backend = backend
        self.executor = executor
        self.max_iterations = max_iterations
        self.history: List[Dict[str, str]] = []
        self.summary: str = ""

    def run(self, user_task: str, initial_context: str = ""):
        full_user_msg = user_task
        if initial_context:
            full_user_msg = f"{initial_context}\n\nTask: {user_task}"
            
        self.history = [{"role": "user", "content": full_user_msg}]
        self.summary = ""
        
        for i in range(self.max_iterations):
            console.print(Rule(f"Iteration {i+1}/{self.max_iterations}", style="cyan"))
            
            # Context management: Summarize if history gets too long
            if len(self.history) > 8:
                self._summarize_history()

            # 1. Call LLM with history
            full_context = self._build_context()
            try:
                with console.status("[bold green]Agent is thinking..."):
                    output = self.backend.generate(prompt=full_context, system=SYSTEM_PROMPT)
                self.history.append({"role": "assistant", "content": output})
            except RuntimeError as e:
                console.print(f"[bold red]LLM Error:[/bold red] {e}")
                continue
            
            # 2. Validate and Extract Thoughts
            actions, error = parse_and_validate_actions(output)
            
            if actions:
                # Try to display thoughts if available
                thoughts = [a.get("thought") for a in actions if a.get("thought")]
                if thoughts:
                    console.print(Panel(Text("\n".join(thoughts), style="italic grey70"), title="🧠 Thinking", border_style="dim"))
            
            if error:
                console.print(f"[bold red]Model Output Error:[/bold red] {error}")
                error_msg = f"The previous output was invalid.\n{error}\nPlease return a valid JSON array of actions."
                self.history.append({"role": "user", "content": error_msg})
                continue
            
            if not actions:
                console.print("[bold yellow]Model Output:[/bold yellow] No actions returned (stopping).")
                break
                
            # 3. Execute
            console.print(f"[bold blue]Actions:[/bold blue] {len(actions)} tasks to execute...")
            feedbacks = self.executor.execute_batch(actions)
            
            # Check if any action returned an error
            any_error = any(f.startswith("ERROR") for f in feedbacks)
            
            # Check for FINISH - only exit if NO errors occurred in the batch
            if "FINISH" in feedbacks and not any_error:
                console.print(Panel(Text("Task completed successfully!", style="bold green"), border_style="green"))
                break
                
            # 4. Prepare next prompt
            feedback_str = "\n".join(feedbacks)
            self.history.append({"role": "user", "content": f"Results of previous actions:\n{feedback_str}"})
            
            if any_error:
                console.print("[bold red]Agent encountered an error in the batch. Retrying with feedback...[/bold red]")
                continue
            
        else:
            console.print(Panel(Text("Reached maximum iterations.", style="bold yellow"), border_style="yellow"))

    def _summarize_history(self):
        """Uses the LLM to summarize the middle part of the history."""
        with console.status("[bold yellow]Summarizing conversation history..."):
            to_summarize = self.history[1:-2]
            if not to_summarize:
                return

            summary_prompt = "Please provide a concise summary of the progress made and the issues encountered so far in this task. Focus on facts, file changes, and current status.\n\nCONVERSATION LOG:\n"
            for msg in to_summarize:
                summary_prompt += f"### {msg['role'].upper()}\n{msg['content']}\n\n"
            
            summary_system = "You are a helpful assistant that summarizes technical conversations. Be brief and objective."
            
            try:
                new_summary_part = self.backend.generate(prompt=summary_prompt, system=summary_system, max_tokens=256)
                
                if self.summary:
                    self.summary = f"{self.summary}\n\nPrevious Summary Update: {new_summary_part}"
                else:
                    self.summary = new_summary_part
                    
                self.history = [self.history[0]] + self.history[-2:]
                console.print("[dim yellow]Summary updated and history compressed.[/dim yellow]")
            except Exception as e:
                console.print(f"[bold red]Summarization failed:[/bold red] {e}")

    def _build_context(self) -> str:
        """Formats the history into a single string, including the summary if available."""
        if not self.history:
            return ""
            
        context = ""
        
        # 1. Add Original Task
        context += f"### ORIGINAL TASK\n{self.history[0]['content']}\n\n"
        
        # 2. Add Progress Summary if available
        if self.summary:
            context += f"### PROGRESS SUMMARY\n{self.summary}\n\n"
        
        # 3. Add recent messages (skip index 0 as it's handled above)
        for msg in self.history[1:]:
            role = msg["role"].upper()
            content = msg["content"]
            context += f"### {role}\n{content}\n\n"
        
        # Add a strict reminder at the end of every prompt
        context += "### SYSTEM REMINDER\nIMPORTANT: YOU MUST OUTPUT A SINGLE JSON ARRAY. DO NOT CLOSE THE ARRAY UNTIL ALL ACTIONS ARE INCLUDED."
        return context.strip()
