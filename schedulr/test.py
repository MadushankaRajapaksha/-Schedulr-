from plyer import notification
from datetime import datetime
import threading
import time

def notify(message):
    """Send a desktop notification using plyer"""
    try:
        notification.notify(
            title="Schedulr Notification",
            message=message,
            app_name="Schedulr",
            timeout=10
        )
    except Exception as e:
        print(f"Notification error: {e}")

class TaskNotifier:
    def __init__(self):
        # Track which tasks have already been notified (using task ID instead of index)
        self.notified_tasks = set()
        self.running = False
        self.thread = None
        self.get_tasks_func = None
        self.check_interval = 30
    
    def check_and_notify(self, tasks):
        """
        Check tasks and send notifications for due tasks.
        Each task is notified only once.
        
        Args:
            tasks: List of task dictionaries with 'id', 'title', 'date_time', and 'status'
        """
        now = datetime.now()
        
        for task in tasks:
            # Use task ID for tracking instead of index
            task_id = task.get('id')
            
            # Skip if already notified or task is completed
            if task_id in self.notified_tasks or task.get('status', '').lower() != 'pending':
                continue
            
            try:
                # Parse the task due time
                task_time = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
                
                # Calculate time difference in seconds
                time_diff = (task_time - now).total_seconds()
                
                # Notify if task is due within the next minute (0 to 60 seconds)
                if 0 <= time_diff <= 60:
                    notify(f"Task Due: {task['title']}")
                    print(f"[{now.strftime('%H:%M:%S')}] Notified: {task['title']}")
                    
                    # Mark this task as notified using its ID
                    self.notified_tasks.add(task_id)
                    
            except ValueError as e:
                print(f"Invalid date format for task: {task.get('title', 'Unknown')} - {e}")
                continue
            except Exception as e:
                print(f"Error checking task {task.get('title', 'Unknown')}: {e}")
                continue
    
    def _run_loop(self):
        """Internal loop that runs in a separate thread"""
        print("Task Notifier started in background thread.")
        
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
        
        notify("notifyer started!")
        
        self.get_tasks_func = get_tasks_func
        self.check_interval = check_interval
        self.running = True
        
        # Start the notifier in a daemon thread so it stops when the app closes
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        print(f"Task Notifier started with {check_interval}s check interval.")
    
    def stop(self):
        """Stop the notifier thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=2)
            print("Task Notifier stopped.")
    
    def reset_notifications(self):
        """Clear the list of notified tasks (useful for testing or refresh)"""
        self.notified_tasks.clear()
        print("Notification history cleared.")

# Example usage:
if __name__ == "__main__":
    # Sample function to get tasks (replace with your actual database/file reading)
    def get_tasks():
        now = datetime.now()
        from datetime import timedelta
        
        # Example tasks - in your real app, load these from your database/file
        return [
            {
                'id': 1,
                'title': 'Team Meeting',
                'date_time': (now + timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
            {
                'id': 2,
                'title': 'Submit Report',
                'date_time': (now + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
            {
                'id': 3,
                'title': 'Past Task',
                'date_time': (now - timedelta(seconds=90)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
        ]
    
    # Create and start notifier
    notifier = TaskNotifier()
    notifier.start(get_tasks, check_interval=15)
    
    # Keep main thread alive for testing
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        notifier.stop()
        print("\nTest stopped.")