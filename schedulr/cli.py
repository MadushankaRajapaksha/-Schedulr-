from .app import run_app
from .notifier import TaskNotifier
from .core import Database
from datetime import datetime
import threading

def map_tasks(db_data):
    """Map database tuple data to list of dictionaries"""
    tasks = []
    for i in reversed(db_data):
        # If it's already a dictionary (from your example format), use it directly
        if isinstance(i, dict):
            tasks.append(i)
        else:
            # If it's a tuple from the database query, map it
            tasks.append({
                "id": i[0],
                "title": i[1],
                "date_time": i[2],
                "status": i[3],
            })
    return tasks


def app():
    """Main entry point - starts TUI with background notifier"""

    # Create notifier with a reference to the app's task manager
    notifier = TaskNotifier()
    db = Database()

    # def get_tasks():
    #     """Function that returns current tasks from the app"""
    #     return tui_app.task_manager.get_all_tasks()
    def get_tasks():
        """Function that returns current tasks from the database"""
        return map_tasks(db.get_all_tasks())

    # Start notifier in background thread before running TUI
    notifier_thread = threading.Thread(
        target=notifier.start,
        args=(get_tasks,),
        kwargs={"check_interval": 30},  # Check every 30 seconds
        daemon=True,
    )
    notifier_thread.start()

    print("🔔 Task Notifier started in background")
    print("📅 Starting Schedulr TUI...\n")

    # Run the TUI app (blocks until app exits)
    try:
        print(get_tasks())
        run_app(get_tasks_func=get_tasks)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    finally:
        # Stop notifier
        notifier.stop()
        db.close()
        print("✅ Notifier stopped")
        print("👋 Goodbye!")


def main():
    app()

if __name__ == "__main__":
    main()
