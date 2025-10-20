from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, DataTable, Label
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
        width: 70%;
        height: 70%;
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
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        border: solid $primary 50%;
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
                else:
                    yield Static("No tasks for this day", classes="no-tasks")
            
            with Horizontal(id="modal-footer"):
                yield Button("Close", id="close", classes="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Close the modal"""
        if event.button.id == "close":
            self.dismiss()


class SettingsModal(ModalScreen):
    """Modal screen for application settings"""

    CSS = """
    SettingsModal {
        align: center middle;
    }

    #settings-container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #settings-header {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
        background: $primary;
        border-bottom: solid $primary-lighten-1;
    }

    #settings-content {
        height: 1fr;
        padding: 1;
    }

    .setting-item {
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        border: solid $primary 50%;
    }

    .setting-label {
        text-style: bold;
        padding: 0 1;
    }

    .setting-control {
        padding: 0 1;
    }

    .checkbox-setting {
        layout: horizontal;
        align: center middle;
    }

    #settings-footer {
        layout: horizontal;
        height: auto;
        padding: 1;
        align: center middle;
    }

    .settings-button {
        width: 15;
        background: $primary;
        color: $text;
        margin: 0 1;
    }

    .settings-button:hover {
        background: $primary-lighten-1;
    }

    .close-button {
        background: $error;
    }

    .close-button:hover {
        background: $error-lighten-1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = {
            "notifications": True,
            "autostart": False,
            "theme": "light",
            "reminder_time": "15",
            "sound_enabled": True,
            "default_view": "calendar",
            "week_start": "monday",
            "time_format": "24h",
            "show_completed": True,
            "default_duration": "30",
            "working_hours_start": "09:00",
            "working_hours_end": "17:00"
        }

    def compose(self) -> ComposeResult:
        with Container(id="settings-container"):
            yield Static("Settings", id="settings-header")

            with VerticalScroll(id="settings-content"):
                # Notifications setting
                with Container(classes="setting-item"):
                    yield Static("🔔 Enable Notifications", classes="setting-label")
                    with Horizontal(classes="checkbox-setting"):
                        yield Button("ON" if self.settings["notifications"] else "OFF",
                                   id="toggle-notifications", classes="settings-button")

                # Autostart setting
                with Container(classes="setting-item"):
                    yield Static("🚀 Start on Boot", classes="setting-label")
                    with Horizontal(classes="checkbox-setting"):
                        yield Button("ON" if self.settings["autostart"] else "OFF",
                                   id="toggle-autostart", classes="settings-button")

                # Theme setting
                with Container(classes="setting-item"):
                    yield Static("🎨 Theme", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["theme"].title(), id="theme-button", classes="settings-button")

                # Reminder time setting
                with Container(classes="setting-item"):
                    yield Static("⏰ Default Reminder Time (minutes)", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(f"{self.settings['reminder_time']} min",
                                   id="reminder-time-button", classes="settings-button")

                # Sound notifications setting
                with Container(classes="setting-item"):
                    yield Static("🔊 Sound Notifications", classes="setting-label")
                    with Horizontal(classes="checkbox-setting"):
                        yield Button("ON" if self.settings["sound_enabled"] else "OFF",
                                   id="toggle-sound", classes="settings-button")

                # Default view setting
                with Container(classes="setting-item"):
                    yield Static("📅 Default View", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["default_view"].title(), id="view-button", classes="settings-button")

                # Week start setting
                with Container(classes="setting-item"):
                    yield Static("📆 Week Starts On", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["week_start"].title(), id="week-start-button", classes="settings-button")

                # Time format setting
                with Container(classes="setting-item"):
                    yield Static("🕐 Time Format", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["time_format"].upper(), id="time-format-button", classes="settings-button")

                # Show completed tasks setting
                with Container(classes="setting-item"):
                    yield Static("✅ Show Completed Tasks", classes="setting-label")
                    with Horizontal(classes="checkbox-setting"):
                        yield Button("ON" if self.settings["show_completed"] else "OFF",
                                   id="toggle-completed", classes="settings-button")

                # Default task duration setting
                with Container(classes="setting-item"):
                    yield Static("⏱️ Default Task Duration (minutes)", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(f"{self.settings['default_duration']} min",
                                   id="duration-button", classes="settings-button")

                # Working hours start setting
                with Container(classes="setting-item"):
                    yield Static("🌅 Working Hours Start", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["working_hours_start"],
                                   id="work-start-button", classes="settings-button")

                # Working hours end setting
                with Container(classes="setting-item"):
                    yield Static("🌇 Working Hours End", classes="setting-label")
                    with Horizontal(classes="setting-control"):
                        yield Button(self.settings["working_hours_end"],
                                   id="work-end-button", classes="settings-button")

            with Horizontal(id="settings-footer"):
                yield Button("Save", id="save-settings", classes="settings-button")
                yield Button("Close", id="close-settings", classes="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle settings button presses"""
        button_id = event.button.id

        if button_id == "toggle-notifications":
            self.settings["notifications"] = not self.settings["notifications"]
            self.refresh_setting_button(button_id, "ON" if self.settings["notifications"] else "OFF")

        elif button_id == "toggle-autostart":
            self.settings["autostart"] = not self.settings["autostart"]
            self.refresh_setting_button(button_id, "ON" if self.settings["autostart"] else "OFF")

        elif button_id == "theme-button":
            current_theme = self.settings["theme"]
            themes = ["light", "dark", "auto"]
            current_index = themes.index(current_theme)
            next_index = (current_index + 1) % len(themes)
            self.settings["theme"] = themes[next_index]
            self.refresh_setting_button(button_id, self.settings["theme"].title())

        elif button_id == "reminder-time-button":
            current_time = int(self.settings["reminder_time"])
            times = [5, 10, 15, 30, 60]
            current_index = times.index(current_time) if current_time in times else 2
            next_index = (current_index + 1) % len(times)
            self.settings["reminder_time"] = str(times[next_index])
            self.refresh_setting_button(button_id, f"{self.settings['reminder_time']} min")

        elif button_id == "toggle-sound":
            self.settings["sound_enabled"] = not self.settings["sound_enabled"]
            self.refresh_setting_button(button_id, "ON" if self.settings["sound_enabled"] else "OFF")

        elif button_id == "view-button":
            current_view = self.settings["default_view"]
            views = ["calendar", "list"]
            current_index = views.index(current_view)
            next_index = (current_index + 1) % len(views)
            self.settings["default_view"] = views[next_index]
            self.refresh_setting_button(button_id, self.settings["default_view"].title())

        elif button_id == "week-start-button":
            current_start = self.settings["week_start"]
            starts = ["sunday", "monday"]
            current_index = starts.index(current_start)
            next_index = (current_index + 1) % len(starts)
            self.settings["week_start"] = starts[next_index]
            self.refresh_setting_button(button_id, self.settings["week_start"].title())

        elif button_id == "time-format-button":
            current_format = self.settings["time_format"]
            formats = ["12h", "24h"]
            current_index = formats.index(current_format)
            next_index = (current_index + 1) % len(formats)
            self.settings["time_format"] = formats[next_index]
            self.refresh_setting_button(button_id, self.settings["time_format"].upper())

        elif button_id == "toggle-completed":
            self.settings["show_completed"] = not self.settings["show_completed"]
            self.refresh_setting_button(button_id, "ON" if self.settings["show_completed"] else "OFF")

        elif button_id == "duration-button":
            current_duration = int(self.settings["default_duration"])
            durations = [15, 30, 45, 60, 90, 120]
            current_index = durations.index(current_duration) if current_duration in durations else 1
            next_index = (current_index + 1) % len(durations)
            self.settings["default_duration"] = str(durations[next_index])
            self.refresh_setting_button(button_id, f"{self.settings['default_duration']} min")

        elif button_id == "work-start-button":
            current_start = self.settings["working_hours_start"]
            start_times = ["06:00", "07:00", "08:00", "09:00", "10:00"]
            current_index = start_times.index(current_start) if current_start in start_times else 3
            next_index = (current_index + 1) % len(start_times)
            self.settings["working_hours_start"] = start_times[next_index]
            self.refresh_setting_button(button_id, self.settings["working_hours_start"])

        elif button_id == "work-end-button":
            current_end = self.settings["working_hours_end"]
            end_times = ["16:00", "17:00", "18:00", "19:00", "20:00"]
            current_index = end_times.index(current_end) if current_end in end_times else 1
            next_index = (current_index + 1) % len(end_times)
            self.settings["working_hours_end"] = end_times[next_index]
            self.refresh_setting_button(button_id, self.settings["working_hours_end"])

        elif button_id == "save-settings":
            # Here you would typically save settings to a config file or database
            # For now, just show a confirmation
            self.notify("Settings saved successfully!")

        elif button_id == "close-settings":
            # Properly dismiss the settings modal
            try:
                self.dismiss()
            except Exception as e:
                # Fallback: try to pop screen if dismiss fails
                try:
                    self.app.pop_screen()
                except Exception:
                    pass  # Last resort - do nothing if all else fails

    def refresh_setting_button(self, button_id: str, new_label: str):
        """Update a setting button's label"""
        button = self.query_one(f"#{button_id}", Button)
        button.label = new_label


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
            yield Button("⚙️ Settings", id="settings-button", classes="nav-button")
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
            modal = TaskModal(date_tasks, selected_date)
            self.app.push_screen(modal)
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

    def action_open_settings(self) -> None:
        """Action to open settings modal"""
        try:
            settings_modal = SettingsModal()
            self.app.push_screen(settings_modal)
        except Exception as e:
            self.notify(f"Error opening settings: {str(e)}", severity="error")

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