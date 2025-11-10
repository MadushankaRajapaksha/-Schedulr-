import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import time

from schedulr.notifier import TaskNotifier
from schedulr.core import Database

class TestTaskNotifier(unittest.TestCase):
    def setUp(self):
        """Set up a mock database and notifier for testing."""
        self.db = MagicMock()
        self.notifier = TaskNotifier()
        self.notifier.get_tasks_func = self.db.get_all_tasks

    @patch('schedulr.notifier.notify')
    def test_due_task_notification(self, mock_notify):
        """Test that a notification is sent for a due task."""
        now = datetime.now()
        due_time = now + timedelta(seconds=30)
        
        self.db.get_all_tasks.return_value = [{
            'id': 1,
            'title': 'Test Task',
            'date_time': due_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }]
        
        self.notifier.check_and_notify(self.db.get_all_tasks())
        
        mock_notify.assert_called_with("Task Due: Test Task")

    @patch('schedulr.notifier.notify')
    def test_no_notification_for_past_task(self, mock_notify):
        """Test that no notification is sent for a past task."""
        past_time = datetime.now() - timedelta(minutes=5)
        
        self.db.get_all_tasks.return_value = [{
            'id': 2,
            'title': 'Past Task',
            'date_time': past_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }]
        
        self.notifier.check_and_notify(self.db.get_all_tasks())
        
        mock_notify.assert_not_called()

    @patch('schedulr.notifier.notify')
    def test_no_notification_for_future_task(self, mock_notify):
        """Test that no notification is sent for a future task."""
        future_time = datetime.now() + timedelta(minutes=5)
        
        self.db.get_all_tasks.return_value = [{
            'id': 3,
            'title': 'Future Task',
            'date_time': future_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }]
        
        self.notifier.check_and_notify(self.db.get_all_tasks())
        
        mock_notify.assert_not_called()

    @patch('schedulr.notifier.notify')
    def test_no_notification_for_completed_task(self, mock_notify):
        """Test that no notification is sent for a completed task."""
        due_time = datetime.now() + timedelta(seconds=30)
        
        self.db.get_all_tasks.return_value = [{
            'id': 4,
            'title': 'Completed Task',
            'date_time': due_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed'
        }]
        
        self.notifier.check_and_notify(self.db.get_all_tasks())
        
        mock_notify.assert_not_called()

    @patch('schedulr.notifier.notify')
    def test_notification_for_recently_past_task(self, mock_notify):
        """Test that a notification is sent for a recently past task."""
        past_time = datetime.now() - timedelta(seconds=30)
        
        self.db.get_all_tasks.return_value = [{
            'id': 5,
            'title': 'Recently Past Task',
            'date_time': past_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }]
        
        self.notifier.check_and_notify(self.db.get_all_tasks())
        
        mock_notify.assert_called_with("Task Due: Recently Past Task")

if __name__ == '__main__':
    unittest.main()
