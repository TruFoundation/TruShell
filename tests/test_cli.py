import os
import subprocess
from types import SimpleNamespace

from typer.testing import CliRunner

from trushell.cli import app
from trushell.project import (
    TruShellEditor,
    _handle_cd_command,
    _handle_edit_command,
    _handle_local_command,
    _handle_os_fallback,
    _prompt_command,
    _run_external_command,
    _split_command,
    is_dangerous_command,
    parse_and_execute_command,
)


runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_help_shows_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_unknown_command_uses_os_fallback(monkeypatch) -> None:
    calls = {}

    def fake_run(command: list[str], shell: bool, check: bool, cwd: str) -> subprocess.CompletedProcess[str]:
        calls["command"] = command
        calls["shell"] = shell
        calls["check"] = check
        calls["cwd"] = cwd
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr("trushell.project._run_external_command", fake_run)

    assert _handle_os_fallback("pwd") is True
    assert calls == {
        "command": ["pwd"],
        "shell": False,
        "check": False,
        "cwd": os.getcwd(),
    }


def test_is_dangerous_command_blocks_shell_meta() -> None:
    assert is_dangerous_command("ls | grep foo") is True
    assert is_dangerous_command("echo $HOME") is True
    assert is_dangerous_command("rm file; echo hi") is True
    assert is_dangerous_command("echo hello") is False
    assert is_dangerous_command('echo "hello world"') is False


def test_handle_local_command_prioritizes_todo(monkeypatch) -> None:
    calls = {}

    def fake_addtask(task: str, category: str) -> None:
        calls["task"] = task
        calls["category"] = category

    monkeypatch.setattr("trushell.project.addtask", fake_addtask)

    command, arguments = _split_command('addtask "Review PR" "Work"')
    result = _handle_local_command(command, arguments)

    assert result == "handled"
    assert calls == {"task": "Review PR", "category": "Work"}


def test_handle_local_command_addtask_escaped_quotes(monkeypatch) -> None:
    calls = {}

    def fake_addtask(task: str, category: str) -> None:
        calls["task"] = task
        calls["category"] = category

    monkeypatch.setattr("trushell.project.addtask", fake_addtask)

    command, arguments = _split_command(
        'addtask "Finish report with \\"quotes\\" inside" "Work"'
    )
    result = _handle_local_command(command, arguments)

    assert result == "handled"
    assert calls == {
        "task": 'Finish report with "quotes" inside',
        "category": "Work",
    }


def test_split_command_returns_empty_on_unclosed_quotes() -> None:
    command, arguments = _split_command('addtask "Unclosed quote')

    assert command == ""
    assert arguments == []


def test_prompt_command_warns_on_multiline_input(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr("builtins.input", lambda prompt: "echo hi\nls")
    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: messages.append((message, fg)),
    )

    raw, command, arguments = _prompt_command()

    assert raw == ""
    assert command == ""
    assert arguments == []
    assert messages and "Please enter commands one at a time" in messages[0][0]


def test_prompt_command_warns_on_invalid_syntax(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr("builtins.input", lambda prompt: 'addtask "Unclosed quote')
    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: messages.append((message, fg)),
    )

    raw, command, arguments = _prompt_command()

    assert raw == ""
    assert command == ""
    assert arguments == []
    assert messages and "Invalid syntax" in messages[0][0]


def test_parse_and_execute_command_handles_unclosed_quotes(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: messages.append((message, fg)),
    )

    assert parse_and_execute_command('addtask "Unclosed quote') is True
    assert messages and "Invalid syntax" in messages[0][0]


def test_parse_and_execute_command_runs_simple_external(monkeypatch) -> None:
    calls = {}

    def fake_run(command: list[str], shell: bool, check: bool, cwd: str) -> subprocess.CompletedProcess[str]:
        calls["command"] = command
        calls["shell"] = shell
        calls["check"] = check
        calls["cwd"] = cwd
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr("trushell.project._run_external_command", fake_run)

    assert parse_and_execute_command("echo hi") is True
    assert calls == {
        "command": ["echo", "hi"],
        "shell": False,
        "check": False,
        "cwd": os.getcwd(),
    }


