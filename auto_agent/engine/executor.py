from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from auto_agent.tools.filesystem import Workspace
from auto_agent.core.logger import ActionLogger
from typing import Dict, Any, List

console = Console()

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
                    confirm = console.input(f"[bold yellow]⚠️  File '{path}' already exists. Overwrite? (y/n): [/bold yellow]").lower()
                    if confirm != 'y':
                        self.logger.log(action, path, "fail")
                        return f"ERROR: User denied overwrite of '{path}'."
                self.workspace.create_file(path, content)
                
                # Validation
                valid, err = self.workspace.validate_syntax(path)
                if not valid:
                    self.logger.log(action, path, "fail")
                    console.print(f"  [red]✗[/red] [bold white]{path}[/bold white] [dim](syntax error)[/dim]")
                    return f"ERROR: File '{path}' created but has syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                console.print(f"  [green]✓[/green] [bold white]{path}[/bold white] [dim](created & validated)[/dim]")
                return f"SUCCESS: File '{path}' created and validated."
                
            elif action == "read_file":
                content = self.workspace.read_file(path)
                self.logger.log(action, str(path), "success")
                console.print(f"  [blue]📖[/blue] [bold white]{path}[/bold white]")
                # If it's a single file and a python file, try to show syntax
                if isinstance(path, str) and path.endswith(".py"):
                    from rich.syntax import Syntax
                    # We need to strip the line numbers added by Workspace for highlighting to work perfectly, 
                    # but Workspace added them for the LLM. 
                    # For the user, we can just show the raw content if we read it again or if we strip them.
                    # Actually, Workspace.read_file returns numbered lines. 
                    # Let's just show it as is for now or use a simple Panel.
                return f"SUCCESS: Read file(s):\n{content}"
                
            elif action == "list_directory":
                files = self.workspace.list_directory(path or ".")
                self.logger.log(action, path, "success")
                console.print(f"  [blue]📂[/bold blue] [bold white]{path or '.'}[/bold white]")
                return f"SUCCESS: Directory listing for '{path}': {', '.join(files)}"
                
            elif action == "delete_file":
                confirm = console.input(f"[bold red]⚠️  Are you sure you want to delete '{path}'? (y/n): [/bold red]").lower()
                if confirm != 'y':
                    self.logger.log(action, path, "fail")
                    return f"ERROR: User denied deletion of '{path}'."
                self.workspace.delete_file(path)
                self.logger.log(action, path, "success")
                console.print(f"  [red]🗑️[/red] [bold white]{path}[/bold white]")
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
                    console.print(f"  [red]✗[/red] [bold white]{path}[/bold white] [dim](edit introduced syntax error)[/dim]")
                    return f"ERROR: Text replaced in '{path}' but introduced syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                console.print(f"  [green]📝[/green] [bold white]{path}[/bold white] [dim](edited & validated)[/dim]")
                return f"SUCCESS: Replaced text in '{path}' and validated."
                
            elif action == "read_file_lines":
                start = action_obj.get("start_line")
                end = action_obj.get("end_line")
                if start is None or end is None:
                    self.logger.log(action, path, "fail")
                    return "ERROR: 'read_file_lines' requires 'start_line' and 'end_line'."
                content = self.workspace.read_file_lines(path, start, end)
                self.logger.log(action, path, "success")
                console.print(f"  [blue]📑[/blue] [bold white]{path}[/bold white] [dim](lines {start}-{end})[/dim]")
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
                    console.print(f"  [red]✗[/red] [bold white]{path}[/bold white] [dim](lines {start}-{end} edit error)[/dim]")
                    return f"ERROR: Lines {start}-{end} replaced in '{path}' but introduced syntax errors:\n{err}"
                
                self.logger.log(action, path, "success")
                console.print(f"  [green]✏️[/green] [bold white]{path}[/bold white] [dim](lines {start}-{end} edited & validated)[/dim]")
                return f"SUCCESS: Replaced lines {start}-{end} in '{path}' and validated."
                
            elif action == "run_command":
                command = action_obj.get("command")
                if not command:
                    self.logger.log(action, "N/A", "fail")
                    return "ERROR: Missing 'command' for 'run_command' action."
                
                # Security: Explicit confirmation for all commands
                confirm = console.input(f"[bold red]⚠️  The agent wants to run:[/bold red] [dim]{command}[/dim]\n[bold red]Allow? (y/n): [/bold red]").lower()
                if confirm != 'y':
                    self.logger.log(action, f"cmd: {command[:50]}", "fail")
                    return f"ERROR: User denied execution of command: {command}"

                console.print(f"  [yellow]⚡[/yellow] [bold white]Running:[/bold white] [dim]{command}[/dim]")
                output, success = self.workspace.run_command(command)
                status = "success" if success else "fail"
                self.logger.log(action, f"cmd: {command[:50]}", status)
                status_str = "SUCCESS" if success else "ERROR"
                return f"{status_str}: Command '{command}' executed:\n{output}"
            
            elif action == "update_memory":
                content = action_obj.get("content")
                self.workspace.update_memory(content)
                self.logger.log(action, "MEMORY.md", "success")
                console.print(f"  [magenta]🧠[/magenta] [bold white]MEMORY.md[/bold white] [dim](updated)[/dim]")
                return "SUCCESS: MEMORY.md updated."
                
            elif action == "search_regex":
                pattern = action_obj.get("pattern")
                if not pattern:
                    return "ERROR: 'search_regex' requires a 'pattern' field."
                results = self.workspace.search_regex(pattern)
                self.logger.log(action, f"regex: {pattern}", "success")
                console.print(f"  [cyan]🔍[/cyan] [bold white]Regex:[/bold white] [dim]{pattern}[/dim]")
                return f"SUCCESS: Search results for regex '{pattern}':\n{results}"

            elif action == "find_symbols":
                query = action_obj.get("query", "")
                results = self.workspace.find_symbols(query)
                self.logger.log(action, f"query: {query}", "success")
                console.print(f"  [cyan]🧬[/cyan] [bold white]Symbols:[/bold white] [dim]{query or 'all'}[/dim]")
                return f"SUCCESS: Symbol search results for '{query}':\n{results}"

            elif action == "finish":
                self.logger.log(action, "N/A", "success")
                return "FINISH"
                
            else:
                self.logger.log(action, path, "fail")
                return f"ERROR: Action '{action}' not recognized by executor."
                
        except Exception as e:
            self.logger.log(action, path, "fail")
            console.print(f"  [red]⚠[/red] [bold red]Error executing {action}:[/bold red] {e}")
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
