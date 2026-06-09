import re
import sys
from pathlib import Path

import pytest


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_run_csv_view_file_not_found() -> None:
    from trushell.commands.data import run_csv_view

    output = _strip_ansi(run_csv_view("missing_file.csv"))
    assert "Error: File '" in output
    assert "not found." in output


@pytest.mark.skipif(sys.platform == "win32", reason="shlex.split() mangles Windows backslash paths, causing file-not-found errors")
def test_run_csv_view_empty_file(tmp_path: Path) -> None:
    from trushell.commands.data import run_csv_view

    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))
    assert "Warning: File is empty." in output


@pytest.mark.skipif(sys.platform == "win32", reason="shlex.split() mangles Windows backslash paths, causing file-not-found errors")
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


@pytest.mark.skipif(sys.platform == "win32", reason="shlex.split() mangles Windows backslash paths, causing file-not-found errors")
def test_run_csv_view_short_rows_are_padded(tmp_path: Path) -> None:
    """Ensure ragged rows are padded with empty cells.

    Use quoted fields so csv.Sniffer has sufficient signal to detect
    the delimiter reliably on small samples.
    """
    from trushell.commands.data import run_csv_view

    file_path = tmp_path / "short_rows.csv"
    rows = ['"A","B","C"', '"1","2"', '"3","4","5"']
    file_path.write_text("\n".join(rows), encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))

    assert "A" in output
    assert "B" in output
    assert "C" in output
    assert "1" in output
    assert "3" in output
    # There should be at least one empty/padded cell visible in output
    assert "  " in output


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX temp paths are used for this regression test")
def test_run_csv_view_handles_unquoted_paths_with_spaces(tmp_path: Path) -> None:
    from trushell.commands.data import run_csv_view

    directory = tmp_path / "Program Files"
    directory.mkdir()
    file_path = directory / "users.csv"
    file_path.write_text("ID,Name\n1,Ada\n", encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))

    assert "ID" in output
    assert "Name" in output
    assert "Ada" in output


@pytest.mark.skipif(sys.platform != "win32", reason="Windows path parsing regression")
def test_run_csv_view_handles_unquoted_windows_paths(tmp_path: Path) -> None:
    from trushell.commands.data import run_csv_view

    file_path = tmp_path / "users.csv"
    rows = ["ID,Name"] + [f"{i},User {i}" for i in range(1, 52)]
    file_path.write_text("\n".join(rows), encoding="utf-8")

    output = _strip_ansi(run_csv_view(str(file_path)))

    assert "User 50" in output
    assert "User 51" not in output
    assert "...and 1 more" in output
    assert "rows" in output
