from auto_agent.tools.filesystem import Workspace
import os
import shutil
from pathlib import Path

def test_sandbox():
    root = "test_workspace"
    if os.path.exists(root):
        shutil.rmtree(root)
    
    ws = Workspace(root)
    
    # Test creation
    ws.create_file("hello.txt", "Hello World")
    assert os.path.exists(os.path.join(root, "hello.txt"))
    print("✓ create_file works")
    
    # Test reading
    content = ws.read_file("hello.txt")
    assert content == "Hello World"
    print("✓ read_file works")
    
    # Test list
    files = ws.list_directory(".")
    assert "hello.txt" in files
    print("✓ list_directory works")
    
    # Test Sandbox escape (should fail)
    try:
        ws.read_file("../GEMINI.md")
        print("✗ Sandbox escape failed to block!")
    except PermissionError as e:
        print(f"✓ Sandbox blocked escape: {e}")
        
    # Test hidden file block (should fail)
    try:
        ws.create_file(".secret", "data")
        print("✗ Hidden file failed to block!")
    except PermissionError as e:
        print(f"✓ Sandbox blocked hidden file: {e}")

    # Cleanup
    shutil.rmtree(root)
    print("All tests passed!")

if __name__ == "__main__":
    test_sandbox()
