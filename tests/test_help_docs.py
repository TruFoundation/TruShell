from __future__ import annotations

from types import SimpleNamespace

from trushell.commands.core import run_help


def test_run_help_prints_docstring_for_known_command(monkeypatch, capsys):
    fake_kernel = SimpleNamespace(
        registry={
            "settings": {
                "path": "trushell/commands/settings.py",
                "function": "run_settings",
            }
        }
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
