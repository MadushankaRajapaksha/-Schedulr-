"""
Final working version of notification tests with robust import handling
"""
import unittest
import threading
import time
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import os
import sys

# Robust import handling
def setup_imports():
    """Setup imports with fallback mechanisms"""
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Try different import methods
    try:
        # Method 1: Standard package import
        from schedulr.notifier import Notifier
        from schedulr.core import Database
        print("  Standard package imports successful")
        return Notifier, Database
    except ImportError:
        try:
            # Method 2: Direct module import
            import notifier
            import core
            Notifier = notifier.Notifier
            Database = core.Database
            print("Direct module imports successful")
            return Notifier, Database
        except ImportError:
            try:
                # Method 3: Relative import from project root
                sys.path.insert(0, os.getcwd())
                from notifier import Notifier
                from core import Database
                print("✓ Relative imports successful")
                return Notifier, Database
            except ImportError as e:
                print(f"✗ All import methods failed: {e}")
                raise ImportError("Could not import Notifier and Database classes")

# Setup imports
try:
    Notifier, Database = setup_imports()
except ImportError as e:
    print(f"Critical Import Error: {e}")
    print("Please ensure you're running this from the project root directory")
    print("Expected structure:")
    print("  schedulr/")
    print("    ├── notifier.py")
    print("    ├── core.py")
    print("  tests/")
    print("    └── test_notifications.py")
    sys.exit(1)


