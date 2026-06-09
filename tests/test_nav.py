from __future__ import annotations

import sys
from pathlib import Path

import pytest
from trushell.commands.nav import run_jump


def test_run_jump_no_matches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_jump("missing")
    assert "No directories found matching" in result
    assert "missing" in result


def test_run_jump_single_match(tmp_path, monkeypatch):
    target = tmp_path / "src"
    target.mkdir()
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)

    result = run_jump("src")
    assert result == f"__TRUSHELL_CD__: {target}"


@pytest.mark.skipif(sys.platform == "win32", reason="Windows backslash escaping in Rich table output breaks path assertion")
def test_run_jump_multiple_matches(tmp_path, monkeypatch):
    first = tmp_path / "src"
    first.mkdir()
    second = tmp_path / "my_src"
    second.mkdir()
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)

    result = run_jump("src")
    assert "Multiple matches found. Please be more specific." in result
    assert str(first) in result
    assert str(second) in result


def test_run_jump_ignores_hidden_directories(tmp_path, monkeypatch):
    (tmp_path / ".hidden_dir").mkdir()
    visible = tmp_path / "src"
    visible.mkdir()
    monkeypatch.chdir(tmp_path)

    result = run_jump("src")
    assert result == f"__TRUSHELL_CD__: {visible}"
