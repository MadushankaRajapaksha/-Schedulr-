import pystray
from PIL import Image
import threading
import os
import sys
from .notifier import Notifier
from .cli import Home


class SystemTrayApp:
    def __init__(self):
        self.notifier = Notifier()
        self.app_thread = None
        self.icon = None

    def create_icon(self):
        """Create a simple icon for the system tray"""
        # Create a simple 64x64 icon (you can replace this with a proper icon file)
        icon = Image.new('RGB', (64, 64), color='blue')
        return icon

    def show_app(self, icon, item):
        """Show the main application"""
        if self.app_thread and self.app_thread.is_alive():
            return  # App is already running

        self.app_thread = threading.Thread(target=self.run_app, daemon=True)
        self.app_thread.start()

    def run_app(self):
        """Run the main Textual app"""
        try:
            Home().run()
        except Exception as e:
            print(f"Error running app: {e}")

    def exit_app(self, icon, item):
        """Exit the application"""
        self.notifier.stop()
        icon.stop()

    def setup_menu(self):
        """Create the system tray menu"""
        menu = pystray.Menu(
            pystray.MenuItem("Open Schedulr", self.show_app),
            pystray.MenuItem("Exit", self.exit_app)
        )
        return menu

    def run(self):
        """Start the system tray application"""
        # Start the notifier in background
        self.notifier.start()

        # Create and run the system tray icon
        icon = pystray.Icon("Schedulr", self.create_icon(), "Schedulr Task Scheduler", self.setup_menu())
        icon.run()


if __name__ == "__main__":
    tray_app = SystemTrayApp()
    tray_app.run()