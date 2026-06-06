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

    monkeypatch.setattr("trushell.core.trukernel.get_kernel", lambda: fake_kernel)

    run_help("settings")

    out = capsys.readouterr().out
    assert "Launch the TruShell settings TUI." in out
