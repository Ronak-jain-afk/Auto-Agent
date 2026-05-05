import logging
from typing import List, Dict, Any
from auto_agent.core.backend import LLMBackend
from auto_agent.core.prompt import SYSTEM_PROMPT
from auto_agent.core.validator import parse_and_validate_actions
from auto_agent.engine.executor import ActionExecutor

class ExecutionLoop:
    def __init__(self, backend: LLMBackend, executor: ActionExecutor, max_iterations: int = 5):
        self.backend = backend
        self.executor = executor
        self.max_iterations = max_iterations
        self.history: List[Dict[str, str]] = []

    def run(self, user_task: str, initial_context: str = ""):
        print(f"\n[Task]: {user_task}")
        
        full_user_msg = user_task
        if initial_context:
            full_user_msg = f"{initial_context}\n\nTask: {user_task}"
            
        self.history = [{"role": "user", "content": full_user_msg}]
        
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1}/{self.max_iterations} ---")
            
            # 1. Call LLM with history
            full_context = self._build_context()
            try:
                output = self.backend.generate(prompt=full_context, system=SYSTEM_PROMPT)
                self.history.append({"role": "assistant", "content": output})
            except RuntimeError as e:
                print(f"[LLM Error]: {e}")
                # Don't add failed requests to history, just retry
                continue
            
            # Debug: Print raw output
            print(f"DEBUG: Raw LLM Output:\n{output}\n")
            
            # 2. Validate
            actions, error = parse_and_validate_actions(output)
            
            if error:
                print(f"[Model Output Error]: {error}")
                error_msg = f"The previous output was invalid.\n{error}\nPlease return a valid JSON array of actions."
                self.history.append({"role": "user", "content": error_msg})
                continue
            
            if not actions:
                print("[Model Output]: No actions returned (stopping).")
                break
                
            # 3. Execute
            print(f"[Actions]: {len(actions)} found.")
            feedbacks = self.executor.execute_batch(actions)
            
            # Check if any action returned an error
            any_error = any(f.startswith("ERROR") for f in feedbacks)
            
            # Check for FINISH - only exit if NO errors occurred in the batch
            if "FINISH" in feedbacks and not any_error:
                print("[Agent]: Task finished.")
                break
                
            # 4. Prepare next prompt
            feedback_str = "\n".join(feedbacks)
            print(f"[Feedback]:\n{feedback_str}")
            self.history.append({"role": "user", "content": f"Results of previous actions:\n{feedback_str}"})
            
            if any_error:
                print("[Agent]: Encountered error in batch. Retrying with feedback.")
                continue
            
        else:
            print("\n[Warning]: Reached maximum iterations.")

    def _build_context(self) -> str:
        """Formats the history into a single string, always preserving the original task."""
        if not self.history:
            return ""
            
        # ALWAYS include the very first message (the user task)
        # Then include the last 4 messages to keep context of the current error/state
        important_history = [self.history[0]]
        if len(self.history) > 1:
            important_history.extend(self.history[-4:])
        
        context = ""
        for msg in important_history:
            role = msg["role"].upper()
            content = msg["content"]
            context += f"### {role}\n{content}\n\n"
        
        # Add a strict reminder at the end of every prompt
        context += "### SYSTEM REMINDER\nIMPORTANT: YOU MUST OUTPUT A SINGLE JSON ARRAY. DO NOT CLOSE THE ARRAY UNTIL ALL ACTIONS ARE INCLUDED."
        return context.strip()
