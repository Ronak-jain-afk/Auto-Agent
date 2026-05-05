import os
import shutil
from auto_agent.tools.filesystem import Workspace
from auto_agent.engine.executor import ActionExecutor

def run_pen_test():
    test_dir = "pen_test_workspace"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create a sensitive file OUTSIDE the sandbox
    secret_file = "outside_secret.txt"
    with open(secret_file, "w") as f:
        f.write("THIS IS A SECRET")

    workspace = Workspace(test_dir)
    executor = ActionExecutor(workspace)

    print("--- Security Vulnerability Testing ---\n")

    # 1. Test Path Traversal
    print("Test 1: Path Traversal (../)")
    traversal_action = {
        "action": "read_file",
        "path": "../outside_secret.txt"
    }
    try:
        res = executor.execute(traversal_action)
        print(f"Result: {res}")
        if "THIS IS A SECRET" in res:
            print("❌ VULNERABILITY FOUND: Path Traversal successful!")
        else:
            print("✅ Path Traversal blocked.")
    except Exception as e:
        print(f"✅ Path Traversal blocked (Exception): {e}")

    # 2. Test Absolute Path Access
    print("\nTest 2: Absolute Path Access")
    abs_path = os.path.abspath(secret_file)
    abs_action = {
        "action": "read_file",
        "path": abs_path
    }
    try:
        res = executor.execute(abs_action)
        print(f"Result: {res}")
        if "THIS IS A SECRET" in res:
            print("❌ VULNERABILITY FOUND: Absolute Path access successful!")
        else:
            print("✅ Absolute Path access blocked.")
    except Exception as e:
        print(f"✅ Absolute Path access blocked (Exception): {e}")

    # 3. Test Command Injection
    print("\nTest 3: Command Injection")
    # Try to execute a second command using ; or &
    injection_action = {
        "action": "run_command",
        "command": "echo 'safe' && echo 'INJECTED' > injected.txt"
    }
    res = executor.execute(injection_action)
    print(f"Result: {res}")
    if os.path.exists(os.path.join(test_dir, "injected.txt")):
        print("❌ VULNERABILITY FOUND: Command Injection successful (Operator bypass)!")
    else:
        print("✅ Command Injection blocked (or operator not supported).")

    # 4. Test Access to Hidden Files (.env)
    print("\nTest 4: Hidden File Access")
    try:
        workspace.create_file(".env", "DB_PASSWORD=password123")
        res = executor.execute({"action": "read_file", "path": ".env"})
        print(f"Result: {res}")
        if "password123" in res:
            print("❌ VULNERABILITY FOUND: Hidden file (.env) access successful!")
        else:
            print("✅ Hidden file access blocked.")
    except Exception as e:
        print(f"✅ Hidden file access blocked (Exception): {e}")

    # 5. Test Symlink Attack
    print("\nTest 5: Symlink Attack")
    secret_path = os.path.abspath("outside_secret.txt")
    symlink_path = os.path.join(test_dir, "malicious_link.txt")
    try:
        # Create a symlink pointing to the secret file outside
        os.symlink(secret_path, symlink_path)
        res = executor.execute({"action": "read_file", "path": "malicious_link.txt"})
        print(f"Result: {res}")
        if "THIS IS A SECRET" in res:
            print("❌ VULNERABILITY FOUND: Symlink attack successful!")
        else:
            print("✅ Symlink attack blocked.")
    except Exception as e:
        print(f"✅ Symlink attack blocked/failed: {e}")

    # 6. Test Self-Tampering
    print("\nTest 6: Self-Tampering Prevention")
    try:
        # Try to read the executor's own source code
        res = executor.execute({"action": "read_file", "path": "../auto_agent/engine/executor.py"})
        print(f"Result: {res}")
        if "class ActionExecutor" in res:
            print("❌ VULNERABILITY FOUND: Self-tampering/Code access successful!")
        else:
            print("✅ Self-tampering blocked.")
    except Exception as e:
        print(f"✅ Self-tampering blocked (Exception): {e}")

    # 7. Test File Size Limit
    print("\nTest 7: File Size Limit")
    try:
        huge_content = "A" * (6 * 1024 * 1024) # 6MB
        res = executor.execute({"action": "create_file", "path": "huge.txt", "content": huge_content})
        print(f"Result: {res}")
        if "SUCCESS" in res:
            print("❌ VULNERABILITY FOUND: Large file creation successful!")
        else:
            print("✅ Large file creation blocked.")
    except Exception as e:
        print(f"✅ Large file creation blocked (Exception): {e}")

    # Clean up
    if os.path.exists(secret_file):
        os.remove(secret_file)

if __name__ == "__main__":
    run_pen_test()
