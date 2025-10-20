import os
import sys
import winreg as reg
import getpass
from pathlib import Path


def get_startup_folder():
    """Get the Windows startup folder path"""
    user = getpass.getuser()
    startup_path = f"C:\\Users\\{user}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    return startup_path


def get_current_exe_path():
    """Get the path to the current executable or script"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script
        current_dir = Path(__file__).parent.parent
        script_path = current_dir / "tray.py"
        return str(script_path)


def add_to_startup():
    """Add Schedulr to Windows startup"""
    try:
        # Get paths
        startup_folder = get_startup_folder()
        exe_path = get_current_exe_path()

        # Create shortcut name
        shortcut_name = "Schedulr.lnk"

        # For Python scripts, we need to create a batch file or use pythonw.exe
        if exe_path.endswith('.py'):
            # Create a batch file to run the Python script
            batch_content = f'@echo off\npythonw "{exe_path}"\n'
            batch_path = os.path.join(startup_folder, "Schedulr.bat")

            with open(batch_path, 'w') as f:
                f.write(batch_content)

            print(f"Added Schedulr to startup: {batch_path}")
            return True
        else:
            print("Executable startup not implemented yet")
            return False

    except Exception as e:
        print(f"Error adding to startup: {e}")
        return False


def remove_from_startup():
    """Remove Schedulr from Windows startup"""
    try:
        startup_folder = get_startup_folder()
        batch_path = os.path.join(startup_folder, "Schedulr.bat")

        if os.path.exists(batch_path):
            os.remove(batch_path)
            print("Removed Schedulr from startup")
            return True
        else:
            print("Schedulr not found in startup")
            return False

    except Exception as e:
        print(f"Error removing from startup: {e}")
        return False


def is_in_startup():
    """Check if Schedulr is in Windows startup"""
    startup_folder = get_startup_folder()
    batch_path = os.path.join(startup_folder, "Schedulr.bat")
    return os.path.exists(batch_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage Schedulr auto-start")
    parser.add_argument('action', choices=['add', 'remove', 'check'],
                       help='Action to perform')

    args = parser.parse_args()

    if args.action == 'add':
        add_to_startup()
    elif args.action == 'remove':
        remove_from_startup()
    elif args.action == 'check':
        in_startup = is_in_startup()
        print(f"Schedulr is {'in' if in_startup else 'not in'} startup")