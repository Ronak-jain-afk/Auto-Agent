import json
import datetime
from pathlib import Path

class ActionLogger:
    def __init__(self, log_file: str = "agent_actions.log"):
        """
        Initializes the logger. The log file will be created in the directory 
        from which the agent is run, typically the project root.
        """
        self.log_file = Path(log_file)

    def log(self, action: str, path: str, status: str):
        """
        Logs an action in structured JSON format.
        Status should be 'success' or 'fail'.
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "path": str(path) if path else "N/A",
            "status": status
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging Error: {e}")
