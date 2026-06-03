from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from trushell.core.database import complete_todo, delete_todo, get_all_todos, insert_todo, update_todo
from trushell.core.models import Todo

console = Console()
app = typer.Typer(name="todo", help="Manage todo tasks.")


@app.command("addtask")
def addtask(task: str, category: str) -> None:
    """Add a task to the todo list."""
    todo = Todo(task=task, category=category)
    insert_todo(todo)
    typer.secho("Task added.", fg=typer.colors.GREEN)


@app.command("deletetask")
def deletetask(position: int) -> None:
    """Delete a task by its position."""
    delete_todo(position - 1)
    typer.secho("Task deleted.", fg=typer.colors.GREEN)


@app.command("updatetask")
def updatetask(position: int, task: str | None = None, category: str | None = None) -> None:
    """Update the task text or category."""
    update_todo(position - 1, task, category)
    typer.secho("Task updated.", fg=typer.colors.GREEN)


@app.command("completetask")
def completetask(position: int) -> None:
    """Mark a task as complete."""
    complete_todo(position - 1)
    typer.secho("Task completed.", fg=typer.colors.GREEN)


@app.command("showtasks")
def showtask() -> None:
    """Show the current todo list."""
    tasks = get_all_todos()
    console.print("[bold magenta]Todos[/bold magenta]", "💻")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("#", style="dim", width=6)
    table.add_column("Todo", min_width=20)
    table.add_column("Category", min_width=12, justify="right")
    table.add_column("Done", min_width=12, justify="right")

    def get_category_color(category: str) -> str:
        colors = {"Learn": "cyan", "YouTube": "red", "Sports": "cyan", "Study": "green"}
        return colors.get(category, "white")

    for idx, task in enumerate(tasks, start=1):
        color = get_category_color(task.category)
        is_done_str = "✅" if task.status == 2 else "❌"
        table.add_row(str(idx), task.task, f"[{color}]{task.category}[/{color}]", is_done_str)

    console.print(table)
