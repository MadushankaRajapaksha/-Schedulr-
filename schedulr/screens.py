from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, DataTable, Label, Input
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from datetime import date, datetime, timedelta
from calendar import monthrange
from typing import Dict, List
from .core import Database


def map_tasks(db_data):
    """Map database tuple data to list of dictionaries"""
    tasks = []
    for i in db_data:
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


class TaskModal(ModalScreen):
    """Modal screen to show all tasks for a specific date"""
    
    CSS = """
    TaskModal {
        align: center middle;
    }
    
    #modal-container {
        width: 100%;
        height: auto;
        max-height:100%;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }
    
    #modal-header {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
        background: $primary;
        border-bottom: solid $primary-lighten-1;
    }
    
    #modal-content {
        height: 1fr;
        padding: 1;
    }
    
    .task-item {
        layout: horizontal;
        padding: 1;
        height: auto;
        min-height: 4;
        background: $panel;
        border: solid $primary;
        align: center middle;
        margin-bottom: 1;
    }
    
    .task-item.-completed {
        text-style: strike;
        opacity: 0.7;
    }
    
    .task-title {
        text-style: bold;
    }
    
    .task-time {
        color: $text-muted;
    }
    
    .task-status {
        padding: 0 1;
    }

    .task-buttons {
        width: auto;
        height: auto;
        dock: right;
        margin-left: 1;
    }

    .edit-button {
        margin-right: 1;
        background: $warning;
    }

    .delete-button {
        background: $error;
    }
    
    #modal-footer {
        layout: horizontal;
        height: auto;
        padding: 1;
        align: center middle;
    }
    
    .close-button {
        width: 15;
        background: $error;
        color: $text;
    }
    
    .close-button:hover {
        background: $error-lighten-1;
    }
    """
    
    def __init__(self, date_tasks: List[dict], selected_date: date, **kwargs) -> None:
        super().__init__(**kwargs)
        self.date_tasks = date_tasks
        self.selected_date = selected_date
    
    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(
                f"Tasks for {self.selected_date.strftime('%A, %B %d, %Y')}", 
                id="modal-header"
            )
            
            with VerticalScroll(id="modal-content"):
                if self.date_tasks:
                    for task in self.date_tasks:
                        status_symbol = "✅" if task.get("status") and task["status"].lower() == "completed" else "⏳"
                        task_time = task["date_time"].split(" ")[1] if task["date_time"] else "No time"
                        
                        with Container(classes="task-item"):
                            with Vertical():
                                if task.get("status") and task["status"].lower() == "completed":
                                    yield Static(
                                        f"{status_symbol} {task['title']}",
                                        classes="task-title -completed"
                                    )
                                else:
                                    yield Static(
                                        f"{status_symbol} {task['title']}",
                                        classes="task-title"
                                    )
                                yield Static(
                                    f"Time: {task_time}",
                                    classes="task-time"
                                )
                            with Horizontal(classes="task-buttons"):
                                yield Button("Edit", variant="warning", classes="edit-button", id=f"edit-{task['id']}")
                                yield Button("Delete", variant="error", classes="delete-button", id=f"delete-{task['id']}")
                else:
                    yield Static("No tasks for this day", classes="no-tasks")
            
            with Horizontal(id="modal-footer"):
                yield Button("Close", id="close", classes="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the modal"""
        button_id = event.button.id
        if button_id == "close":
            self.dismiss()
        elif button_id and button_id.startswith("delete-"):
            task_id = int(button_id.split("-")[1])
            db = Database()
            db.delete_task(task_id)
            db.close()
            self.dismiss(True)  # Dismiss and signal a refresh
        elif button_id and button_id.startswith("edit-"):
            task_id = int(button_id.split("-")[1])
            with Database() as db:
                task_data = db.get_task_by_id(task_id)
            if task_data:
                task_dict = {
                    "id": task_data[0],
                    "title": task_data[1],
                    "date_time": task_data[2],
                    "status": task_data[3],
                }
                self.app.push_screen(EditTaskModal(task=task_dict), self.handle_edit_task)


    def handle_edit_task(self, updated: bool):
        """Handle the result of the edit modal."""
        if updated:
            self.dismiss(True) # Dismiss and signal a refresh

class EditTaskModal(ModalScreen):
    """Modal screen for editing an existing task"""

    CSS = """
    EditTaskModal {
        align: center middle;
    }
    #edit-modal-container {
        width: 80;
        height: 25;
        background: $surface;
        border: thick $primary;
    }
    #edit-modal-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }
    #edit-form {
        padding: 1 2;
    }
    .edit-input {
        margin-bottom: 1;
    }
    #edit-buttons {
        layout: horizontal;
        padding: 0 2;
    }
    """

    def __init__(self, task: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task_data = task

    def compose(self) -> ComposeResult:
        with Container(id="edit-modal-container"):
            yield Static("Edit Task", id="edit-modal-title")
            with Container(id="edit-form"):
                yield Label("Title:")
                yield Input(value=self.task_data["title"], id="edit-title", classes="edit-input")
                yield Label("Date (YYYY-MM-DD HH:MM):")
                yield Input(value=self.task_data["date_time"].split(":00")[0], id="edit-datetime", classes="edit-input")
                yield Label("Status:")
                yield Input(value=self.task_data["status"], id="edit-status", classes="edit-input")
            with Horizontal(id="edit-buttons"):
                yield Button("Save", variant="success", id="save-edit")
                yield Button("Cancel", variant="default", id="cancel-edit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-edit":
            title = self.query_one("#edit-title", Input).value
            date_time_str = self.query_one("#edit-datetime", Input).value + ":00"
            status = self.query_one("#edit-status", Input).value
            
            with Database() as db:
                db.update_task(
                    task_id=self.task_data["id"],
                    title=title,
                    date_time=date_time_str,
                    status=status,
                )
            self.dismiss(True)
        elif event.button.id == "cancel-edit":
            self.dismiss(False)


class DateButton(Button):
    """Custom button for calendar dates that stores date information"""
    
    def __init__(self, label: str, date_info: date, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.date_info = date_info


class CalendarScreen(Screen):
    """Calendar screen showing tasks organized by date"""

    BINDINGS = [
        Binding("escape", "go_home", "Go Home"),
        Binding("s", "open_settings", "Settings"),
        Binding("left", "prev_month", "Previous Month"),
        Binding("right", "next_month", "Next Month"),
    ]

    CSS = """
    CalendarScreen {
        layout: vertical;
    }
    
    #calendar-nav {
        height: auto;
        padding: 1 2;
        background: $panel;
        layout: horizontal;
        align: center middle;
    }
    
    #calendar-container {
        padding: 1 2;
        overflow-y: auto;
        height: 1fr;
    }
    
    .calendar-month-header {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1 0;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }
    
    .calendar-week {
        layout: horizontal;
        height: 8;
        width: 100%;
        margin-bottom: 1;
    }
    
    .calendar-day {
        width: 1fr;
        height: 100%;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }
    
    .calendar-day.-today {
        background: $success;
        border: solid $accent;
    }
    
    .calendar-day.-other-month {
        color: $text-muted;
        background: $panel-darken-1;
    }
    
    .calendar-day.-has-tasks {
        background: $primary-lighten-2;
    }
    
    .day-number {
        text-style: bold;
        text-align: right;
        padding: 0 1 1 0;
    }
    
    .day-tasks {
        padding: 1 1;
        overflow-y: auto;
    }
    
    .task-item {
        color: $text-muted;
        padding: 1 0;
    }
    
    .task-item.-completed {
        text-style: strike;
        opacity: 0.6;
    }
    
    .nav-button {
        width: auto;
        height: 3;
        margin: 0 1;
        background: $primary;
        color: $text;
    }
    
    .nav-button:hover {
        background: $primary-lighten-1;
    }
    
    .month-display {
        width: auto;
        padding: 0 2;
        text-style: bold;
        color: $text;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_date = date.today()
        self.db = Database()
        self.all_tasks = self.get_all_tasks_by_date()
        
        
    def get_all_tasks_by_date(self) -> Dict[str, List[dict]]:
        """Get all tasks from database grouped by date"""
        # Get data from database (should return list of tuples)
        data = self.db.get_all_tasks()

        # Map the database tuples to dictionaries
        mapped_tasks = map_tasks(data)

        # Group tasks by date
        tasks_by_date = {}
        for task in mapped_tasks:
            if task["date_time"]:
                # Extract date part from datetime string
                task_date = task["date_time"].split(" ")[0]
                if task_date not in tasks_by_date:
                    tasks_by_date[task_date] = []
                tasks_by_date[task_date].append(task)

        return tasks_by_date

    
    def get_month_dates(self, year: int, month: int) -> List[date]:
        """Get all dates for a given month"""
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        
        dates = []
        current_date = first_day
        while current_date <= last_day:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Calendar header with navigation
        with Horizontal(id="calendar-nav"):
            yield Button("🏠 Home", id="home-button", classes="nav-button")
            # yield Button("⚙️ Settings", id="settings-button", classes="nav-button")
            yield Button("◀ Prev", id="prev-month", classes="nav-button")
            yield Static(
                f"{self.current_date.strftime('%B %Y')}",
                id="month-display",
                classes="month-display"
            )
            yield Button("Next ▶", id="next-month", classes="nav-button")
        
        # Calendar container
        with ScrollableContainer(id="calendar-container"):
            yield from self.create_calendar_widgets(
                self.current_date.year, 
                self.current_date.month
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button presses and date button presses"""
        if event.button.id == "home-button":
            # Return to home screen using the same logic as keyboard shortcut
            self.action_go_home()
        elif event.button.id == "settings-button":
            # Open settings modal using the same logic as keyboard shortcut
            self.action_open_settings()
        elif hasattr(event.button, 'date_info'):
            # This is a date button
            selected_date = event.button.date_info
            date_str = selected_date.strftime('%Y-%m-%d')
            date_tasks = self.all_tasks.get(date_str, [])

            # Open modal with tasks for this date
            def modal_callback(refresh: bool):
                if refresh:
                    self.refresh_calendar()

            modal = TaskModal(date_tasks, selected_date)
            self.app.push_screen(modal, modal_callback)
        elif event.button.id in ["prev-month", "next-month"]:
            # Handle navigation buttons using action methods
            if event.button.id == "prev-month":
                self.action_prev_month()
            elif event.button.id == "next-month":
                self.action_next_month()

    def action_go_home(self) -> None:
        """Action to go back to home screen"""
        try:
            if hasattr(self.app, 'pop_screen'):
                self.app.pop_screen()
            else:
                self.app.exit()
        except Exception:
            self.app.exit()

     
    def action_prev_month(self) -> None:
        """Action to go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(
                year=self.current_date.year - 1,
                month=12
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month - 1
            )
        self.refresh_calendar()

    def action_next_month(self) -> None:
        """Action to go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(
                year=self.current_date.year + 1,
                month=1
            )
        else:
            self.current_date = self.current_date.replace(
                month=self.current_date.month + 1
            )
        self.refresh_calendar()

    def create_calendar_widgets(self, year: int, month: int):
        """Yield calendar widgets for a specific month"""
        # Month header
        yield Static(
            f"{date(year, month, 1).strftime('%B %Y')}", 
            classes="calendar-month-header"
        )
        
        # Weekday headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        with Horizontal(classes="calendar-week"):
            for day_name in weekdays:
                yield Static(day_name, classes="calendar-day day-header")
        
        # Get all dates for the month
        month_dates = self.get_month_dates(year, month)
        
        # Group dates by week
        weeks = []
        current_week = []
        
        # Add empty slots for days before the first of the month
        first_day_weekday = date(year, month, 1).weekday()
        for i in range(first_day_weekday):
            current_week.append(None)
        
        # Add actual dates
        for d in month_dates:
            current_week.append(d)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        
        # Fill last week
        if current_week:
            while len(current_week) < 7:
                current_week.append(None)
            weeks.append(current_week)
        
        # Create calendar weeks
        for week in weeks:
            with Horizontal(classes="calendar-week"):
                for day_date in week:
                    yield self.create_day_widget(day_date)

    def create_day_widget(self, day_date: date):
        """Create a widget for a single day with its tasks"""
        if day_date is None:
            # Empty day
            return Static("", classes="calendar-day -other-month")
        
        # Day number
        day_str = str(day_date.day)
        
        # Determine CSS classes
        day_classes = "calendar-day"
        if day_date == date.today():
            day_classes += " -today"
        elif day_date.month != self.current_date.month:
            day_classes += " -other-month"
        
        # Get tasks for this day
        date_str = day_date.strftime('%Y-%m-%d')
        day_tasks = self.all_tasks.get(date_str, [])
        
        if day_tasks:
            day_classes += " -has-tasks"
        
        # Build day content
        content = f"[bold]{day_str}[/bold]\n"
        if day_tasks:
            for task in day_tasks[:2]:  # Show max 2 tasks preview
                status = "✅" if task.get("status") and task["status"].lower() == "completed" else "⏳"
                content += f"{status} {task['title'][:12]}\n"
            if len(day_tasks) > 2:
                content += f"+{len(day_tasks) - 2} more"
        
        # Create button widget with date info
        return DateButton(content.strip(), date_info=day_date, classes=day_classes)

    def refresh_calendar(self):
        """Refresh the calendar display"""
        # Reload tasks
        self.all_tasks = self.get_all_tasks_by_date()

        # Remove and rebuild calendar
        calendar_container = self.query_one("#calendar-container", ScrollableContainer)
        calendar_container.remove_children()

        # Mount new widgets using compose-style mounting
        try:
            # Create a temporary list to hold widgets
            widgets = []
            for widget in self.create_calendar_widgets(
                self.current_date.year,
                self.current_date.month
            ):
                widgets.append(widget)

            # Mount all widgets at once
            calendar_container.compose_add_child(*widgets)
        except Exception as e:
            # Fallback: recreate the entire screen if mounting fails
            try:
                self.app.pop_screen()
                new_calendar = CalendarScreen()
                new_calendar.current_date = self.current_date  # Preserve the date
                self.app.push_screen(new_calendar)
            except Exception:
                pass  # If all else fails, just continue
            return

        # Update month display in header navigation
        try:
            month_display = self.query_one("#month-display", Static)
            month_display.update(f"{self.current_date.strftime('%B %Y')}")
        except Exception:
            pass  # If element not found, continue silently