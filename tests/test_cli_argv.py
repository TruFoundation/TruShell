from __future__ import annotations

from trushell import cli


def test_app_with_lower_does_not_mutate_original_argv(monkeypatch):
    original = ["trushell", "HeLp"]
    monkeypatch.setattr(cli.sys, "argv", original)

    calls: list[str] = []

    class FakeKernel:
        def execute_command(self, raw: str) -> None:
            calls.append(raw)

    monkeypatch.setattr(cli, "get_kernel", lambda: FakeKernel())

    cli.app_with_lower()

    assert cli.sys.argv == original
    assert calls == ["help"]
