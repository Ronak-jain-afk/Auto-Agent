from auto_agent.tools.filesystem import Workspace
from typing import Dict, Any, List

class ActionExecutor:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def execute(self, action_obj: Dict[str, Any]) -> str:
        """Executes a single action and returns a feedback string."""
        action = action_obj.get("action")
        path = action_obj.get("path")
        
        try:
            if action == "create_file":
                content = action_obj.get("content", "")
                self.workspace.create_file(path, content)
                return f"SUCCESS: File '{path}' created."
                
            elif action == "read_file":
                content = self.workspace.read_file(path)
                return f"SUCCESS: Read file '{path}':\n{content}"
                
            elif action == "list_directory":
                files = self.workspace.list_directory(path or ".")
                return f"SUCCESS: Directory listing for '{path}': {', '.join(files)}"
                
            elif action == "delete_file":
                # In a real app, this would prompt the user.
                # For the executor layer, we assume it's authorized.
                self.workspace.delete_file(path)
                return f"SUCCESS: Deleted '{path}'."
                
            elif action == "edit_file":
                # For MVP, if we don't have a diff tool, we might ask the LLM
                # to read first then recreate, or implement a basic search/replace.
                # Placeholder for now.
                return f"ERROR: 'edit_file' not fully implemented. Suggest using 'read_file' then 'create_file' to overwrite."
                
            elif action == "finish":
                return "FINISH"
                
            else:
                return f"ERROR: Action '{action}' not recognized by executor."
                
        except Exception as e:
            return f"ERROR executing '{action}' on '{path}': {str(e)}"

    def execute_batch(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Executes a list of actions and returns feedback for each."""
        results = []
        for action in actions:
            result = self.execute(action)
            results.append(result)
            if result == "FINISH":
                break
        return results
