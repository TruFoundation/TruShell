import os
import msvcrt
import typer
from pathlib import Path

from chronoterm.state import StateStore


COMMANDS = [
    "joke",
    "addtask",
    "tasks",
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


def _clear_screen() -> None:
    os.system("cls")


def _show_cancelled_message() -> None:
    typer.secho("Settings cancelled.", fg=typer.colors.YELLOW)


def _show_selection_screen(title: str, options: list[str], index: int) -> None:
    _clear_screen()
    typer.secho(f"? {title}", fg=typer.colors.CYAN)
    typer.secho("  Use arrow keys. Press Enter to select. Press Esc to go back.", fg=typer.colors.BRIGHT_BLACK)
    typer.echo("")

    current_index = 0
    while current_index < len(options):
        option = options[current_index]
        prefix = ">" if current_index == index else " "
        color = typer.colors.GREEN if current_index == index else typer.colors.WHITE
        typer.secho(f"{prefix} {option}", fg=color)
        current_index = current_index + 1


def _read_menu_key(index: int, total: int) -> tuple[int, bool, bool]:
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        arrow = msvcrt.getwch()
        if arrow == "H":
            index = (index - 1) % total
        elif arrow == "P":
            index = (index + 1) % total
        return index, False, False
    if key == "\r":
        return index, True, False
    if key == "\x1b":
        return index, False, True
    return index, False, False


def _select_from_menu(title: str, options: list[str]) -> str | None:
    index = 0

    while True:
        _show_selection_screen(title, options, index)
        index, did_submit, did_escape = _read_menu_key(index, len(options))
        if did_submit:
            return options[index]
        if did_escape:
            return None


def _available_sound_files() -> list[str]:
    sounds_dir = Path(__file__).resolve().parent / "chronoterm" / "sounds"
    if not sounds_dir.exists():
        return []
    return sorted(path.name for path in sounds_dir.iterdir() if path.is_file())


def _save_state(update_message: str, apply_change) -> None:
    store = StateStore()
    state = store.load()
    apply_change(state)
    store.save(state)
    typer.secho(update_message, fg=typer.colors.GREEN)


def _edit_time_settings() -> None:
    selected_setting = _select_from_menu(
        "Select a time setting to edit:",
        ["Template", "Clock Format"],
    )
    if selected_setting is None:
        _show_cancelled_message()
        return
    if selected_setting == "Template":
        labels = [label for _, label in TIME_TEMPLATES]
        selected_label = _select_from_menu("Select a template for the time command:", labels)
        if selected_label is None:
            _show_cancelled_message()
            return
        template_lookup = {label: key for key, label in TIME_TEMPLATES}
        _save_state(
            f"Time template updated to {selected_label}.",
            lambda state: setattr(state, "time_template", template_lookup[selected_label]),
        )
        return

    _edit_clock_format("time")


def _edit_clock_format(command_name: str) -> None:
    labels = [label for _, label in CLOCK_FORMATS]
    selected_label = _select_from_menu(f"Select a clock format for the {command_name} command:", labels)
    if selected_label is None:
        _show_cancelled_message()
        return
    format_lookup = {label: key for key, label in CLOCK_FORMATS}
    _save_state(
        f"Clock format updated to {selected_label}.",
        lambda state: setattr(state, "clock_format", format_lookup[selected_label]),
    )


def _edit_joke_character() -> None:
    selected_character = _select_from_menu("Select a character for the joke command:", JOKE_CHARACTERS)
    if selected_character is None:
        _show_cancelled_message()
        return
    _save_state(
        f"Joke character updated to {selected_character}.",
        lambda state: setattr(state, "joke_character", selected_character),
    )


def _edit_joke_sound() -> None:
    sound_files = _available_sound_files()
    if not sound_files:
        typer.secho("No sound files were found in chronoterm/sounds.", fg=typer.colors.RED)
        return

    selected_sound = _select_from_menu("Select a sound for the joke command:", sound_files)
    if selected_sound is None:
        _show_cancelled_message()
        return
    _save_state(
        f"Joke sound updated to {selected_sound}.",
        lambda state: setattr(state, "joke_sound", selected_sound),
    )


def _edit_joke_settings() -> None:
    selected_setting = _select_from_menu("Select a joke setting to edit:", ["Character", "Sound"])
    if selected_setting is None:
        _show_cancelled_message()
        return
    if selected_setting == "Character":
        _edit_joke_character()
        return
    _edit_joke_sound()


def _command_settings(command_name: str) -> None:
    handlers = {
        "time": _edit_time_settings,
        "world": lambda: _edit_clock_format("world"),
        "joke": _edit_joke_settings,
    }
    handler = handlers.get(command_name)
    if handler is None:
        typer.secho(f"No editable settings are available yet for '{command_name}'.", fg=typer.colors.YELLOW)
        return
    handler()


def launch_settings() -> None:
    selected_command = _select_from_menu("Select a command to configure:", COMMANDS)
    _clear_screen()

    if selected_command is None:
        typer.secho("Settings closed.", fg=typer.colors.YELLOW)
        return

    _command_settings(selected_command)
