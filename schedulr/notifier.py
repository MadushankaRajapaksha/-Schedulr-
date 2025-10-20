import threading
import time
from datetime import datetime, timedelta
from plyer import notification
from .core import Database


class Notifier:
    def __init__(self, check_interval=60):  # Check every 60 seconds
        self.db = Database()
        self.check_interval = check_interval
        self.running = False
        self.thread = None

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
        """Main loop for checking due tasks"""
        while self.running:
            try:
                self.check_due_tasks()
            except Exception as e:
                print(f"Error checking tasks: {e}")
            time.sleep(self.check_interval)

    def check_due_tasks(self):
        """Check for tasks that are due now"""
        now = datetime.now()
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')

        # Get all pending tasks
        pending_tasks = self.db.get_pending_tasks()

        for task_row in pending_tasks:
            task = self.map_task(task_row)
            if self.is_task_due(task, now):
                self.notify_task(task)
                # Optionally mark as notified or keep pending

    def map_task(self, task_row):
        """Map database row to task dict"""
        return {
            "id": task_row[0],
            "title": task_row[1],
            "date_time": task_row[2],
            "repeat_type": task_row[3],
            "start_date": task_row[4],
            "end_date": task_row[5],
            "day_of_week": task_row[6],
            "day_of_month": task_row[7],
            "status": task_row[8],
        }

    def is_task_due(self, task, now):
        """Check if a task is due at the current time"""
        if task['repeat_type'] == 'none':
            # One-time task
            if task['date_time']:
                try:
                    task_time = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
                    # Check if within the last minute to account for check interval
                    return abs((now - task_time).total_seconds()) < 60
                except ValueError:
                    return False
        else:
            # Recurring task - simplified check for now
            # For daily: check time matches
            # For weekly: check day and time
            # For monthly: check day of month and time
            if self.is_recurring_task_due_today(task, now):
                try:
                    # Extract time from task (assume time is in date_time or default)
                    if task['date_time']:
                        task_time = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
                        task_hour_minute = task_time.strftime('%H:%M')
                    else:
                        task_hour_minute = '12:00'  # Default
                    now_hour_minute = now.strftime('%H:%M')
                    return task_hour_minute == now_hour_minute
                except (ValueError, AttributeError):
                    return False
        return False

    def is_recurring_task_due_today(self, task, now):
        """Check if a recurring task is scheduled for today"""
        repeat_type = task['repeat_type']
        if repeat_type == 'daily':
            # Daily tasks are always due (within date range)
            if task.get('start_date') and task.get('end_date'):
                start = datetime.strptime(task['start_date'], '%Y-%m-%d').date()
                end = datetime.strptime(task['end_date'], '%Y-%m-%d').date()
                return start <= now.date() <= end
            return True
        elif repeat_type == 'weekly':
            if task.get('day_of_week'):
                return task['day_of_week'] == now.strftime('%A')
            return False
        elif repeat_type == 'monthly':
            if task.get('day_of_month'):
                return task['day_of_month'] == now.day
            return False
        return False

    def notify_task(self, task):
        """Send a desktop notification for the task"""
        title = f"Task Due: {task['title']}"
        message = f"Your task '{task['title']}' is due now!"
        if task.get('repeat_type') and task['repeat_type'] != 'none':
            message += f" (Recurring: {task['repeat_type']})"

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Schedulr",
                timeout=10  # 10 seconds
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")