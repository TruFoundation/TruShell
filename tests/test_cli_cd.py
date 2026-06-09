from __future__ import annotations

from pathlib import Path

from trushell import cli


def test_handle_cd_command_changes_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "dir"
    target.mkdir()

    called = False

    def fake_run_external_command(command: str, shell: bool = True, check: bool = False, cwd: str | None = None):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(cli, "_run_external_command", fake_run_external_command)

    result = cli._handle_cd_command("cd dir")

    assert result is True
    assert Path.cwd() == target
    assert not called
    assert str(target) in capsys.readouterr().out


def test_handle_cd_command_expands_environment_variables(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "env-target"
    target.mkdir()
    monkeypatch.setenv("TRUSHELL_CD_TARGET", str(target))

    result = cli._handle_cd_command("cd $TRUSHELL_CD_TARGET")

    assert result is True
    assert Path.cwd() == target
    assert str(target) in capsys.readouterr().out


def test_handle_cd_command_strips_trailing_whitespace(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "space-target"
    target.mkdir()
    monkeypatch.setenv("TRUSHELL_CD_TARGET", str(target))

    result = cli._handle_cd_command("cd $TRUSHELL_CD_TARGET   ")

    assert result is True
    assert Path.cwd() == target
    assert str(target) in capsys.readouterr().out
