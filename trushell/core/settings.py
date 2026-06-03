from __future__ import annotations

from pathlib import Path
from typing import Sequence

import typer

from trushell.state import StateStore

COMMANDS = ["time", "world", "joke"]
TIME_TEMPLATES = [
    ("lcd", "LCD Display"),
    ("wrist_watch", "Wrist Watch"),
    ("desktop", "Desktop Clock"),
]
CLOCK_FORMATS = [
    ("24h", "24 Hour (Military)"),
    ("12h", "12 Hour (AM/PM)"),
]
JOKE_CHARACTERS = [
    "cow",
    "trex",
    "dragon",
    "tux",
    "kitty",
    "turkey",
    "stegosaurus",
    "ghostbusters",
    "pig",
    "daemon",
]


def _select_option(prompt: str, options: Sequence[str]) -> str | None:
    typer.echo("")
    typer.echo(prompt)
    for index, option in enumerate(options, start=1):
        typer.echo(f"  {index}. {option}")

    selection = typer.prompt("Choose an option (or leave blank to cancel)").strip()
    if not selection:
        return None

    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(options):
            return options[index]

    if selection in options:
        return selection

    typer.secho("Invalid selection.", fg=typer.colors.RED)
    return None


def _available_sound_files() -> list[str]:
    sounds_dir = Path(__file__).resolve().parents[1] / "sounds"
    if not sounds_dir.exists():
        return []
    return sorted([path.name for path in sounds_dir.iterdir() if path.is_file()])


def _edit_time_template() -> None:
    target = _select_option("Select a template for the time command:", [label for _, label in TIME_TEMPLATES])
    if target is None:
        typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
        return

    selected = next((key for key, label in TIME_TEMPLATES if label == target), None)
    if selected is None:
        typer.secho("Template not found.", fg=typer.colors.RED)
        return

    state = StateStore().load()
    state.time_template = selected
    StateStore().save(state)
    typer.secho(f"Time template updated to {target}.", fg=typer.colors.GREEN)


def _edit_clock_format() -> None:
    target = _select_option("Select a clock format for the time command:", [label for _, label in CLOCK_FORMATS])
    if target is None:
        typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
        return

    selected = next((key for key, label in CLOCK_FORMATS if label == target), None)
    if selected is None:
        typer.secho("Clock format not found.", fg=typer.colors.RED)
        return

    state = StateStore().load()
    state.clock_format = selected
    StateStore().save(state)
    typer.secho(f"Clock format updated to {target}.", fg=typer.colors.GREEN)


def _edit_joke_character() -> None:
    target = _select_option("Select a character for jokes:", JOKE_CHARACTERS)
    if target is None:
        typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
        return

    state = StateStore().load()
    state.joke_character = target
    StateStore().save(state)
    typer.secho(f"Joke character updated to {target}.", fg=typer.colors.GREEN)


def _edit_joke_sound() -> None:
    sound_files = _available_sound_files()
    if not sound_files:
        typer.secho("No sounds found.", fg=typer.colors.RED)
        return

    target = _select_option("Select a sound for jokes:", sound_files)
    if target is None:
        typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
        return

    state = StateStore().load()
    state.joke_sound = target
    StateStore().save(state)
    typer.secho(f"Joke sound updated to {target}.", fg=typer.colors.GREEN)


def launch_settings() -> None:
    command = _select_option("Select a command to configure:", COMMANDS)
    if command is None:
        typer.secho("Settings closed.", fg=typer.colors.YELLOW)
        return

    if command == "time":
        _edit_time_template()
    elif command == "world":
        _edit_clock_format()
    elif command == "joke":
        option = _select_option("Select a joke setting to change:", ["Character", "Sound"])
        if option == "Character":
            _edit_joke_character()
        elif option == "Sound":
            _edit_joke_sound()
        else:
            typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
    else:
        typer.secho(f"No editable settings available for '{command}'.", fg=typer.colors.YELLOW)
