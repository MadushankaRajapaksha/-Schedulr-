from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Static,
    Input,
    Button,
    Label,
    Select,
)
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.binding import Binding
from textual import on
from textual.events import Event
from datetime import date, datetime, timedelta

from rich.console import Console
from pyfiglet import figlet_format

from .core import Database
from .screens import CalendarScreen  
from .notifier import TaskNotifier
import random

import sqlite3


def get_day_of_week(d):
    """Get day name from date"""
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    return days[d.weekday()]


class NavButton(Button):
    """Custom navigation button with icon"""

    def __init__(self, icon: str, label: str, **kwargs) -> None:
        super().__init__(icon, **kwargs)
        self.icon = icon
        self.label = label


# Sample task data


TEST_TASKS_DATA = [
    {
        "id": 1,
        "title": "Meeting",
        "date_time": "2023-07-25 09:00:00",
        "repeat_interval": "Weekly",
        "status": "Pending",
    }
]

# title, date_time, status
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


class TaskCard(Button):
    def __init__(self, task_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task_data = task_data
        self.task_id = task_data["id"]

    def compose(self) -> ComposeResult:
        task = self.task_data
        status_emoji = {"pending": "⏳", "completed": "✅"}
        status = status_emoji.get(task["status"], "⏳")

        # Format date and time nicely
        try:
            dt = datetime.strptime(task['date_time'], '%Y-%m-%d %H:%M:%S')
            time_str = dt.strftime('%I:%M %p')
            date_str = dt.strftime('%b %d, %Y')
            datetime_display = f"{date_str} at {time_str}"
        except:
            datetime_display = task['date_time']

        card_content = f"{status} {task['title']}\n⏰ {datetime_display}"
        yield Static(card_content, classes="task-card-content")


class Home(App):
    CSS = """
    Screen {
        layout: horizontal;
    }

    #left-nav {
        width: 18%;
        background: $panel;
        border-right: solid $primary;
        padding: 2 0;
        align: center top;
    }

    #right-content {
        width: 82%;
        padding: 0;
        layout: vertical;
        overflow-y: auto;
    }

    .nav-button {
        width: 90%;
        height: 4;
        margin-bottom: 1;
        background: $panel;
        color: $text;
        content-align: center middle;
        text-style: bold;
        border: none;
       
    }

    .nav-button:hover {
        background: $primary-darken-1;
        color: $text;
        border: solid $primary-lighten-1;
    }

    .nav-button.-active {
        background: $primary;
        color: $text;
        border: solid $accent;
    }

    #welcome-section {
        background: $primary-darken-3;
        padding: 2 3;
        margin: 0 2 1 2;
        border: solid $primary;
         
    }

    .search-label {
        text-style: bold;
        color: $text;
        padding: 0 0 1 0;
        
    }

    .tasks-header {
        text-style: bold;
        color: $accent;
        padding: 1 2;
        margin: 0 2;
        
        border-bottom: solid $primary;
    }

    #day {
        color: $accent;
        text-align: center;
        padding: 0 0 1 0;
        margin: 0;
        text-style: bold;
         
    }

    #greet {
        text-align: center;
        padding: 0 0 1 0;
        margin: 0;
        color: $text-muted;
     
    }

    #search-section {
        padding: 1 3;
        margin: 0 2 1 2;
        background: $surface;
        border: solid $primary;
         
    }

    .search-input {
        margin: 1 2 ;
        width: 100%;
        border: solid $primary;
    }

    .task-stats {
        text-align: center;
        padding: 1 1;
        color: $text;
        background: $success-darken-3;
        margin: 0 2 1 2;
        border: solid $primary;
       
        text-style: bold;
    }

    #tasks-container {
        width: 100%;
        padding: 1 2;
        overflow-y: auto;
    }

    TaskCard {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        background: $surface;
        border: solid $primary;
         
        padding: 0;
         
    }

    TaskCard:hover {
        background: $primary-darken-2;
        border: solid $accent;
    }

    .task-card-content {
        width: 100%;
        padding: 1 2;
        color: $text;
        text-style: bold;
    }

    TaskCard.-completed {
        opacity: 0.7;
        background: $success-darken-3;
        border: solid $success;
    }

    TaskCard.-completed:hover {
        opacity: 0.9;
        background: $success-darken-2;
        border: solid $success-lighten-1;
    }
    """

    def __init__(self, get_tasks_func=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_page = "home"
        self.db = Database()
        self.notifier = TaskNotifier()
        
        # Use the provided function to get tasks, or fetch them directly
        self.get_tasks_func = get_tasks_func
        self.tasks = self.get_tasks_func() if self.get_tasks_func else self.db.get_all_tasks()
        
        self.search_query = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal():
            with Vertical(id="left-nav"):
                yield NavButton("🏠", "Home", id="nav-home", classes="nav-button")
                yield NavButton("➕", "Add Task", id="nav-add", classes="nav-button")
                yield NavButton("📅", "Calendar", id="nav-calendar", classes="nav-button")
                 
                # yield NavButton("⚙️", "Settings", id="nav-settings", classes="nav-button")

            with Vertical(id="right-content"):
                # with Vertical(id="welcome-section"):
                #     banner = figlet_format(get_day_of_week(date.today()).upper(), font="small")
                #     yield Static(f"[bold cyan]{banner}[/bold cyan]", id="day")

                #     quotes = [
                #         "Believe you can and you're halfway there.",
                #         "The future belongs to those who believe in the beauty of their dreams.",
                #         "Success is not final, failure is not fatal: It is the courage to continue that counts.",
                #         "Don't watch the clock; do what it does. Keep going.",
                #         "The biggest risk is not taking any risk.",
                #     ]

                #     quote = random.choice(quotes)
                #     yield Static(f"[italic]{quote}[/italic]", id="greet")

                yield Input(
                    placeholder="Search by task title",
                    classes="search-input",
                    id="sInput",
                )

                yield Static(
                    "📊 Tasks: 0 |  ⏰ Pending: 0  |  ✅ Completed: 0  |  🔄 Recurring: 0",
                    classes="task-stats",
                )

                yield Static("📋 Your Tasks", classes="tasks-header")

                with VerticalScroll(id="tasks-container"):
                    pass

    @on(Button.Pressed, "#nav-add")
    async def open_task_create(self):
        self.push_screen(AddTaskModal(), self.handle_add_new_task)
        
    @on(Button.Pressed, "#nav-calendar")
    async def open_calendar(self):
        self.push_screen(CalendarScreen())
        
    # @on(Button.Pressed, "#nav-settings")
    # async def open_settings(self):
    #     self.push_screen(SettingsModal())

    # handle  add new task

    def handle_add_new_task(self, new_task):
        """Handle adding new task and updating display"""
        if new_task:
            try:
                # Save to database
                result = self.db.create_task(
                    title=new_task["title"],
                    date_time=new_task["date_time"]
                )

                if result.startswith("Success"):
                    # IMPORTANT: Reload tasks from database to get fresh data with new task
                    self.tasks = map_tasks(self.db.get_all_tasks())
                    self.refresh_task_list()
                
                    # Send new task notification
                    self.notifier.notify_new_task(new_task['title'])
                
                    # Show success notification
                    self.notify(f"✅ Task '{new_task['title']}' added successfully!")
                else:
                    self.notify(f"❌ Error adding task: {result}", severity="error")

            except sqlite3.Error as e:
                self.notify(f"❌ Error adding task: {str(e)}", severity="error")
        else:
            self.notify("❌ Task creation cancelled", severity="warning")

    def on_mount(self) -> None:
        home_btn = self.query_one("#nav-home", NavButton)
        home_btn.add_class("-active")

        # day_label = self.query_one("#day")
        # day_label.update(figlet_format(get_day_of_week(date.today()), font="small"))

        self.refresh_task_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Remove active class from all nav buttons
        for btn in self.query(".nav-button"):
            btn.remove_class("-active")

        event.button.add_class("-active")

    def refresh_task_list(self) -> None:
        """Refresh task list based on search query"""
        try:
            tasks_scroll = self.query_one("#tasks-container", VerticalScroll)
        except Exception:
            return  # Return early if element not found

        # Remove all existing task cards to prevent duplicate IDs
        tasks_scroll.remove_children()

        # Use the provided function to get tasks, or fetch them directly
        self.tasks = self.get_tasks_func() if self.get_tasks_func else map_tasks(self.db.get_all_tasks())

        # Filter tasks based on search query
        if self.search_query:
            filtered_tasks = [
                task
                for task in self.tasks
                if self.search_query.lower() in task["title"].lower()
            ]
        else:
            filtered_tasks = self.tasks

        # Mount filtered task cards
        for idx, task in enumerate(filtered_tasks):
            # Use a more unique ID that includes a timestamp or random component to prevent conflicts
            unique_id = f"task-{task['id']}-{hash(str(task['id']) + str(idx) + str(datetime.now().timestamp())) % 10000}"
            task_card = TaskCard(task, id=unique_id, classes="task-card")
            if task.get("status") and task["status"].lower() == "completed":
                task_card.add_class("-completed")
            tasks_scroll.mount(task_card)

        # Update statistics
        total_tasks = len(self.tasks)
        completed_tasks = len(
            [t for t in self.tasks if t.get("status") and t["status"].lower() == "completed"]
        )
        pending_tasks = total_tasks - completed_tasks
        # All tasks are now one-time, so no recurring tasks
        recurring_tasks = 0

        stats_label = self.query_one(".task-stats", Static)
        stats_label.update(
            f"📊 Tasks: {total_tasks}  |  ⏰ Pending: {pending_tasks}  |  ✅ Completed: {completed_tasks}  |  🔄 Recurring: {recurring_tasks}"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter tasks based on search input"""
        if event.input.id == "sInput":
            self.search_query = event.value.strip()
            self.refresh_task_list()
            
    def on_unmount(self) -> None:
        """Clean up resources when app is closed"""
        if hasattr(self, 'notifier') and self.notifier:
            self.notifier.stop()
        if hasattr(self, 'db') and self.db:
            self.db.close()
 
from typing import Optional, Dict, Any


class AddTaskModal(ModalScreen[Optional[Dict[str, Any]]]):
    """Modal screen for adding a new task"""

    CSS = """
    AddTaskModal {
        align: center middle;
    }
    
    #modal-container {
        width: 75;
        height: 40;
        background: $panel;
        border: thick $primary;
        padding: 0;
    }
    
    #modal-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
        background: $primary-darken-1;
    }
    
    #form-scroll {
        width: 100%;
        height: 1fr;
        padding: 2 2 1 2;
    }
    
    .form-group {
        height: auto;
        padding: 0;
        margin-bottom: 1;
    }
    
     
    
    .form-field {
        width: 1fr;
        margin: 0 1;
    }
    
    .form-field:first-child {
        margin-left: 0;
    }
    
    .form-field:last-child {
        margin-right: 0;
    }
    
    .form-label {
        width: 100%;
        color: $text;
        text-style: bold;
        padding: 0 0 1 0;
        margin: 0;
    }
    
    .form-input {
        width: 100%;
        border: solid $primary;
        margin: 0;
    }
    
    .form-select {
        width: 100%;
        margin: 0;
    }
    
    Select {
        height: 3;
    }
    
    Select > SelectCurrent {
        border: solid $primary;
        background: $surface;
    }
    
    Select > SelectCurrent:focus {
        border: solid $accent;
    }
    
    #button-group {
        layout: horizontal;
        height: auto;
        padding: 1 2;
        align: center middle;
    }
    
    .modal-button {
        width: 1fr;
        margin: 0 1;
    }
    
    .btn-save {
        background: $success;
        color: $text;
    }
    
    .btn-save:hover {
        background: $success-lighten-1;
    }
    
    .btn-cancel {
        background: $error;
        color: $text;
    }
    
    .btn-cancel:hover {
        background: $error-lighten-1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the modal UI"""
        with Container(id="modal-container"):
            yield Static("➕ Add New Task", id="modal-title")

            with VerticalScroll(id="form-scroll"):
                # Task Title Field
                with Vertical(classes="form-group"):
                    yield Label("📝 Task Title:", classes="form-label")
                    yield Input(
                        placeholder="Enter task title...",
                        id="input-title",
                        classes="form-input",
                    )

                # Date and Time Selection (side by side)
                with Horizontal(classes="form-group-row"):
                    # Date Field
                    with Vertical(classes="form-field"):
                        yield Label("📅 Date:", classes="form-label")
                        yield Input(
                            placeholder="YYYY-MM-DD",
                            id="input-date",
                            classes="form-input",
                        )

                    # Time Field (Hour)
                    with Vertical(classes="form-field"):
                        yield Label("⏰ Hour:", classes="form-label")
                        yield Input(
                            placeholder="HH (0-23)",
                            id="input-hour",
                            classes="form-input",
                        )

                    # Time Field (Minute)
                    with Vertical(classes="form-field"):
                        yield Label("⏰ Minute:", classes="form-label")
                        yield Input(
                            placeholder="MM (0-59)",
                            id="input-minute",
                            classes="form-input",
                        )

                    # AM/PM Selector
                     

            # Buttons
            with Horizontal():
                yield Button(
                    "✅ Save Task", id="btn-save", classes="modal-button btn-save"
                )
                yield Button(
                    "❌ Cancel", id="btn-cancel", classes="modal-button btn-cancel"
                )


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks in modal"""
        if event.button.id == "btn-save":
            # Get form values
            title = self.query_one("#input-title", Input).value.strip()
            date_input = self.query_one("#input-date", Input).value.strip()
            hour_input = self.query_one("#input-hour", Input).value.strip()
            minute_input = self.query_one("#input-minute", Input).value.strip()

             
            # Validate required fields
            if not title:
                self.app.notify("⚠️ Please enter a task title!", severity="warning")
                return

            # Set default date if empty
            if not date_input:
                date_input = date.today().strftime("%Y-%m-%d")

            # Validate date format
            try:
                datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                self.app.notify("⚠️ Invalid date format! Use YYYY-MM-DD", severity="error")
                return

            # Validate time inputs
            try:
                hour = int(hour_input) if hour_input else 12
                minute = int(minute_input) if minute_input else 0

                if not (0 <= hour <= 23):
                    self.app.notify("⚠️ Hour must be between 0 and 23!", severity="error")
                    return
                if not (0 <= minute <= 59):
                    self.app.notify("⚠️ Minute must be between 0 and 59!", severity="error")
                    return
            except ValueError:
                self.app.notify("⚠️ Invalid time format! Use numbers for hour and minute.", severity="error")
                return

             

            date_time = f"{date_input} {hour:02d}:{minute:02d}:00"

            new_task = {
                "title": title,
                "date_time": date_time,
                "status": "Pending",
            }

            # Dismiss modal and return the new task
            self.dismiss(new_task)

        elif event.button.id == "btn-cancel":
            # Dismiss modal without saving
            self.dismiss(None)
# TODO:


def run_app(get_tasks_func=None):
    """Entry point function for the CLI app"""
    app = Home(get_tasks_func=get_tasks_func)
    app.run()

# Create app instance for entry point
app = run_app
  
