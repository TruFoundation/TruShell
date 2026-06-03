from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from trushell import project
from trushell.chronoterm.state import StateStore


def test_frecency_score() -> None:
    now = 1_700_000_000.0
    assert project._frecency_score(10, now, now=now) == 10.0
    decayed = project._frecency_score(10, now - 86400.0, now=now)
    assert decayed == pytest.approx(10 * 0.95, rel=1e-6)


def test_add_z_path_updates_state(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))

    directory = tmp_path / "home"
    directory.mkdir()
    project._add_z_path(str(directory))

    state = project._load_z_state()
    normalized = project._normalize_directory(str(directory))
    assert normalized in state.z_dirs
    assert state.z_dirs[normalized]["count"] == 1

    project._add_z_path(str(directory))
    state = project._load_z_state()
    assert state.z_dirs[normalized]["count"] == 2


def test_handle_z_command_add_option(tmp_path: Path, monkeypatch, capsys) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))

    directory = tmp_path / "projects"
    directory.mkdir()

    assert project._handle_z_command("z", ["--add", str(directory)]) is True
    captured = capsys.readouterr()
    assert "Added:" in captured.out

    state = project._load_z_state()
    normalized = project._normalize_directory(str(directory))
    assert normalized in state.z_dirs
    assert state.z_dirs[normalized]["count"] == 1


def test_find_z_matches_prefers_higher_frecency(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))

    path_one = tmp_path / "one"
    path_two = tmp_path / "two"
    path_one.mkdir()
    path_two.mkdir()

    state = project._load_z_state()
    now = time.time()
    state.z_dirs = {
        project._normalize_directory(str(path_one)): {
            "count": 1,
            "last_accessed": now,
        },
        project._normalize_directory(str(path_two)): {
            "count": 10,
            "last_accessed": now - 86400.0 * 10,
        },
    }
    project._save_z_state(state)

    matches = project._find_z_matches("two", current_only=False, recency_only=False)
    assert matches[0][0] == project._normalize_directory(str(path_two))

    recent_matches = project._find_z_matches("two", current_only=False, recency_only=True)
    assert recent_matches[0][0] == project._normalize_directory(str(path_two))


def test_find_z_matches_ignores_missing_directories(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))

    existing_path = tmp_path / "exists"
    existing_path.mkdir()
    missing_path = tmp_path / "missing"

    state = project._load_z_state()
    state.z_dirs = {
        project._normalize_directory(str(existing_path)): {"count": 1, "last_accessed": time.time()},
        project._normalize_directory(str(missing_path)): {"count": 10, "last_accessed": time.time()},
    }
    project._save_z_state(state)

    matches = project._find_z_matches(None, current_only=False, recency_only=False)
    assert len(matches) == 1
    assert matches[0][0] == project._normalize_directory(str(existing_path))


def test_cd_command_adds_path_to_z_history(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))
    project._PREVIOUS_CWD = None

    target = tmp_path / "directory"
    target.mkdir()

    monkeypatch.setattr(project.os, "chdir", lambda path: None)
    monkeypatch.setattr(project.os, "getcwd", lambda: str(target))
    monkeypatch.setattr(project, "_run_external_command", lambda command, shell, check, cwd=None: SimpleNamespace(returncode=0))

    command, arguments = project._split_command(f"cd {target}")
    assert project._handle_cd_command(command, arguments) is True

    state = project._load_z_state()
    normalized = project._normalize_directory(str(target))
    assert normalized in state.z_dirs
    assert state.z_dirs[normalized]["count"] == 1


def test_mkdir_command_creates_directories(tmp_path: Path) -> None:
    target_a = tmp_path / "test_a"
    target_b = tmp_path / "test_b"

    command, arguments = project._split_command(f"mkdir -p {target_a} {target_b}")
    assert project._handle_mkdir_command(command, arguments) is True

    assert target_a.exists() and target_a.is_dir()
    assert target_b.exists() and target_b.is_dir()


def test_cd_command_revisits_existing_path_and_increments_count(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))
    project._PREVIOUS_CWD = None

    target = tmp_path / "directory"
    target.mkdir()

    monkeypatch.setattr(project.os, "chdir", lambda path: None)
    monkeypatch.setattr(project.os, "getcwd", lambda: str(target))
    monkeypatch.setattr(project, "_run_external_command", lambda command, shell, check, cwd=None: SimpleNamespace(returncode=0))

    command, arguments = project._split_command(f"cd {target}")
    assert project._handle_cd_command(command, arguments) is True
    assert project._handle_cd_command(command, arguments) is True

    state = project._load_z_state()
    normalized = project._normalize_directory(str(target))
    assert state.z_dirs[normalized]["count"] == 2


def test_cd_dash_switches_to_previous_directory(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))
    project._PREVIOUS_CWD = None

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    cwd_state = {"cwd": str(first_dir)}

    def fake_chdir(path: str) -> None:
        cwd_state["cwd"] = str(project._normalize_directory(path))

    monkeypatch.setattr(project.os, "chdir", fake_chdir)
    monkeypatch.setattr(project.os, "getcwd", lambda: cwd_state["cwd"])
    monkeypatch.setattr(project, "_run_external_command", lambda command, shell, check, cwd=None: SimpleNamespace(returncode=0))

    command, arguments = project._split_command(f"cd {second_dir}")
    assert project._handle_cd_command(command, arguments) is True
    command, arguments = project._split_command("cd -")
    assert project._handle_cd_command(command, arguments) is True
    assert cwd_state["cwd"] == project._normalize_directory(str(first_dir))


def test_z_command_updates_current_directory_and_supports_bang_pwd(tmp_path: Path, monkeypatch) -> None:
    history_path = tmp_path / "state.json"
    monkeypatch.setattr(project, "_Z_STATE_STORE", StateStore(path=history_path))

    target = tmp_path / "target"
    target.mkdir()

    # Add target to z history so z can match it.
    project._add_z_path(str(target))

    cwd_state = {"cwd": str(project._normalize_directory(target))}

    def fake_chdir(path: str) -> None:
        cwd_state["cwd"] = project._normalize_directory(path)

    monkeypatch.setattr(project.os, "chdir", fake_chdir)
    monkeypatch.setattr(project.os, "getcwd", lambda: cwd_state["cwd"])

    executed = {}
    def fake_run(command, shell, check, cwd=None):
        executed["command"] = command
        executed["shell"] = shell
        executed["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(project, "_run_external_command", fake_run)

    command, arguments = project._split_command("z target")
    assert project._handle_z_command(command, arguments) is True
    assert project._CURRENT_DIR == project._normalize_directory(str(target))

    assert project.parse_and_execute_command("!pwd") is True
    assert executed["command"] == "pwd"
    assert executed["shell"] is True
    assert executed["cwd"] == project._CURRENT_DIR
