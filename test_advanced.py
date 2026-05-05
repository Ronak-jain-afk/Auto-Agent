import os
import shutil
from auto_agent.tools.filesystem import Workspace
from auto_agent.engine.executor import ActionExecutor
from auto_agent.core.logger import ActionLogger

def test_advanced_features():
    test_dir = "test_workspace_advanced"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    workspace = Workspace(test_dir)
    logger = ActionLogger(os.path.join(test_dir, "test.log"))
    executor = ActionExecutor(workspace, logger)

    print("--- 1. Testing Batch Read ---")
    workspace.create_file("file1.txt", "Content of file 1")
    workspace.create_file("file2.txt", "Content of file 2")
    
    batch_read_action = {
        "action": "read_file",
        "path": ["file1.txt", "file2.txt"]
    }
    result = executor.execute(batch_read_action)
    print(result)
    assert "file1.txt" in result and "file2.txt" in result
    print("✅ Batch read successful.\n")

    print("--- 2. Testing Syntax Validation (Valid) ---")
    valid_py = {
        "action": "create_file",
        "path": "valid.py",
        "content": "def hello():\n    print('world')"
    }
    result = executor.execute(valid_py)
    print(result)
    assert "validated" in result.lower()
    print("✅ Valid syntax passed.\n")

    print("--- 3. Testing Syntax Validation (Invalid) ---")
    invalid_py = {
        "action": "create_file",
        "path": "invalid.py",
        "content": "def broken("
    }
    result = executor.execute(invalid_py)
    print(result)
    assert "ERROR" in result and "syntax errors" in result.lower()
    print("✅ Invalid syntax correctly flagged.\n")

    print("--- 4. Testing Update Memory ---")
    memory_update = {
        "action": "update_memory",
        "content": "# Project Memory\n- Task 1 complete"
    }
    result = executor.execute(memory_update)
    print(result)
    with open(os.path.join(test_dir, "MEMORY.md"), "r") as f:
        content = f.read()
        print(f"Memory Content: {content}")
        assert "Task 1 complete" in content
    print("✅ Memory update successful.\n")

    print("--- 5. Testing Regex Search ---")
    workspace.create_file("search_test.txt", "The magic word is gemini-core.")
    regex_search = {
        "action": "search_regex",
        "pattern": "gemini-[a-z]+"
    }
    result = executor.execute(regex_search)
    print(result)
    assert "gemini-core" in result
    print("✅ Regex search successful.\n")

    print("--- 6. Testing Find Symbols ---")
    workspace.create_file("symbols.py", "class MyAgent:\n    def start(self):\n        pass\n\ndef global_func():\n    pass")
    find_sym = {
        "action": "find_symbols",
        "query": "Agent"
    }
    result = executor.execute(find_sym)
    print(result)
    assert "class MyAgent" in result
    
    find_all = {
        "action": "find_symbols",
        "query": ""
    }
    result = executor.execute(find_all)
    print(result)
    assert "global_func" in result
    print("✅ Symbol finding successful.\n")

    print("--- All Advanced Feature Tests Passed! ---")

if __name__ == "__main__":
    try:
        test_advanced_features()
    except Exception as e:
        print(f"❌ Test failed: {e}")
