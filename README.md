# Schedulr - Smart Terminal Task Scheduler

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

> A beautiful, feature-rich terminal-based task scheduler with a calendar visualization and desktop notifications.

## Features

### Core Functionality
- **Beautiful Terminal Interface**: Rich, colorful TUI built with Textual framework
- **SQLite Database**: Persistent storage for all your tasks
- **Calendar View**: Visual monthly calendar with task indicators
- **Search & Filter**: Quickly find tasks by title
- **Task Statistics**: Overview of pending and completed tasks

### Advanced Features
- **Desktop Notifications**: Get notified when tasks are due
- **Settings Management**: Customizable preferences and themes
- **Responsive Design**: Adaptive layout for different terminal sizes

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Task Management](#task-management)
- [Calendar View](#calendar-view)
- [Settings](#settings)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- A terminal with color support (recommended)

### Install from PyPI (Recommended)

```bash
pip install schedulr
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/MadushankaRajapaksha/-Schedulr- 
cd schedulr

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
schedulr
```

## Quick Start

### Launch the Application

```bash
# Launch the main interface
schedulr
```

### Create Your First Task

1. Launch Schedulr
2. Click the **➕ Add Task** button or press the navigation button
3. Fill in the task details:
   - **Task Title**: What needs to be done
   - **Date**: When it should happen (YYYY-MM-DD format)
   - **Time**: Hour and minute
4. Click **✅ Save Task**

## Usage

### Basic Navigation

- **🏠 Home**: View all tasks with search and statistics
- **➕ Add Task**: Create new tasks with the modal form
- **📅 Calendar**: Monthly calendar view with task indicators
- **⚙️ Settings**: Configure application preferences

### Keyboard Shortcuts

- **Tab**: Navigate between interface elements
- **Enter**: Activate buttons and submit forms
- **Escape**: Close modals or go back
- **Arrow Keys**: Navigate in calendar view

### Search Functionality

Use the search bar in the Home view to filter tasks by title.

## Task Management

### Creating Tasks

Tasks can be created through the **➕ Add Task** modal with the following fields:

- **Title**: Task description (required)
- **Date**: Target date in YYYY-MM-DD format
- **Time**: Hour (0-23) and minute (0-59)

### Task Status

Tasks have the following status levels:
- **⏳ Pending**: Not yet completed
- **✅ Completed**: Finished tasks

### Task Operations

- **View**: Click on a date in the calendar to see tasks for that day.
- **Edit**: Modify task details.
- **Delete**: Remove tasks.
- **Mark Complete**: Change status to completed.

## Calendar View

### Monthly Overview

The calendar view displays:
- **Month Navigation**: Previous/Next month buttons
- **Task Indicators**: Days with tasks are highlighted
- **Today Highlighting**: Current date is specially marked
- **Task Preview**: Brief task list on each calendar day

### Calendar Navigation

- **◀ Prev**: Go to previous month
- **Next ▶**: Go to next month
- **Keyboard**: Use arrow keys for quick navigation
- **Click Days**: Click on calendar days to view tasks

## Development

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd schedulr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run in development mode
python -m schedulr
```

### Project Structure

```
schedulr/
├── __main__.py          # Entry point
├── cli.py              # Main Textual TUI application
├── core.py             # Database operations and task management
├── screens.py          # Calendar screen and modal screens
└── notifier.py         # Background notification system

data.db                # SQLite database (created automatically)
README.md             # This file
pyproject.toml        # Project configuration and dependencies
```

### Dependencies

```toml
[project]
dependencies = [
    "rich",
    "textual"
]
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Verify installation
pip show schedulr
```

#### Database Issues
```bash
# Reset database (WARNING: Deletes all tasks)
del data.db
schedulr
```

#### Display Problems
- Ensure terminal supports colors
- Try resizing terminal window
- Check font supports Unicode characters

## Contributing

We welcome contributions! Please see our Contributing Guide for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Textual](https://textual.textualize.io/) for the beautiful TUI framework
- [Rich](https://rich.readthedocs.io/) for enhanced terminal formatting