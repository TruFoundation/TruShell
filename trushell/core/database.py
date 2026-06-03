from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from platformdirs import user_data_dir

from trushell.core.models import Todo

APP_NAME = "TruShell"
APP_AUTHOR = "AkshajSinghal"
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "todos.db"


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _create_table() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS todos (
                task TEXT,
                category TEXT,
                date_added TEXT,
                date_completed TEXT,
                status INTEGER,
                position INTEGER
            )"""
        )


_create_table()


def insert_todo(todo: Todo) -> None:
    with get_db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        todo.position = count if count is not None else 0
        conn.execute(
            "INSERT INTO todos VALUES (:task, :category, :date_added, :date_completed, :status, :position)",
            {
                "task": todo.task,
                "category": todo.category,
                "date_added": todo.date_added,
                "date_completed": todo.date_completed,
                "status": todo.status,
                "position": todo.position,
            },
        )


def get_all_todos() -> List[Todo]:
    with get_db_connection() as conn:
        results = conn.execute("SELECT * FROM todos ORDER BY position").fetchall()
    return [Todo(*result) for result in results]


def delete_todo(position: int) -> None:
    with get_db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0] or 0
        conn.execute("DELETE FROM todos WHERE position = :position", {"position": position})
        for pos in range(position + 1, count):
            conn.execute(
                "UPDATE todos SET position = :position_new WHERE position = :position_old",
                {"position_old": pos, "position_new": pos - 1},
            )


def _change_position(conn: sqlite3.Connection, old_position: int, new_position: int) -> None:
    conn.execute(
        "UPDATE todos SET position = :position_new WHERE position = :position_old",
        {"position_old": old_position, "position_new": new_position},
    )


def update_todo(position: int, task: str | None, category: str | None) -> None:
    with get_db_connection() as conn:
        if task is not None and category is not None:
            conn.execute(
                "UPDATE todos SET task = :task, category = :category WHERE position = :position",
                {"task": task, "category": category, "position": position},
            )
        elif task is not None:
            conn.execute(
                "UPDATE todos SET task = :task WHERE position = :position",
                {"task": task, "position": position},
            )
        elif category is not None:
            conn.execute(
                "UPDATE todos SET category = :category WHERE position = :position",
                {"category": category, "position": position},
            )


def complete_todo(position: int) -> None:
    from datetime import datetime

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE todos SET status = 2, date_completed = :date_completed WHERE position = :position",
            {"position": position, "date_completed": datetime.now().isoformat()},
        )
