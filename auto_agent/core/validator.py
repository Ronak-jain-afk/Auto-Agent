import json
import re
from typing import List, Dict, Any, Tuple

ALLOWED_ACTIONS = {
    "create_file", "read_file", "edit_file", "delete_file", "list_directory", "finish"
}

def parse_and_validate_actions(llm_output: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parses LLM output as JSON and validates against the allowed action schema.
    Returns (actions, error_message).
    """
    try:
        # 1. Clean up common LLM garbage (like markdown blocks or preambles)
        # Try to find the outermost [ ]
        start_idx = llm_output.find('[')
        end_idx = llm_output.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = llm_output[start_idx:end_idx+1]
        else:
            json_str = llm_output.strip()

        data = json.loads(json_str)
            
        if not isinstance(data, list):
            return [], "ERROR: Output must be a JSON array of actions."
            
        validated_actions = []
        for i, action_obj in enumerate(data):
            if not isinstance(action_obj, dict):
                return [], f"ERROR: Action at index {i} is not an object."
                
            action_name = action_obj.get("action")
            if action_name not in ALLOWED_ACTIONS:
                return [], f"ERROR: Unknown action '{action_name}' at index {i}."
                
            if "path" not in action_obj and action_name != "finish":
                return [], f"ERROR: Missing 'path' for action '{action_name}' at index {i}."
            
            validated_actions.append(action_obj)
            
        return validated_actions, ""
        
    except json.JSONDecodeError:
        return [], "ERROR: Invalid JSON format. Please ensure your output is a strictly formatted JSON array."
    except Exception as e:
        return [], f"ERROR: Validation failed: {str(e)}"
