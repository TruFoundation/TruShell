from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import typer
from platformdirs import user_config_dir


def default_state_path() -> Path:
    return Path(user_config_dir("TruShell", "AkshajSinghal")) / "state.json"


@dataclass
class AppState:
    timezones: list[str] | None = None
    alarms: list[dict] | None = None
    time_template: str = "lcd"
    clock_format: str = "24h"
    joke_character: str = "cow"
    joke_sound: str = "cow-sound.mp3"
    version: int = 1
    updated_at_iso: str | None = None

    def __post_init__(self) -> None:
        if self.timezones is None:
            self.timezones = []
        if self.alarms is None:
            self.alarms = []

    def touch(self) -> None:
        self.updated_at_iso = datetime.now().astimezone().isoformat(timespec="seconds")


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_state_path()

    def _new_state(self) -> AppState:
        return AppState()

    def load(self) -> AppState:
        state = self._new_state()
        try:
            with open(self.path, "r", encoding="utf-8") as state_file:
                file_data = json.load(state_file)
            state.timezones = file_data.get("timezones", [])
            state.alarms = file_data.get("alarms", [])
            state.time_template = file_data.get("time_template", "lcd")
            state.clock_format = file_data.get("clock_format", "24h")
            state.joke_character = file_data.get("joke_character", "cow")
            state.joke_sound = file_data.get("joke_sound", "cow-sound.mp3")
            state.version = file_data.get("version", 1)
            state.updated_at_iso = file_data.get("updated_at_iso")
        except FileNotFoundError:
            return state
        except Exception:
            typer.secho("Unable to load application state. Using defaults.", fg=typer.colors.YELLOW)
            return state
        return state

    def save(self, state: AppState) -> None:
        state.touch()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as state_file:
            json.dump(
                {
                    "timezones": state.timezones,
                    "alarms": state.alarms,
                    "time_template": state.time_template,
                    "clock_format": state.clock_format,
                    "joke_character": state.joke_character,
                    "joke_sound": state.joke_sound,
                    "version": state.version,
                    "updated_at_iso": state.updated_at_iso,
                },
                state_file,
                indent=2,
                ensure_ascii=False,
            )
