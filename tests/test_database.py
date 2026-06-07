from trushell.core.database import _ensure_initialized, get_all_todos, get_db_connection, insert_todo
from trushell.core.models import Todo


def _use_temp_database(monkeypatch, tmp_path):
    db_path = tmp_path / "todos.db"
    monkeypatch.setattr("trushell.core.database._DB_PATH", db_path)
    monkeypatch.setattr("trushell.core.database._INITIALIZED", False)
    return db_path


def test_get_db_connection_returns_fresh_connection(monkeypatch, tmp_path) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    conn_one = get_db_connection()
    conn_two = get_db_connection()

    assert conn_one is not conn_two

    conn_one.close()
    conn_two.close()


def test_insert_todo_assigns_sequential_positions(monkeypatch, tmp_path) -> None:
    _use_temp_database(monkeypatch, tmp_path)

    _ensure_initialized()
    insert_todo(Todo(task="first", category="work"))
    insert_todo(Todo(task="second", category="work"))

    tasks = get_all_todos()

    assert [task.task for task in tasks] == ["first", "second"]
    assert [task.position for task in tasks] == [0, 1]


def test_get_all_todos_works_with_local_connections(monkeypatch, tmp_path) -> None:
    _use_temp_database(monkeypatch, tmp_path)

    _ensure_initialized()
    insert_todo(Todo(task="alpha", category="study"))

    assert len(get_all_todos()) == 1


def test_get_all_todos_returns_rows_ordered_by_position(monkeypatch, tmp_path) -> None:
    _use_temp_database(monkeypatch, tmp_path)

    _ensure_initialized()
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


def test_ensure_initialized_skips_lock_when_already_initialized(monkeypatch, tmp_path) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    _ensure_initialized()

    class FailingLock:
        def __enter__(self):
            raise AssertionError("lock should not be acquired after initialization")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("trushell.core.database._INITIALIZE_LOCK", FailingLock())

    _ensure_initialized()
