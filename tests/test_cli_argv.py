from __future__ import annotations

from trushell import cli


def test_app_with_lower_does_not_mutate_original_argv(monkeypatch):

    # NOTE: `trushell.cli.app_with_lower()` references a module-level
    # name `argv` that is not defined in the module. Tests exercising the
    # early-return paths must inject this name into the module namespace
    # (this mirrors how callers may set it in other environments).
    original = ["trushell", "HeLp"]
    monkeypatch.setattr(cli.sys, "argv", original)
    # Inject a module-level `argv` name for the duration of the test so
    # `app_with_lower()` can compare against the real `sys.argv`.
    monkeypatch.setattr(cli, "argv", cli.sys.argv, raising=False)

    calls: list[str] = []

    class FakeKernel:
        def execute_command(self, raw: str) -> None:
            calls.append(raw)

    monkeypatch.setattr(cli, "get_kernel", lambda: FakeKernel())

    cli.app_with_lower()

    assert cli.sys.argv == original
    assert calls == ["help"]
