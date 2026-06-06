from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from platformdirs import user_data_dir

from trushell.core.models import Todo

# Global state to track initialization
_INITIALIZED = False
_DB_PATH: Optional[Path] = None


def _get_db_path() -> Path:
    """Get the path to the database file."""
    global _DB_PATH
    if _DB_PATH is None:
        data_dir = Path(user_data_dir("TruShell", "AkshajSinghal"))
        data_dir.mkdir(parents=True, exist_ok=True)
        _DB_PATH = data_dir / "todos.db"
    return _DB_PATH


def _ensure_initialized() -> None:
    """
    Create the database and tables if they don't exist.
    This function is idempotent and safe to call multiple times.
    Does NOT call get_db_connection() to avoid infinite recursion.
    """
    global _INITIALIZED
    
    if _INITIALIZED:
        return

    db_path = _get_db_path()
    
    # Open a direct connection to initialize.
    # We do NOT use get_db_connection() here to avoid recursion.
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS todos (
                task TEXT,
                category TEXT,
                date_added TEXT,
                date_completed TEXT,
                status INTEGER,
                position INTEGER
            )"""
        )
        conn.commit()
        _INITIALIZED = True
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    """
    Return a connection to the SQLite database.
    Ensures the database is initialized before returning the connection.
    """
    _ensure_initialized()
    db_path = _get_db_path()
    return sqlite3.connect(str(db_path), check_same_thread=False)


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
