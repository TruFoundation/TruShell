from __future__ import annotations

from types import SimpleNamespace

from trushell.commands.core import run_help
from trushell.cli import _handle_local_command


def test_run_help_prints_docstring_for_known_command(monkeypatch, capsys):
    import importlib

    fake_kernel = SimpleNamespace(
        registry={
            "settings": {
                "path": "trushell/commands/settings.py",
                "function": "run_settings",
            }
        },
        _import_module=lambda _path: importlib.import_module("trushell.commands.settings"),
    )

    # Provide a minimal module object with the expected function and
    # docstring so `run_help()` can import and print the docstring.
    def run_settings():
        """Launch the TruShell settings TUI."""
        return None

    fake_module = SimpleNamespace(run_settings=run_settings)
    fake_kernel._import_module = lambda path: fake_module

    monkeypatch.setattr("trushell.core.trukernel.get_kernel", lambda: fake_kernel)

    run_help("settings")

    out = capsys.readouterr().out
    assert "Launch the TruShell settings TUI." in out


def test_run_help_lists_all_registry_commands(monkeypatch, capsys):
    fake_kernel = SimpleNamespace(
        registry={
            "help": {"path": "trushell/commands/core.py", "function": "run_help"},
            "task": {"path": "trushell/commands/tasks.py", "function": "run_task_command"},
            "gstatus": {"path": "trushell/plugins/git_enhancer/main.py", "function": "plugin_init"},
        },
        _import_module=None,
    )

    monkeypatch.setattr("trushell.core.trukernel.get_kernel", lambda: fake_kernel)

    run_help("")

    out = capsys.readouterr().out
    assert "gstatus" in out, "plugin-registered commands must appear in help output"
    assert "task" in out
    assert "help" in out


def test_handle_local_command_does_not_intercept_help():
    """help must reach the kernel's run_help(), not a hardcoded CLI handler."""
    result = _handle_local_command("help", "")
    assert result == "unhandled"
