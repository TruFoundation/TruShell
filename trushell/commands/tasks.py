from __future__ import annotations

from typing import Callable

import typer

from trushell.core.database import complete_todo, delete_todo, get_all_todos, insert_todo, update_todo
from trushell.core.models import Todo


def add_task(args: str) -> None:
    """Add a new task to the todo list.

    Supports two formats:
        addtask "task text" "category"
        addtask task text here
    """
    if not args.strip():
        typer.secho('⚠️ Missing arguments. Syntax: addtask "task-name" "category"', fg=typer.colors.YELLOW)
        return

    # Try to parse quoted arguments: "task text" "category"
    import shlex
    try:
        parts = shlex.split(args)
    except ValueError:
        parts = args.strip().split(maxsplit=1)

    if len(parts) >= 2:
        task_text = parts[0]
        category = parts[1]
    else:
        task_text = parts[0]
        category = "General"

    todo = Todo(task=task_text, category=category)
    insert_todo(todo)
    typer.secho("✅ Task added.", fg=typer.colors.GREEN)


def show_tasks(_: str) -> None:
    """Display the current todo list."""
    tasks = get_all_todos()
    if not tasks:
        typer.echo("No tasks found.")
        return

    for index, task in enumerate(tasks, start=1):
        status = "✅" if task.status == 2 else "❌"
        typer.echo(f"{index}. {task.task} [{task.category}] {status}")


def complete_task(args: str) -> None:
    """Mark a todo item as complete."""
    if not args.strip() or not args.strip().isdigit():
        typer.secho("⚠️ Usage: task done <task-number>", fg=typer.colors.YELLOW)
        return

    index = int(args.strip()) - 1
    try:
        complete_todo(index)
        typer.secho("✅ Task completed.", fg=typer.colors.GREEN)
    except Exception as error:
        typer.secho(f"❌ Task error: {error}", fg=typer.colors.RED)


def remove_task(args: str) -> None:
    """Remove a task by its numeric position."""
    if not args.strip() or not args.strip().isdigit():
        typer.secho("⚠️ Usage: task remove <task-number>", fg=typer.colors.YELLOW)
        return

    index = int(args.strip()) - 1
    try:
        delete_todo(index)
        typer.secho("✅ Task removed.", fg=typer.colors.GREEN)
    except Exception as error:
        typer.secho(f"❌ Task error: {error}", fg=typer.colors.RED)


def update_task(args: str) -> None:
    """Update an existing task's text and/or category."""
    parts = args.split(maxsplit=2)
    if len(parts) < 2 or not parts[0].isdigit():
        typer.secho('⚠️ Usage: task update <task-number> "<task>" ["<category>"]', fg=typer.colors.YELLOW)
        return

    index = int(parts[0]) - 1
    task_text = parts[1].strip('"') if len(parts) >= 2 else None
    category = parts[2].strip('"') if len(parts) == 3 else None

    try:
        update_todo(index, task_text, category)
        typer.secho("✅ Task updated.", fg=typer.colors.GREEN)
    except Exception as error:
        typer.secho(f"❌ Task error: {error}", fg=typer.colors.RED)


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
        typer.secho("⚠️ Usage: task <add|show|done|list|remove|update> [options]", fg=typer.colors.YELLOW)
        return

    parts = args.split(maxsplit=1)
    subcmd = parts[0].lower()
    subargs = parts[1] if len(parts) > 1 else ""

    handler = subcommands.get(subcmd)
    if handler:
        try:
            handler(subargs)
        except Exception as error:
            typer.secho(f"❌ Task error: {error}", fg=typer.colors.RED)
    else:
        typer.secho(f"❓ Unknown task subcommand: {subcmd}", fg=typer.colors.YELLOW)
