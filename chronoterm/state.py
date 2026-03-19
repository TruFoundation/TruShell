from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def _app_state_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "ChronoTerm"
    return Path.home() / ".chronoterm"


def default_state_path() -> Path:
    return _app_state_dir() / "state.json"


def _atomic_write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


@dataclass
class AppState:
    timezones: list[str] = field(default_factory=list)
    alarms: list[dict[str, Any]] = field(default_factory=list)
    time_template: str = "lcd"
    clock_format: str = "24h"
    joke_character: str = "cow"
    joke_sound: str = "cow-sound.mp3"
    version: int = 1
    updated_at_iso: str | None = None

    def touch(self) -> None:
        self.updated_at_iso = datetime.now().astimezone().isoformat(timespec="seconds")


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_state_path()

    def _new_state(self) -> AppState:
        return AppState()

    def _apply_dict(self, data: dict[str, Any]) -> AppState:
        state = self._new_state()
        tzs = data.get("timezones")
        alarms = data.get("alarms")
        time_template = data.get("time_template")
        clock_format = data.get("clock_format")
        joke_character = data.get("joke_character")
        joke_sound = data.get("joke_sound")
        version = data.get("version")
        updated_at_iso = data.get("updated_at_iso")

        if isinstance(tzs, list) and all(isinstance(x, str) for x in tzs):
            state.timezones = tzs
        if isinstance(alarms, list) and all(isinstance(x, dict) for x in alarms):
            state.alarms = alarms
        if isinstance(time_template, str):
            state.time_template = time_template
        if isinstance(clock_format, str):
            state.clock_format = clock_format
        if isinstance(joke_character, str):
            state.joke_character = joke_character
        if isinstance(joke_sound, str):
            state.joke_sound = joke_sound
        if isinstance(version, int):
            state.version = version
        if isinstance(updated_at_iso, str) or updated_at_iso is None:
            state.updated_at_iso = updated_at_iso
        return state

    def _payload(self, state: AppState) -> dict[str, Any]:
        return {
            "version": state.version,
            "updated_at_iso": state.updated_at_iso,
            "timezones": state.timezones,
            "alarms": state.alarms,
            "time_template": state.time_template,
            "clock_format": state.clock_format,
            "joke_character": state.joke_character,
            "joke_sound": state.joke_sound,
        }

    def load(self) -> AppState:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self._new_state()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return self._new_state()

        if not isinstance(data, dict):
            return self._new_state()
        return self._apply_dict(data)

    def save(self, state: AppState) -> None:
        state.touch()
        payload = self._payload(state)
        _atomic_write_text(self.path, json.dumps(payload, indent=2, ensure_ascii=False))

