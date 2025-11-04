import unittest
from unittest.mock import patch, MagicMock
from schedulr.notifier import Notifier, get_db_connection, close_db_connection
from schedulr.core import Database
from datetime import datetime, timedelta

class TestNotifier(unittest.TestCase):
    def setUp(self):
        self.notifier = Notifier(check_interval=1)
        self.notifier.db = MagicMock(spec=Database)
        self.notifier.db.get_pending_tasks.return_value = [
            (1, 'Test Task', (datetime.now() + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S'), 'pending', 'none')
        ]

    def tearDown(self):
        close_db_connection()

    @patch('schedulr.notifier.notification.notify')
    def test_notify_task(self, mock_notify):
        task = {
            "id": 1,
            "title": "Test Task",
            "date_time": (datetime.now() + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "pending",
            "repeat_type": "none"
        }
        self.notifier.notify_task(task)
        mock_notify.assert_called_once_with(
            title="Task Due Soon: Test Task",
            message="Your task 'Test Task' is due in 5 seconds!",
            app_name="Schedulr",
            timeout=10
        )

    @patch('schedulr.notifier.notification.notify')
    def test_notify_new_task(self, mock_notify):
        self.notifier.notify_new_task("Test Task")
        mock_notify.assert_called_once_with(
            title="✅ New Task Added",
            message="Task 'Test Task' has been added to your schedule!",
            app_name="Schedulr",
            timeout=5
        )

    @patch('schedulr.notifier.notification.notify')
    def test_check_due_tasks(self, mock_notify):
        self.notifier.check_due_tasks()
        mock_notify.assert_called_once_with(
            title="Task Due Soon: Test Task",
            message="Your task 'Test Task' is due in 5 seconds!",
            app_name="Schedulr",
            timeout=10
        )

    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        self.assertEqual(conn.row_factory, sqlite3.Row)

    def test_close_db_connection(self):
        conn = get_db_connection()
        close_db_connection()
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

if __name__ == '__main__':
    unittest.main()