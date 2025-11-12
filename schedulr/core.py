import sqlite3
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_path: str = "data.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        self.cur = self.conn.cursor()
        
        # Create task table in database if it doesn't exist
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS task(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_time DATETIME,
                status TEXT DEFAULT 'Pending'
            )
        """)
        
         
        
        self.conn.commit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
     
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def create_task(self, title: str, date_time: str, status: str = "Pending") -> str:
        """Create a new task in the database.

        Args:
            title (str): The title of the task.
            date_time (str): The date and time for the task.
            status (str): The status of the task.

        Returns:
            str: A success message or an error message if the task creation fails.
        """
        try:
            self.cur.execute(
                "INSERT INTO task (title, date_time, status) VALUES (?, ?, ?)",
                (title, date_time, status)
            )
            self.conn.commit()
            return f"Success, task added with id {self.cur.lastrowid}"
        except sqlite3.Error as e:
            print(f"Error creating task: {e}")
            self.conn.rollback()
            return f"Error: {str(e)}"

    def get_all_tasks(self) -> List[Tuple]:
        """Get all tasks from the database.

        Returns:
            List[Tuple]: A list of all tasks as tuples, or empty list if error occurs.
        """
        try:
            self.cur.execute("SELECT * FROM task ORDER BY id")
            return self.cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting all tasks: {e}")
            return []

    def get_task_by_id(self, task_id: int) -> Optional[Tuple]:
        """Get a specific task by its ID.

        Args:
            task_id (int): The ID of the task to retrieve.

        Returns:
            Optional[Tuple]: The task as a tuple, or None if not found or error occurs.
        """
        try:
            self.cur.execute("SELECT * FROM task WHERE id = ?", (task_id,))
            result = self.cur.fetchone()
            return result
        except sqlite3.Error as e:
            print(f"Error getting task by ID: {e}")
            return None

    def update_task(self, task_id: int, title: str = None, date_time: str = None, status: str = None) -> str:
        """Update an existing task in the database.

        Args:
            task_id (int): The ID of the task to update.
            title (str, optional): The new title of the task.
            date_time (str, optional): The new date and time for the task.
            status (str, optional): The new status of the task.

        Returns:
            str: A success message or an error message if the update fails.
        """
        try:
            updates = []
            params = []

            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if date_time is not None:
                updates.append("date_time = ?")
                params.append(date_time)
            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if not updates:
                return "No updates provided"

            params.append(task_id)
            query = f"UPDATE task SET {', '.join(updates)} WHERE id = ?"

            self.cur.execute(query, params)

            if self.cur.rowcount == 0:
                return f"No task found with ID {task_id}"

            self.conn.commit()
            return f"Task {task_id} updated successfully"
        except sqlite3.Error as e:
            print(f"Error updating task: {e}")
            self.conn.rollback()
            return f"Error: {str(e)}"

    def delete_task(self, task_id: int) -> str:
        """Delete a task from the database.

        Args:
            task_id (int): The ID of the task to delete.

        Returns:
            str: A success message or an error message if the deletion fails.
        """
        try:
            self.cur.execute("DELETE FROM task WHERE id = ?", (task_id,))
            
            if self.cur.rowcount == 0:
                return f"No task found with ID {task_id}"
            
            self.conn.commit()
            return f"Task {task_id} deleted successfully"
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")
            self.conn.rollback()
            return f"Error: {str(e)}"

    def get_tasks_by_status(self, status: str) -> List[Tuple]:
        """Get all tasks with a specific status.

        Args:
            status (str): The status to filter tasks by.

        Returns:
            List[Tuple]: A list of tasks with the specified status.
        """
        try:
            self.cur.execute("SELECT * FROM task WHERE status = ?", (status,))
            return self.cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting tasks by status: {e}")
            return []

    def get_pending_tasks(self) -> List[Tuple]:
        """Get all pending tasks.

        Returns:
            List[Tuple]: A list of pending tasks.
        """
        return self.get_tasks_by_status("Pending")

    def get_completed_tasks(self) -> List[Tuple]:
        """Get all completed tasks.

        Returns:
            List[Tuple]: A list of completed tasks.
        """
        return self.get_tasks_by_status("Completed")