from __future__ import annotations

import os
import subprocess

from trushell import cli


def test_os_fallback_runs_argument_vector_without_shell(monkeypatch):
    calls = {}

    def fake_run(command, shell, check, cwd):
        calls.update(
            command=command,
            shell=shell,
            check=check,
            cwd=cwd,
        )
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(cli, "_run_external_command", fake_run)

    assert cli._handle_os_fallback('echo "hello world"') is True
    assert calls == {
        "command": ["echo", "hello world"],
        "shell": False,
        "check": False,
        "cwd": os.getcwd(),
    }


def test_os_fallback_does_not_interpret_shell_metacharacters(monkeypatch):
    calls = {}

    def fake_run(command, shell, check, cwd):
        calls.update(command=command, shell=shell)
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(cli, "_run_external_command", fake_run)

    assert cli._handle_os_fallback("echo safe; touch injected") is True
    assert calls == {
        "command": ["echo", "safe;", "touch", "injected"],
        "shell": False,
    }


def test_os_fallback_handles_malformed_quoting(monkeypatch, capsys):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("external command should not run")

    monkeypatch.setattr(cli, "_run_external_command", fail_if_called)

    assert cli._handle_os_fallback('echo "unterminated') is True
    assert "OS fallback error" in capsys.readouterr().out
