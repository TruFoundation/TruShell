import os
import msvcrt
import typer
from pathlib import Path

from chronoterm.state import StateStore


COMMANDS = [
    "joke",
    "joke_trex",
    "addtask",
    "deletetask",
    "updatetask",
    "completetask",
    "showtasks",
    "now",
    "time",
    "world",
    "tz",
    "alarm",
    "sw",
]

TIME_TEMPLATES = [
    ("lcd", "LCD Display"),
    ("wrist_watch", "Wrist Watch"),
    ("desktop", "Desktop Clock"),
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


def _clear_screen() -> None:
    os.system("cls")


def _select_from_menu(title: str, options: list[str]) -> str | None:
    index = 0

    while True:
        _clear_screen()
        typer.secho(f"? {title}", fg=typer.colors.CYAN)
        typer.secho("  Use arrow keys. Press Enter to select. Press Esc to go back.", fg=typer.colors.BRIGHT_BLACK)
        typer.echo("")

        for current_index, option in enumerate(options):
            prefix = ">" if current_index == index else " "
            color = typer.colors.GREEN if current_index == index else typer.colors.WHITE
            typer.secho(f"{prefix} {option}", fg=color)

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            arrow = msvcrt.getwch()
            if arrow == "H":
                index = (index - 1) % len(options)
            elif arrow == "P":
                index = (index + 1) % len(options)
        elif key == "\r":
            return options[index]
        elif key == "\x1b":
            return None


def _available_sound_files() -> list[str]:
    sounds_dir = Path(__file__).resolve().parent / "chronoterm" / "sounds"
    if not sounds_dir.exists():
        return []
    return sorted(path.name for path in sounds_dir.iterdir() if path.is_file())


def _command_settings(command_name: str) -> None:
    store = StateStore()
    state = store.load()

    if command_name == "time":
        selected_label = _select_from_menu(
            "Select a template for the time command:",
            [label for _, label in TIME_TEMPLATES],
        )
        if selected_label is None:
            typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
            return

        template_lookup = {label: key for key, label in TIME_TEMPLATES}
        state.time_template = template_lookup[selected_label]
        store.save(state)
        typer.secho(f"Time template updated to {selected_label}.", fg=typer.colors.GREEN)
        return

    if command_name == "joke":
        selected_setting = _select_from_menu(
            "Select a joke setting to edit:",
            ["Character", "Sound"],
        )
        if selected_setting is None:
            typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
            return

        if selected_setting == "Character":
            selected_character = _select_from_menu(
                "Select a character for the joke command:",
                JOKE_CHARACTERS,
            )
            if selected_character is None:
                typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
                return

            state.joke_character = selected_character
            store.save(state)
            typer.secho(f"Joke character updated to {selected_character}.", fg=typer.colors.GREEN)
            return

        sound_files = _available_sound_files()
        if not sound_files:
            typer.secho("No sound files were found in chronoterm/sounds.", fg=typer.colors.RED)
            return

        selected_sound = _select_from_menu(
            "Select a sound for the joke command:",
            sound_files,
        )
        if selected_sound is None:
            typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)
            return

        state.joke_sound = selected_sound
        store.save(state)
        typer.secho(f"Joke sound updated to {selected_sound}.", fg=typer.colors.GREEN)
        return

    typer.secho(f"No editable settings are available yet for '{command_name}'.", fg=typer.colors.YELLOW)


def launch_settings() -> None:
    selected_command = _select_from_menu("Select a command to configure:", COMMANDS)
    _clear_screen()

    if selected_command is None:
        typer.secho("Settings closed.", fg=typer.colors.YELLOW)
        return

    _command_settings(selected_command)
