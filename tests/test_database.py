from trushell.database import _create_table, get_all_todos, get_db_connection, insert_todo
from trushell.model import Todo


def test_get_db_connection_returns_fresh_connection(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "todos.db"
    monkeypatch.setattr("trushell.database.DB_PATH", db_path)

    conn_one = get_db_connection()
    conn_two = get_db_connection()

    assert conn_one is not conn_two

    conn_one.close()
    conn_two.close()


def test_insert_todo_assigns_sequential_positions(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "todos.db"
    monkeypatch.setattr("trushell.database.DB_PATH", db_path)

    _create_table()
    insert_todo(Todo(task="first", category="work"))
    insert_todo(Todo(task="second", category="work"))

    tasks = get_all_todos()

    assert [task.task for task in tasks] == ["first", "second"]
    assert [task.position for task in tasks] == [0, 1]


def test_get_all_todos_works_with_local_connections(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "todos.db"
    monkeypatch.setattr("trushell.database.DB_PATH", db_path)

    _create_table()
    insert_todo(Todo(task="alpha", category="study"))

    assert len(get_all_todos()) == 1


def test_get_all_todos_returns_rows_ordered_by_position(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "todos.db"
    monkeypatch.setattr("trushell.database.DB_PATH", db_path)

    _create_table()
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO todos VALUES (?, ?, ?, ?, ?, ?)",
            ("second", "work", "", None, 0, 1),
        )
        conn.execute(
            "INSERT INTO todos VALUES (?, ?, ?, ?, ?, ?)",
            ("first", "work", "", None, 0, 0),
        )

    tasks = get_all_todos()

    assert [task.task for task in tasks] == ["first", "second"]
    assert [task.position for task in tasks] == [0, 1]
