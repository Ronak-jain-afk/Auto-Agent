from auto_agent.tools.filesystem import Workspace
from auto_agent.core.logger import ActionLogger
from typing import Dict, Any, List

class ActionExecutor:
    def __init__(self, workspace: Workspace, logger: ActionLogger = None):
        self.workspace = workspace
        self.logger = logger or ActionLogger()

    def execute(self, action_obj: Dict[str, Any]) -> str:
        """Executes a single action and returns a feedback string."""
        action = action_obj.get("action")
        path = action_obj.get("path")
        
        try:
            if action == "create_file":
                content = action_obj.get("content", "")
                if self.workspace.exists(path):
                    confirm = input(f"⚠️  File '{path}' already exists. Overwrite? (y/n): ").lower()
                    if confirm != 'y':
                        self.logger.log(action, path, "fail")
                        return f"ERROR: User denied overwrite of '{path}'."
                self.workspace.create_file(path, content)
                
                # Validation
                valid, err = self.workspace.validate_syntax(path)
                if not valid:
                    self.logger.log(action, path, "fail")
                    return f"ERROR: File '{path}' created but has syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                return f"SUCCESS: File '{path}' created and validated."
                
            elif action == "read_file":
                content = self.workspace.read_file(path)
                self.logger.log(action, str(path), "success")
                return f"SUCCESS: Read file(s):\n{content}"
                
            elif action == "list_directory":
                files = self.workspace.list_directory(path or ".")
                self.logger.log(action, path, "success")
                return f"SUCCESS: Directory listing for '{path}': {', '.join(files)}"
                
            elif action == "delete_file":
                confirm = input(f"⚠️  Are you sure you want to delete '{path}'? (y/n): ").lower()
                if confirm != 'y':
                    self.logger.log(action, path, "fail")
                    return f"ERROR: User denied deletion of '{path}'."
                self.workspace.delete_file(path)
                self.logger.log(action, path, "success")
                return f"SUCCESS: Deleted '{path}'."
                
            elif action == "edit_file":
                search_text = action_obj.get("search_text")
                replace_text = action_obj.get("replace_text")
                if search_text is None or replace_text is None:
                    self.logger.log(action, path, "fail")
                    return "ERROR: 'edit_file' requires both 'search_text' and 'replace_text' fields."
                self.workspace.edit_file(path, search_text, replace_text)
                
                # Validation
                valid, err = self.workspace.validate_syntax(path)
                if not valid:
                    self.logger.log(action, path, "fail")
                    return f"ERROR: Text replaced in '{path}' but introduced syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                return f"SUCCESS: Replaced text in '{path}' and validated."
                
            elif action == "read_file_lines":
                start = action_obj.get("start_line")
                end = action_obj.get("end_line")
                if start is None or end is None:
                    self.logger.log(action, path, "fail")
                    return "ERROR: 'read_file_lines' requires 'start_line' and 'end_line'."
                content = self.workspace.read_file_lines(path, start, end)
                self.logger.log(action, path, "success")
                return f"SUCCESS: Read lines {start}-{end} of '{path}':\n{content}"

            elif action == "edit_file_lines":
                start = action_obj.get("start_line")
                end = action_obj.get("end_line")
                content = action_obj.get("new_content")
                if start is None or end is None or content is None:
                    self.logger.log(action, path, "fail")
                    return "ERROR: 'edit_file_lines' requires 'start_line', 'end_line', and 'new_content'."
                self.workspace.edit_file_lines(path, start, end, content)
                
                # Validation
                valid, err = self.workspace.validate_syntax(path)
                if not valid:
                    self.logger.log(action, path, "fail")
                    return f"ERROR: Lines {start}-{end} replaced in '{path}' but introduced syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                return f"SUCCESS: Replaced lines {start}-{end} in '{path}' and validated."
                
            elif action == "run_command":
                command = action_obj.get("command")
                if not command:
                    self.logger.log(action, "N/A", "fail")
                    return "ERROR: Missing 'command' for 'run_command' action."
                output, success = self.workspace.run_command(command)
                status = "success" if success else "fail"
                self.logger.log(action, f"cmd: {command[:50]}", status)
                status_str = "SUCCESS" if success else "ERROR"
                return f"{status_str}: Command '{command}' executed:\n{output}"
            
            elif action == "update_memory":
                content = action_obj.get("content")
                self.workspace.update_memory(content)
                self.logger.log(action, "MEMORY.md", "success")
                return "SUCCESS: MEMORY.md updated."
                
            elif action == "search_regex":
                pattern = action_obj.get("pattern")
                if not pattern:
                    return "ERROR: 'search_regex' requires a 'pattern' field."
                results = self.workspace.search_regex(pattern)
                self.logger.log(action, f"regex: {pattern}", "success")
                return f"SUCCESS: Search results for regex '{pattern}':\n{results}"

            elif action == "find_symbols":
                query = action_obj.get("query", "")
                results = self.workspace.find_symbols(query)
                self.logger.log(action, f"query: {query}", "success")
                return f"SUCCESS: Symbol search results for '{query}':\n{results}"

            elif action == "finish":
                self.logger.log(action, "N/A", "success")
                return "FINISH"
                
            else:
                self.logger.log(action, path, "fail")
                return f"ERROR: Action '{action}' not recognized by executor."
                
        except Exception as e:
            self.logger.log(action, path, "fail")
            return f"ERROR executing '{action}' on '{path}': {str(e)}"

    def execute_batch(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Executes a list of actions and returns feedback for each. Stops on error."""
        results = []
        for action in actions:
            result = self.execute(action)
            results.append(result)
            if result == "FINISH":
                break
            if result.startswith("ERROR"):
                break
        return results
