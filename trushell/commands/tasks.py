from __future__ import annotations

from typing import Callable

from trushell.core.database import complete_todo, get_all_todos, insert_todo
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
    }

    if not args.strip():
        print("Usage: task <add|show|done|list> [options]")
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
