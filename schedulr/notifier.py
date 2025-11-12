from datetime import datetime
import threading
import time
import platform
import subprocess

# Detect platform
SYSTEM = platform.system()

# Try to import plyer as a fallback
try:
    from plyer import notification

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


def notify(message):
    """
    Send a cross-platform desktop notification.
    Falls back gracefully if native methods aren't available.
    """
    title = "Schedulr Notification"

    try:
        # Try native notification methods first
        if SYSTEM == "Darwin":  # macOS
            # Use osascript (AppleScript) - no dependencies needed
            script = f'display notification "{message}" with title "{title}" sound name "default"'
            subprocess.run(
                ["osascript", "-e", script], check=False, capture_output=True
            )
            return

        elif SYSTEM == "Linux":
            # Try notify-send (most Linux distros have this)
            try:
                subprocess.run(
                    ["notify-send", title, message],
                    check=False,
                    capture_output=True,
                    timeout=2,
                )
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass  # Fall through to plyer

        elif SYSTEM == "Windows":
            # Try Windows toast notification via PowerShell
            try:
                ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
                $Template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $RawXml = [xml] $Template.GetXml()
                ($RawXml.toast.visual.binding.text|where {{$_.id -eq "1"}}).AppendChild($RawXml.CreateTextNode("{title}")) > $null
                ($RawXml.toast.visual.binding.text|where {{$_.id -eq "2"}}).AppendChild($RawXml.CreateTextNode("{message}")) > $null
                $SerializedXml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $SerializedXml.LoadXml($RawXml.OuterXml)
                $Toast = [Windows.UI.Notifications.ToastNotification]::new($SerializedXml)
                $Toast.Tag = "Schedulr"
                $Toast.Group = "Schedulr"
                $Notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Schedulr")
                $Notifier.Show($Toast);
                """
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    check=False,
                    capture_output=True,
                    timeout=3,
                )
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass  # Fall through to plyer

        # Try plyer as a fallback for all platforms
        if PLYER_AVAILABLE:
            notification.notify(
                title=title, message=message, app_name="Schedulr", timeout=10
            )
            return

    except Exception as e:
        # Silent fail - will use console fallback below
        pass

    # Final fallback: print to console
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*50}")
    print(f"🔔 [{timestamp}] {title}")
    print(f"   {message}")
    print(f"{'='*50}\n")


class TaskNotifier:
    def __init__(self):
        # Track which tasks have already been notified (using task ID instead of index)
        self.notified_tasks = set()
        self.running = False
        self.thread = None
        self.get_tasks_func = None
        self.check_interval = 30

        # Print notification setup info
        if SYSTEM == "Darwin":
            print("✅ Using native macOS notifications (osascript)")
        elif SYSTEM == "Linux":
            print("✅ Using native Linux notifications (notify-send)")
        elif SYSTEM == "Windows":
            print("✅ Using native Windows notifications (PowerShell)")
        elif PLYER_AVAILABLE:
            print("✅ Using plyer for notifications")
        else:
            print("ℹ️  Desktop notifications unavailable - will print to console")
            print(
                "   Tip: Install 'plyer' for desktop notifications: pip install plyer"
            )

    def notify_new_task(self, title):
        """Send a notification for a newly created task."""
        notify(f"New Task Added: {title}")

    def check_and_notify(self, tasks):
        """
        Check tasks and send notifications for due tasks.
        Each task is notified only once.

        Args:
            tasks: List of task dictionaries with 'id', 'title', 'date_time', and 'status'
        """
        now = datetime.now()

        if not tasks:
            return  # Silent return if no tasks

        for task in tasks:
            # Use task ID for tracking instead of index
            task_id = task.get("id")

            # Skip if already notified or task is completed
            if (
                task_id in self.notified_tasks
                or task.get("status", "").lower() != "pending"
            ):
                continue

            try:
                # Parse the task due time
                task_time = datetime.strptime(task["date_time"], "%Y-%m-%d %H:%M:%S")

                # Calculate time difference in seconds
                time_diff = (task_time - now).total_seconds()

                # Notify if task is due within the next minute (0 to 60 seconds)
                if -60 < time_diff <= 60:
                    notify(f"⏰ Task Due Now: {task['title']}")
                    print(f"[{now.strftime('%H:%M:%S')}] Notified: {task['title']}")

                    # Mark this task as notified using its ID
                    self.notified_tasks.add(task_id)

            except ValueError as e:
                print(
                    f"Invalid date format for task: {task.get('title', 'Unknown')} - {e}"
                )
                continue
            except Exception as e:
                print(f"Error checking task {task.get('title', 'Unknown')}: {e}")
                continue

    def _run_loop(self):
        """Internal loop that runs in a separate thread"""
        print(f"🔔 Task Notifier started (checking every {self.check_interval}s)")

        while self.running:
            try:
                # Get fresh task list from your app
                if self.get_tasks_func:
                    tasks = self.get_tasks_func()

                    # Check and notify
                    if tasks:
                        self.check_and_notify(tasks)

                # Wait before next check
                time.sleep(self.check_interval)

            except Exception as e:
                print(f"Error in notifier loop: {e}")
                time.sleep(self.check_interval)

    def start(self, get_tasks_func, check_interval=30):
        """
        Start the notifier as a background thread.

        Args:
            get_tasks_func: Function that returns the current list of tasks
            check_interval: Seconds between checks (default: 30)
        """
        if self.running:
            print("Task Notifier is already running.")
            return

        self.get_tasks_func = get_tasks_func
        self.check_interval = check_interval

        # Start the notifier in a daemon thread so it stops when the app closes
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = True
        self.thread.start()

    def stop(self):
        """Stop the notifier thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=2)
            print("✅ Task Notifier stopped.")

    def reset_notifications(self):
        """Clear the list of notified tasks (useful for testing or refresh)"""
        self.notified_tasks.clear()
        print("Notification history cleared.")


def test_notification():
    """Test function to check if notifications work on your system"""
    print(f"\n{'='*50}")
    print(f"Testing notifications on {SYSTEM}...")
    print(f"{'='*50}\n")

    notify("This is a test notification from Schedulr!")

    print("\nDid you see a notification? If not, notifications will")
    print("appear in the console instead.\n")


# Example usage:
if __name__ == "__main__":
    # Test notification first
    test_notification()

    print("\nStarting notifier test...\n")

    # Sample function to get tasks
    def get_tasks():
        now = datetime.now()
        from datetime import timedelta

        # Example tasks
        return [
            {
                "id": 1,
                "title": "Team Meeting",
                "date_time": (now + timedelta(seconds=30)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "status": "Pending",
            },
            {
                "id": 2,
                "title": "Submit Report",
                "date_time": (now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Pending",
            },
        ]

    # Create and start notifier
    notifier = TaskNotifier()
    notifier.start(get_tasks, check_interval=15)

    # Keep main thread alive for testing
    try:
        print("Press Ctrl+C to stop...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        notifier.stop()
        print("\n👋 Test stopped.")
