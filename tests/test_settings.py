from __future__ import annotations

import json
from pathlib import Path

from trushell.commands.settings import SettingsApp, run_settings
from trushell.core.settings import SettingsManager


def test_settings_manager_loads_defaults_and_saves(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    manager = SettingsManager()
    settings = manager.load()

    assert settings["theme"] == "dark"
    assert settings["prompt_symbol"] == "➜"
    assert settings["show_git_status"] is True
    assert settings["auto_complete"] is True
    assert settings["csv_max_rows"] == 50

    assert manager.config_path.exists()

    loaded = json.loads(manager.config_path.read_text(encoding="utf-8"))
    assert loaded["theme"] == "dark"

    manager.set("theme", "monokai")
    manager.save()

    reloaded = SettingsManager(manager.config_path).load()
    assert reloaded["theme"] == "monokai"


def test_run_settings_launches_textual_app(monkeypatch):
    called: dict[str, bool] = {"ran": False}

    def fake_run(self, *args, **kwargs):
        called["ran"] = True

    monkeypatch.setattr(SettingsApp, "run", fake_run)
    run_settings("")

    assert called["ran"] is True

def test_switching_categories_retains_dirty_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    app = SettingsApp()
    app._update_dirty_setting("theme", "light")
    app.selected_category = "Data"
    assert "theme" in app.dirty_settings
    assert app.dirty_settings["theme"] == "light"