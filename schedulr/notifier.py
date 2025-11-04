import threading
import sqlite3
import time
from datetime import datetime, timedelta
from plyer import notification
from .core import Database

# Thread-local storage for SQLite connection
thread_local = threading.local()

class Notifier:
    def __init__(self, check_interval=60):  # Check every 60 seconds
        self.db = Database()
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.notified_tasks = set()  # Track tasks we've already notified about

    def start(self):
        """Start the background notification checker"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background notification checker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _run(self):
        try:
            while self.running:
                try:
                    self.check_due_tasks()
                except Exception as e:
                    print(f"Error checking tasks: {e}")
                time.sleep(self.check_interval)
        finally:
            close_db_connection()

    def check_due_tasks(self):
        """Check for tasks that are due now"""
        now = datetime.now()
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')

        # Get all pending tasks
        pending_tasks = self.db.get_pending_tasks()

        for task_row in pending_tasks:
            task = self.map_task(task_row)
            if self.is_task_due(task, now):
                # Only notify if we haven't already notified about this task
                if task['id'] not in self.notified_tasks:
                    self.notify_task(task)
                    self.notified_tasks.add(task['id'])

    def map_task(self, task_row):
        """Map database row to task dict"""
        return {
            "id": task_row[0],
            "title": task_row[1],
            "date_time": task_row[2],
            "status": task_row[3],
            "repeat_type": "none"  # Default for current schema
        }

    def is_task_due(self, task, now):
        """Check if a task is due at the current time"""
        if task['repeat_type'] == 'none':
            # One-time task
            if task['date_time']:
                try:
                    task_time = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
                    
                    # Only notify for tasks from TODAY
                    # Don't notify for old tasks from previous days/months/years
                    current_date = now.date()
                    task_date = task_time.date()
                    
                    # Only consider tasks from today
                    if task_date != current_date:
                        return False
                    
                    # Calculate time difference in seconds
                    time_diff = now - task_time
                    
                    # Check if the task is due within the next 10 seconds
                    if 0 <= time_diff.total_seconds() < 10:
                        return True
                    
                    # Check if the task was due within the check_interval.
                    # This ensures that we only notify for tasks that have become due since the last check.
                    return 0 <= time_diff.total_seconds() < self.check_interval
                    
                except ValueError:
                    print(f"Error parsing task datetime: {task['date_time']}")
                    return False
        return False

    def notify_task(self, task):
        """Send a desktop notification for the task"""
        now = datetime.now()
        if 'date_time' in task:
            task_time = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
        else:
            raise ValueError("Task dictionary must contain 'date_time' key")
        time_diff = task_time - now
    
        if 0 <= time_diff.total_seconds() < 10:
            title = f"Task Due Soon: {task['title']}"
            message = f"Your task '{task['title']}' is due in {int(time_diff.total_seconds())} seconds!"
        else:
            title = f"Task Due: {task['title']}"
            message = f"Your task '{task['title']}' is due now!"

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Schedulr",
                timeout=10  # 10 seconds
            )
            print(f"Notification sent for task: {task['title']}")
        except Exception as e:
            print(f"Failed to send notification: {e}")

    def notify_new_task(self, task_title):
        """Send a notification when a new task is added"""
        title = "✅ New Task Added"
        message = f"Task '{task_title}' has been added to your schedule!"

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Schedulr",
                timeout=5  # 5 seconds for new task notification
            )
            print(f"New task notification sent for: {task_title}")
        except Exception as e:
            print(f"Failed to send new task notification: {e}")

def get_db_connection():
    if not hasattr(thread_local, 'connection'):
        thread_local.connection = sqlite3.connect('tasks.db')
        thread_local.connection.row_factory = sqlite3.Row
    return thread_local.connection

def close_db_connection():
    if hasattr(thread_local, 'connection'):
        thread_local.connection.close()
        del thread_local.connection