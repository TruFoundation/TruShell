import re
from pathlib import Path

def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_run_csv_view_file_not_found() -> None:
    from trushell.commands.data import run_csv_view

    output = _strip_ansi(run_csv_view("missing_file.csv"))
    assert "Error: File '" in output
    assert "not found." in output


def test_run_csv_view_empty_file(tmp_path: Path) -> None:
    from trushell.commands.data import run_csv_view

    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))
    assert "Warning: File is empty." in output


def test_run_csv_view_shows_limited_rows(tmp_path: Path) -> None:
    from trushell.commands.data import run_csv_view

    file_path = tmp_path / "users.csv"
    rows = ["ID,Name,Email"] + [f"{i},User {i},user{i}@example.com" for i in range(1, 54)]
    file_path.write_text("\n".join(rows), encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))

    assert "ID" in output
    assert "Name" in output
    assert "Email" in output
    assert "User 1" in output
    assert "User 50" in output
    assert "User 51" not in output
    assert "...and 3 more rows" in output
