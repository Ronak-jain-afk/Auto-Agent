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

    def run(self, user_task: str):
        print(f"\n[Task]: {user_task}")
        current_prompt = user_task
        
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1}/{self.max_iterations} ---")
            
            # 1. Call LLM
            full_context = self._build_context(current_prompt)
            try:
                output = self.backend.generate(prompt=full_context, system=SYSTEM_PROMPT)
            except RuntimeError as e:
                print(f"[LLM Error]: {e}")
                current_prompt = f"The previous request failed due to a timeout or connection issue. Please continue with the original task: {user_task}"
                continue
            
            # Debug: Print raw output
            print(f"DEBUG: Raw LLM Output:\n{output}\n")
            
            # 2. Validate
            actions, error = parse_and_validate_actions(output)
            
            if error:
                print(f"[Model Output Error]: {error}")
                current_prompt = f"The previous output was invalid.\n{error}\nPlease return a valid JSON array of actions."
                continue
            
            if not actions:
                print("[Model Output]: No actions returned (stopping).")
                break
                
            # 3. Execute
            print(f"[Actions]: {len(actions)} found.")
            feedbacks = self.executor.execute_batch(actions)
            
            # Check for FINISH
            if "FINISH" in feedbacks:
                print("[Agent]: Task finished.")
                break
                
            # 4. Prepare next prompt
            feedback_str = "\n".join(feedbacks)
            print(f"[Feedback]:\n{feedback_str}")
            current_prompt = f"Results of previous actions:\n{feedback_str}\n\nWhat is your next step?"
            
        else:
            print("\n[Warning]: Reached maximum iterations.")

    def _build_context(self, current_prompt: str) -> str:
        # Simple history concatenation for MVP
        # In more advanced versions, we'd use a chat-style history
        return current_prompt