def test_run_external_command_profiles_resources(monkeypatch) -> None:
    calls = {}
    stats = []

    class FakePopen:
        def __init__(self, command: str, shell: bool, cwd: str | None = None) -> None:
            calls["command"] = command
            calls["shell"] = shell
            calls["cwd"] = cwd
            self.pid = 123
            self.returncode = None
            self._first = True

        def wait(self, timeout: float | None = None) -> int:
            if self._first:
                self._first = False
                raise subprocess.TimeoutExpired(cmd="echo hi", timeout=timeout)
            self.returncode = 5
            return 5

    class FakeProcess:
        def __init__(self, pid: int) -> None:
            self.pid = pid
            self._count = 0

        def cpu_percent(self, interval=None) -> float:
            self._count += 1
            return 8.2 if self._count > 1 else 0.0

        def memory_info(self):
            return SimpleNamespace(rss=45 * 1024 * 1024)

    monkeypatch.setattr("trushell.project.subprocess.Popen", FakePopen)
    monkeypatch.setattr("trushell.project.psutil.Process", FakeProcess)
    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: stats.append((message, fg)),
    )

    result = _run_external_command("echo hi", shell=True, check=False, cwd="/tmp")

    assert result.returncode == 5
    assert calls == {"command": "echo hi", "shell": True, "cwd": "/tmp"}
    assert stats and "CPU peak" in stats[0][0] and "RAM peak" in stats[0][0]


def test_cd_command_changes_directory_and_runs_ls(monkeypatch) -> None:
    calls = {}

    def fake_chdir(path: str) -> None:
        calls["chdir"] = path

    def fake_run(command: list[str], shell: bool, check: bool, cwd: str) -> SimpleNamespace:
        calls["ls_command"] = command
        calls["ls_shell"] = shell
        calls["ls_check"] = check
        calls["ls_cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("trushell.project.os.chdir", fake_chdir)
    monkeypatch.setattr("trushell.project._run_external_command", fake_run)

    command, arguments = _split_command("cd /tmp")
    assert _handle_cd_command(command, arguments) is True
    assert calls == {
        "chdir": "/tmp",
        "ls_command": ["ls"],
        "ls_shell": False,
        "ls_check": False,
        "ls_cwd": os.getcwd(),
    }


def test_cd_without_target_prints_syntax_hint(monkeypatch) -> None:
    calls = {}

    def fake_chdir(path: str) -> None:
        calls["chdir"] = path

    def fake_run(command: str, shell: bool, check: bool, cwd: str) -> SimpleNamespace:
        calls["ls_command"] = command
        calls["ls_cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("trushell.project.os.path.expanduser", lambda path: "/home/test")
    monkeypatch.setattr("trushell.project.os.chdir", fake_chdir)
    monkeypatch.setattr("trushell.project.subprocess.run", fake_run)

    command, arguments = _split_command("cd")
    assert _handle_cd_command(command, arguments) is True
    assert calls == {}


def test_addtask_missing_arguments_is_blocked(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: messages.append((message, fg)),
    )

    command, arguments = _split_command("addtask")
    assert _handle_local_command(command, arguments) == "handled"


def test_edit_requires_filename(monkeypatch) -> None:
    messages = []

    monkeypatch.setattr(
        "trushell.project.typer.secho",
        lambda message, fg=None: messages.append((message, fg)),
    )

    command, arguments = _split_command("edit")
    assert _handle_edit_command(command, arguments) is True
    assert messages and "Syntax: edit <filename>" in messages[0][0]


def test_edit_launches_editor_for_existing_file(monkeypatch, tmp_path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    calls = {}

    class FakeEditor:
        def __init__(self, filename: str, initial_text: str) -> None:
            calls["filename"] = filename
            calls["initial_text"] = initial_text

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr("trushell.project.TruShellEditor", FakeEditor)

    command, arguments = _split_command(f"edit {file_path}")
    assert _handle_edit_command(command, arguments) is True
    assert calls == {"filename": str(file_path), "initial_text": "hello", "ran": True}


def test_trushell_editor_uses_initial_text_without_re_reading_file(tmp_path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_text("from-disk", encoding="utf-8")

    editor = TruShellEditor(str(file_path), initial_text="from-arg")

    assert editor.file_content == "from-arg"


def test_action_save_file_notifies_on_permission_error(monkeypatch, tmp_path) -> None:
    file_path = tmp_path / "readonly.txt"
    editor = TruShellEditor(str(file_path), initial_text="draft")

    notifications = []

    class FakeTextArea:
        text = "draft"

    monkeypatch.setattr(editor, "query_one", lambda *_args, **_kwargs: FakeTextArea())
    monkeypatch.setattr(editor, "notify", lambda message, severity=None: notifications.append((message, severity)))

    def fail_open(*_args, **_kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr("builtins.open", fail_open)

    editor.action_save_file()

    assert notifications and "Failed to save file" in notifications[0][0]
