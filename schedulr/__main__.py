#!/usr/bin/env python
"""
Main entry point for Schedulr application.
This allows running the app with 'python -m schedulr'
"""

import sys
import argparse
from .tray import SystemTrayApp
from .autostart import add_to_startup, remove_from_startup, is_in_startup


def main():
    parser = argparse.ArgumentParser(description="Schedulr - Smart Task Scheduler")
    parser.add_argument('--tray', action='store_true',
                       help='Run in system tray mode with notifications')
    parser.add_argument('--autostart', choices=['add', 'remove', 'check'],
                       help='Manage auto-start on Windows startup')

    args = parser.parse_args()

    if args.autostart:
        if args.autostart == 'add':
            success = add_to_startup()
            sys.exit(0 if success else 1)
        elif args.autostart == 'remove':
            success = remove_from_startup()
            sys.exit(0 if success else 1)
        elif args.autostart == 'check':
            in_startup = is_in_startup()
            print(f"Schedulr is {'enabled' if in_startup else 'disabled'} for auto-start")
            sys.exit(0)
    elif args.tray:
        # Run in system tray mode
        tray_app = SystemTrayApp()
        tray_app.run()
    else:
        # Default: run the CLI app
        from .cli import app
        app()


if __name__ == "__main__":
    main()