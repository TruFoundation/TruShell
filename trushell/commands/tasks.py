from __future__ import annotations

from typing import Callable

from trushell.core.database import complete_todo, delete_todo, get_all_todos, insert_todo, update_todo
from trushell.core.models import Todo


def add_task(args: str) -> None:
    """Add a new task to the todo list. The full remainder is treated as the task."""
    if not args.strip():
        print("Usage: task add <task>")
        return

    task_text = args.strip()
    todo = Todo(task=task_text, category="General")
    insert_todo(todo)
    print("Task added.")


def show_tasks(_: str) -> None:
    """Display the current todo list."""
    tasks = get_all_todos()
    if not tasks:
        print("No tasks found.")
        return

    for index, task in enumerate(tasks, start=1):
        status = "✅" if task.status == 2 else "❌"
        print(f"{index}. {task.task} [{task.category}] {status}")


def complete_task(args: str) -> None:
    """Mark a todo item as complete."""
    if not args.strip() or not args.strip().isdigit():
        print("Usage: task done <task-number>")
        return

    index = int(args.strip()) - 1
    try:
        complete_todo(index)
        print("Task completed.")
    except Exception as error:
        print(f"Task error: {error}")


def remove_task(args: str) -> None:
    """Remove a task by its numeric position."""
    if not args.strip() or not args.strip().isdigit():
        print("Usage: task remove <task-number>")
        return

    index = int(args.strip()) - 1
    try:
        delete_todo(index)
        print("Task removed.")
    except Exception as error:
        print(f"Task error: {error}")


def update_task(args: str) -> None:
    """Update an existing task's text and/or category."""
    parts = args.split(maxsplit=2)
    if len(parts) < 2 or not parts[0].isdigit():
        print('Usage: task update <task-number> "<task>" ["<category>"]')
        return

    index = int(parts[0]) - 1
    task_text = parts[1].strip('"') if len(parts) >= 2 else None
    category = parts[2].strip('"') if len(parts) == 3 else None

    try:
        update_todo(index, task_text, category)
        print("Task updated.")
    except Exception as error:
        print(f"Task error: {error}")


def list_tasks(_: str) -> None:
    """Alias for show_tasks."""
    show_tasks("")


def run_task_command(args: str) -> None:
    """Dispatch task subcommands from the manifest-driven task wrapper."""
    subcommands: dict[str, Callable[[str], None]] = {
        "add": add_task,
        "show": show_tasks,
        "done": complete_task,
        "list": list_tasks,
        "remove": remove_task,
        "delete": remove_task,
        "update": update_task,
    }

    if not args.strip():
        print("Usage: task <add|show|done|list|remove|update> [options]")
        return

    parts = args.split(maxsplit=1)
    subcmd = parts[0].lower()
    subargs = parts[1] if len(parts) > 1 else ""

    handler = subcommands.get(subcmd)
    if handler:
        try:
            handler(subargs)
        except Exception as error:
            print(f"Task error: {error}")
    else:
        print(f"Unknown task subcommand: {subcmd}")