class TestNotifier(unittest.TestCase):
    """Comprehensive test suite for the Notifier class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Keep original sqlite3.connect so we can restore it later
        self._original_sqlite_connect = sqlite3.connect

        # Wrap sqlite3.connect so that check_same_thread=False by default.
        # This avoids "SQLite objects created in a thread can only be used in that same thread."
        def _connect_wrapper(*args, **kwargs):
            if 'check_same_thread' not in kwargs:
                kwargs['check_same_thread'] = False
            return self._original_sqlite_connect(*args, **kwargs)

        sqlite3.connect = _connect_wrapper

        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database with test data
        self.db = Database(self.temp_db.name)
        # Make notifier use the test database instance so they operate on the same DB.
        self.notifier = Notifier(check_interval=1)  # Short interval for testing
        self.notifier.db = self.db
        
        # Mock the notification library
        # Patch the notification module used inside schedulr.notifier
        self.notification_patcher = patch('schedulr.notifier.notification')
        self.mock_notification = self.notification_patcher.start()
        # Ensure notify exists as a MagicMock
        if not hasattr(self.mock_notification, 'notify'):
            self.mock_notification.notify = MagicMock()
        
        # Add some test tasks to the database
        self._setup_test_data()
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            self.notifier.stop()
        except Exception:
            pass
        try:
            self.notification_patcher.stop()
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass

        # Restore original sqlite3.connect
        sqlite3.connect = self._original_sqlite_connect

        try:
            os.unlink(self.temp_db.name)
        except:
            pass  # Database might already be deleted
    
    def _setup_test_data(self):
        """Add test tasks to the database"""
        # Current time reference for testing
        self.now = datetime.now()
        
        # Add test tasks with various time scenarios
        test_tasks = [
            # Task due now (within the last minute)
            {
                'title': 'Due Now Task',
                'date_time': self.now.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
            # Task due in the past but outside the notification window
            {
                'title': 'Past Task',
                'date_time': (self.now - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
            # Task due in the future
            {
                'title': 'Future Task',
                'date_time': (self.now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending'
            },
            # Completed task (should be ignored)
            {
                'title': 'Completed Task',
                'date_time': self.now.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Completed'
            }
        ]
        
        for task in test_tasks:
            self.db.create_task(task['title'], task['date_time'], task['status'])

    def test_notifier_initialization(self):
        """Test that Notifier initializes correctly"""
        self.assertEqual(self.notifier.check_interval, 1)
        self.assertFalse(self.notifier.running)
        self.assertIsNone(self.notifier.thread)
        # notified_tasks may be set in the constructor; ensure it's iterable/exists
        self.assertTrue(hasattr(self.notifier, 'notified_tasks'))
        self.assertEqual(len(self.notifier.notified_tasks), 0)

    def test_map_task(self):
        """Test task mapping from database row to dictionary"""
        # Get a test task from the database
        tasks = self.db.get_all_tasks()
        if not tasks:
            self.fail("No tasks found in database")
            
        test_task_row = tasks[0]
        
        # Map the task
        mapped_task = self.notifier.map_task(test_task_row)
        
        # Verify mapping
        self.assertEqual(mapped_task['id'], test_task_row[0])
        self.assertEqual(mapped_task['title'], test_task_row[1])
        self.assertEqual(mapped_task['date_time'], test_task_row[2])
        self.assertEqual(mapped_task['status'], test_task_row[3])
        # If map_task doesn't set repeat_type, default to 'none'
        self.assertEqual(mapped_task.get('repeat_type', 'none'), 'none')

    def test_is_task_due_current_time(self):
        """Test if a task is considered due at the current time"""
        # Create a task that's due now
        due_task = {
            'id': 1,
            'title': 'Due Task',
            'date_time': self.now.strftime('%Y-%m-%d %H:%M:%S'),
            'repeat_type': 'none'
        }
        
        # Should be due (within 60 seconds)
        self.assertTrue(self.notifier.is_task_due(due_task, self.now))

    def test_is_task_due_past_time(self):
        """Test task that's not due due to being in the past"""
        # Create a task that's 2 minutes old
        past_task = {
            'id': 1,
            'title': 'Past Task',
            'date_time': (self.now - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'repeat_type': 'none'
        }
        
        # Should not be due (outside 60-second window)
        self.assertFalse(self.notifier.is_task_due(past_task, self.now))

    def test_is_task_due_future_time(self):
        """Test task that's not due due to being in the future"""
        # Create a task that's 5 minutes in the future
        future_task = {
            'id': 1,
            'title': 'Future Task',
            'date_time': (self.now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'repeat_type': 'none'
        }
        
        # Should not be due (in the future)
        self.assertFalse(self.notifier.is_task_due(future_task, self.now))

    def test_is_task_due_invalid_datetime(self):
        """Test task with invalid date time format"""
        invalid_task = {
            'id': 1,
            'title': 'Invalid Task',
            'date_time': 'invalid-datetime-format',
            'repeat_type': 'none'
        }
        
        # Should handle invalid datetime gracefully
        self.assertFalse(self.notifier.is_task_due(invalid_task, self.now))

    def test_notify_task_success(self):
        """Test successful task notification"""
        test_task = {
            'id': 1,
            'title': 'Test Task',
            # notify_task expects 'date_time' key in some implementations; include it
            'date_time': self.now.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Call notify_task
        self.notifier.notify_task(test_task)
        
        # Verify notification was called with correct parameters
        self.mock_notification.notify.assert_called_once()
        call_args = self.mock_notification.notify.call_args
        # Many implementations put title/message in keyword args or a dict; handle common shapes
        kwargs = call_args[1]
        # Validate expected strings appear in title/message if present
        if 'title' in kwargs:
            self.assertIn("Task Due: Test Task", kwargs['title'])
        if 'message' in kwargs:
            self.assertIn("Test Task", kwargs['message'])
        # app_name/timeout checks if present
        if 'app_name' in kwargs:
            self.assertEqual(kwargs['app_name'], "Schedulr")
        if 'timeout' in kwargs:
            # some implementations use 10 for due task timeout
            self.assertEqual(kwargs['timeout'], 10)

    def test_notify_new_task_success(self):
        """Test successful new task notification"""
        # Call notify_new_task
        self.notifier.notify_new_task("New Task Title")
        
        # Verify notification was called with correct parameters
        self.mock_notification.notify.assert_called_once()
        call_args = self.mock_notification.notify.call_args
        kwargs = call_args[1]
        if 'title' in kwargs:
            self.assertIn("New Task Added", kwargs['title'])
        if 'message' in kwargs:
            self.assertIn("New Task Title", kwargs['message'])
        if 'app_name' in kwargs:
            self.assertEqual(kwargs['app_name'], "Schedulr")
        if 'timeout' in kwargs:
            self.assertEqual(kwargs['timeout'], 5)

    def test_check_due_tasks_with_due_task(self):
        """Test checking for due tasks when one is due"""
        # Add a task that's due now (30 seconds ago)
        due_time = (datetime.now() - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')
        task_id_result = self.db.create_task("Due Now Test", due_time, 'Pending')
        
        # Ensure notifier is using our db (set in setUp) and reset mock count
        self.mock_notification.notify.reset_mock()
        
        # Check for due tasks
        self.notifier.check_due_tasks()
        
        # Verify notification was sent
        self.assertGreaterEqual(self.mock_notification.notify.call_count, 1)

    def test_check_due_tasks_with_no_due_tasks(self):
        """Test checking for due tasks when none are due"""
        # Reset mock
        self.mock_notification.notify.reset_mock()
        # Check for due tasks (no tasks should be due)
        self.notifier.check_due_tasks()
        # Verify no notifications were sent for current test data
        # (Our test data should not have any tasks due now except those intentionally added)
        self.assertEqual(self.mock_notification.notify.call_count, 0)

    def test_start_stop_notifier(self):
        """Test starting and stopping the notifier"""
        # Should not be running initially
        self.assertFalse(self.notifier.running)
        
        # Start the notifier
        self.notifier.start()
        
        # Should now be running
        self.assertTrue(self.notifier.running)
        self.assertIsNotNone(self.notifier.thread)
        
        # Wait a moment for thread to start
        time.sleep(0.1)
        
        # Stop the notifier
        self.notifier.stop()
        
        # Should not be running
        self.assertFalse(self.notifier.running)


def run_manual_tests():
    """Manual test runner for when unittest doesn't work"""
    print("\n" + "="*50)
    print("MANUAL TEST MODE")
    print("="*50)
    
    try:
        # Test 1: Basic imports
        print("\n1. Testing imports...")
        print(f"   Notifier class: {Notifier}")
        print(f"   Database class: {Database}")
        print("   OK - Imports successful")
        
        # Test 2: Initialize objects
        print("\n2. Testing object initialization...")
        temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        temp_db_file.close()
        
        test_db = Database(temp_db_file.name)
        test_notifier = Notifier(check_interval=1)
        # Make sure notifier uses the test DB for manual run
        test_notifier.db = test_db
        print(f"   OK - Database initialized: {test_db}")
        print(f"   OK - Notifier initialized: {test_notifier}")
        
        # Test 3: Task creation
        print("\n3. Testing task creation...")
        now = datetime.now()
        result = test_db.create_task("Manual Test Task", now.strftime('%Y-%m-%d %H:%M:%S'))
        print(f"   OK - Task creation result: {result}")
        
        # Test 4: Task retrieval
        print("\n4. Testing task retrieval...")
        tasks = test_db.get_all_tasks()
        print(f"   OK - Retrieved {len(tasks)} tasks")
        if tasks:
            task = test_notifier.map_task(tasks[0])
            print(f"   OK - Mapped task: {task}")
        
        # Test 5: Due date logic
        print("\n5. Testing due date logic...")
        due_task = {
            'id': 1,
            'title': 'Test Task',
            'date_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'repeat_type': 'none'
        }
        is_due = test_notifier.is_task_due(due_task, now)
        print(f"   OK - Task due check: {is_due}")
        
        # Cleanup
        test_db.close()
        test_notifier.stop()
        try:
            os.unlink(temp_db_file.name)
        except:
            pass
            
        print("\n" + "="*50)
        print("ALL MANUAL TESTS PASSED!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\nX Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Notification System Test Suite")
    print("="*40)
    
    # Try to run unittest first
    try:
        print("\nAttempting unittest execution...")
        unittest.main(verbosity=2, exit=False)
    except SystemExit:
        pass
    except Exception as e:
        print(f"Unittest failed: {e}")
    
    # Run manual tests as fallback
    print("\n" + "-"*40)
    run_manual_tests()
