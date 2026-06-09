from __future__ import annotations

from typing import Any


def test_update_task_changes_text_single_word(monkeypatch) -> None:
    """Existing parser handles single-word task updates correctly."""
    from trushell.commands.tasks import update_task

    captured: dict[str, Any] = {}

    def fake_update_todo(index: int, task: str | None, category: str | None) -> None:
        captured["index"] = index
        captured["task"] = task
        captured["category"] = category

    monkeypatch.setattr("trushell.commands.tasks.update_todo", fake_update_todo)

    update_task("1 NewTask")

    assert captured["index"] == 0
    assert captured["task"] == "NewTask"
    assert captured["category"] is None


def test_update_task_multiword_known_bug(monkeypatch) -> None:
    """Pin the current (known) parsing bug for quoted multi-word values.

    The current implementation splits with `maxsplit=2` and then strips
    surrounding quotes from individual parts. This results in
    `updatetask 1 "New text"` producing `task == "New"` and
    `category == "text"`. The behaviour is preserved here so the
    regression is detected if/fwhen the parsing is fixed.
    """
    from trushell.commands.tasks import update_task

    captured: dict[str, Any] = {}

    def fake_update_todo(index: int, task: str | None, category: str | None) -> None:
        captured["index"] = index
        captured["task"] = task
        captured["category"] = category

    monkeypatch.setattr("trushell.commands.tasks.update_todo", fake_update_todo)

    update_task('1 "New text"')

    assert captured["index"] == 0
    # The current broken behaviour yields only the first word as the task
    assert captured["task"] == "New"
    # and treats the remainder as the category
    assert captured["category"] == "text"
