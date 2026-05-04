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

    def list_directory(self, path: str = ".") -> List[str]:
        """Lists files and directories in the given relative path."""
        target = self._resolve_path(path)
        if not target.is_dir():
            raise NotADirectoryError(f"'{path}' is not a directory.")
        return [str(p.relative_to(self.root)) for p in target.iterdir()]

    def read_file(self, path: str) -> str:
        """Reads a file with truncation rules (3000 lines or 50KB)."""
        target = self._resolve_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File '{path}' not found.")
            
        # Check size first (50KB limit)
        size = target.stat().st_size
        if size > 50 * 1024:
            # Simple truncation for large files
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read(51200) # Read slightly more than 50KB to handle line boundaries if needed
                return content + "\n... [TRUNCATED DUE TO SIZE] ..."

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 3000:
                return "".join(lines[:3000]) + "\n... [TRUNCATED DUE TO LINE LIMIT] ..."
            return "".join(lines)

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

    def edit_file(self, path: str, instruction: str):
        """
        Placeholder for diff-based editing. 
        For MVP, we might implement a simple full-rewrite or use LLM to generate the new content.
        """
        # This will be integrated with the LLM in later phases.
        pass
