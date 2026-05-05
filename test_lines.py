from auto_agent.tools.filesystem import Workspace
import os
import shutil

def test_line_editing():
    root = "test_edit_workspace"
    if os.path.exists(root):
        shutil.rmtree(root)
    
    ws = Workspace(root)
    
    # Create a test file
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    ws.create_file("test.txt", content)
    
    # Test read_file_lines
    lines = ws.read_file_lines("test.txt", 2, 4)
    print(f"Read lines 2-4:\n{lines}")
    assert lines == "Line 2\nLine 3\nLine 4\n"
    
    # Test edit_file_lines (replace lines 2-3)
    ws.edit_file_lines("test.txt", 2, 3, "New Line A\nNew Line B")
    
    # Verify change
    new_content = ws.read_file("test.txt")
    print(f"New content:\n{new_content}")
    expected = "Line 1\nNew Line A\nNew Line B\nLine 4\nLine 5"
    assert new_content.strip() == expected.strip()
    
    # Cleanup
    shutil.rmtree(root)
    print("Line editing tests passed!")

if __name__ == "__main__":
    test_line_editing()
