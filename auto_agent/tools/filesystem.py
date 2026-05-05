import os
from pathlib import Path
from typing import List, Union

class Workspace:
    def __init__(self, root_dir: str):
        """
        Initializes the Workspace with a fixed root directory.
        All operations are sandboxed within this directory.
        """
        self.root = Path(root_dir).resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
            
    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolves a relative path to an absolute path and ensures it's within the sandbox.
        """
        # Join and resolve to handle '../' or absolute paths provided by the LLM
        target_path = (self.root / relative_path).resolve()
        
        # Security check: Ensure target_path starts with self.root
        if not str(target_path).startswith(str(self.root)):
            raise PermissionError(f"Access denied: Path '{relative_path}' is outside the sandbox.")
        
        # Block hidden files/directories (like .git, .env)
        if any(part.startswith('.') for part in target_path.parts[len(self.root.parts):]):
            raise PermissionError(f"Access denied: Hidden files or directories (like '{relative_path}') are restricted.")
            
        return target_path

    def exists(self, path: str) -> bool:
        """Checks if a path exists within the sandbox."""
        try:
            target = self._resolve_path(path)
            return target.exists()
        except Exception:
            return False

    def list_directory(self, path: str = ".") -> List[str]:
        """Lists files and directories in the given relative path."""
        target = self._resolve_path(path)
        if not target.is_dir():
            raise NotADirectoryError(f"'{path}' is not a directory.")
        return [str(p.relative_to(self.root)) for p in target.iterdir()]

    def read_file(self, path: Union[str, List[str]]) -> str:
        """Reads one or more files with line numbers and truncation rules."""
        paths = [path] if isinstance(path, str) else path
        results = []

        for p in paths:
            try:
                target = self._resolve_path(p)
                if not target.is_file():
                    results.append(f"ERROR: File '{p}' not found.")
                    continue
                    
                size = target.stat().st_size
                if size > 50 * 1024:
                    with open(target, 'r', encoding='utf-8') as f:
                        content = f.read(51200)
                        results.append(f"--- File: {p} ---\n{content}\n... [TRUNCATED DUE TO SIZE] ...")
                        continue

                with open(target, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
                
                if len(numbered_lines) > 3000:
                    content = "".join(numbered_lines[:3000]) + "\n... [TRUNCATED DUE TO LINE LIMIT] ..."
                else:
                    content = "".join(numbered_lines)
                
                results.append(f"--- File: {p} ---\n{content}")
            except Exception as e:
                results.append(f"ERROR reading '{p}': {str(e)}")

        return "\n\n".join(results)

    def validate_syntax(self, path: str) -> tuple[bool, str]:
        """Validates the syntax of a file (currently supports Python)."""
        target = self._resolve_path(path)
        if not target.suffix == ".py":
            return True, "" # Skip non-python files for now

        import subprocess
        try:
            # Use python's built-in compile module to check syntax without executing
            result = subprocess.run(
                ["python", "-m", "py_compile", str(target)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, result.stderr.strip()
            return True, ""
        except Exception as e:
            return False, f"Validation tool error: {str(e)}"

    def update_memory(self, content: str):
        """Specifically updates the MEMORY.md file in the root."""
        memory_path = self.root / "MEMORY.md"
        with open(memory_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def create_file(self, path: str, content: str):
        """Creates a file with the given content."""
        target = self._resolve_path(path)
        # Ensure parent directories exist
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)

    def delete_file(self, path: str):
        """Deletes a file. Confirmation should be handled at the CLI layer."""
        target = self._resolve_path(path)
        if target.is_file():
            target.unlink()
        elif target.is_dir():
            # For MVP, we might want to restrict directory deletion or make it explicit
            import shutil
            shutil.rmtree(target)
        else:
            raise FileNotFoundError(f"Path '{path}' not found.")

    def edit_file(self, path: str, search_text: str, replace_text: str):
        """
        Performs a search and replace on a file.
        """
        target = self._resolve_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File '{path}' not found.")

        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()

        if search_text not in content:
            raise ValueError(f"Search text not found in '{path}'.")

        new_content = content.replace(search_text, replace_text)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def read_file_lines(self, path: str, start_line: int, end_line: int) -> str:
        """Reads a specific range of lines from a file with line numbers (1-indexed)."""
        target = self._resolve_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File '{path}' not found.")

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start = max(0, start_line - 1)
        end = min(len(lines), end_line)
        
        # Add line numbers corresponding to the original file
        numbered_lines = [f"{i+1}: {lines[i]}" for i in range(start, end)]
        return "".join(numbered_lines)

    def edit_file_lines(self, path: str, start_line: int, end_line: int, new_content: str):
        """Replaces a specific line range with new content (1-indexed)."""
        target = self._resolve_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File '{path}' not found.")

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Adjust for 1-based indexing
        start = max(0, start_line - 1)
        end = min(len(lines), end_line)

        # Ensure new_content ends with a newline if it's replacing whole lines
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'

        # Replace the lines
        lines[start:end] = [new_content]

        with open(target, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def run_command(self, command: str) -> tuple[str, bool]:
        """Executes a shell command. Returns (output, success)."""
        import subprocess
        try:
            result = subprocess.run(
                command,
                cwd=self.root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            success = (result.returncode == 0)
            return output.strip() or "[No Output]", success
            
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out after 30 seconds.", False
        except Exception as e:
            return f"ERROR: Command execution failed: {str(e)}", False

    def search_project(self, query: str) -> str:
        """Searches all files in the project for a string (recursive)."""
        results = []
        # Walk through the root directory recursively
        for root, dirs, files in os.walk(self.root):
            # Respect hidden directory blocks
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                full_path = Path(root) / file
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if query in line:
                                rel_path = full_path.relative_to(self.root)
                                results.append(f"{rel_path}:{i+1}: {line.strip()}")
                                if len(results) >= 50: # Limit matches for context safety
                                    return "\n".join(results) + "\n... [TOO MANY MATCHES, TRUNCATED] ..."
                except Exception:
                    # Skip binary or unreadable files
                    continue
        
        return "\n".join(results) if results else "No matches found."

    def search_regex(self, pattern: str) -> str:
        """Searches all files using a regular expression."""
        import re
        try:
            regex = re.compile(pattern)
        except Exception as e:
            return f"ERROR: Invalid regex pattern: {str(e)}"

        results = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'): continue
                full_path = Path(root) / file
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if regex.search(line):
                                rel_path = full_path.relative_to(self.root)
                                results.append(f"{rel_path}:{i+1}: {line.strip()}")
                                if len(results) >= 50:
                                    return "\n".join(results) + "\n... [TRUNCATED] ..."
                except Exception: continue
        return "\n".join(results) if results else "No matches found."

    def find_symbols(self, query: str = "") -> str:
        """Finds class and function definitions in Python files."""
        import re
        # Pattern for: class Name(...) or def name(...)
        symbol_pattern = re.compile(r"^\s*(class|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)")
        
        results = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if not file.endswith(".py"): continue
                full_path = Path(root) / file
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            match = symbol_pattern.match(line)
                            if match:
                                symbol_type = match.group(1)
                                symbol_name = match.group(2)
                                if query.lower() in symbol_name.lower():
                                    rel_path = full_path.relative_to(self.root)
                                    results.append(f"{rel_path}:{i+1}: {symbol_type} {symbol_name}")
                except Exception: continue
        
        return "\n".join(results) if results else "No symbols found."
