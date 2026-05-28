from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

import typer
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TextArea

from .pyfunny import joke, joke_trex
from .settings import launch_settings
from .todocli import addtask, delete_todo, update_todo, complete_todo, showtask
from .chronoterm.shell import app as chronoterm_app

HELP_TEXT = (
    "Available commands: joke, joke_trex, "
    "addtask, deletetask, updatetask, completetask, showtask, "
    "now, time, world, tz, alarm, sw, settings, exit, help"
)


def _split_command(user_input: str) -> tuple[str, str]:
    parts = user_input.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""
    return command, argument


def _prompt_command() -> tuple[str, str, str]:
    raw_command = typer.prompt("atoffice-shell").strip()
    command, argument = _split_command(raw_command)
    return raw_command, command, argument


class AtonEditor(App):
    """Simple full-screen text editor for ATON shell files."""

    inherit_bindings = True

    CSS = """
    Screen { padding: 0; }
    #editor { height: 1fr; }
    Footer { height: 1; }
    """

    BINDINGS = [
        ("ctrl+shift+s", "save_file", "Ctrl+Shift+S Save"),
        ("ctrl+shift+q", "quit_app", "Ctrl+Shift+Q Quit"),
    ]

    def __init__(self, file_path: str, initial_text: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file_path = file_path
        self.file_content = initial_text if initial_text is not None else ""

        if initial_text is None and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    self.file_content = handle.read()
            except OSError as error:
                self.file_content = f"Error reading file: {error}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield TextArea(self.file_content, id="editor_text_area")
        yield Footer()

    def on_mount(self) -> None:
        self.text_area.focus()

    def action_save_file(self) -> None:
        text_area = self.query_one("#editor_text_area", TextArea)
        try:
            with open(self.file_path, "w", encoding="utf-8") as handle:
                handle.write(text_area.text)
        except (PermissionError, OSError) as error:
            self.notify(f"Failed to save file: {error}", severity="error")

    def action_quit_app(self) -> None:
        self.exit()


def _handle_joke_command(command: str) -> bool:
    if command in {"joke", "joke_trex", "joke-trex"}:
        if command == "joke":
            typer.echo(joke())
        else:
            typer.echo(joke_trex())
        return True
    return False


def _handle_todo_command(command: str) -> bool:
    delete_match = re.match(r"deletetask\s+(\d+)", command)
    if delete_match:
        delete_todo(int(delete_match.group(1)) - 1)
        return True

    add_match = re.match(r'addtask\s+"([^"]+)"\s+"([^"]+)"', command)
    if add_match:
        addtask(add_match.group(1), add_match.group(2))
        return True

    update_match = re.match(r'updatetask\s+(\d+)\s+"([^"]+)"\s+"([^"]+)"', command)
    if update_match:
        update_todo(int(update_match.group(1)), update_match.group(2), update_match.group(3))
        return True

    complete_match = re.match(r'completetask\s+(\d+)', command)
    if complete_match:
        complete_todo(int(complete_match.group(1)) - 1)
        return True

    if command == "showtasks":
        showtask()
        return True

    return False


def _handle_edit_command(raw_command: str) -> bool:
    command, argument = _split_command(raw_command)
    if command != "edit":
        return False

    if not argument.strip():
        typer.secho("⚠️ Syntax: edit <filename>", fg=typer.colors.YELLOW)
        return True

    file_path = Path(argument.strip())
    initial_text = file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    try:
        AtonEditor(str(file_path), initial_text=initial_text).run()
    except Exception as error:
        typer.secho(f"Editor error: {error}", fg=typer.colors.RED)

    return True


def _handle_local_command(command: str, argument: str) -> str:
    if command == "addtask" and not argument:
        typer.secho(
            '⚠️ Missing arguments. Syntax: addtask "task-name" "category"',
            fg=typer.colors.YELLOW,
        )
        return "handled"

    if command in {"exit", "quit"}:
        return "exit"
    if _handle_joke_command(command):
        return "handled"
    if _handle_todo_command(command):
        return "handled"
    if command == "settings":
        launch_settings()
        return "handled"
    if command == "help":
        typer.echo(HELP_TEXT)
        return "handled"
    return "unhandled"


def _handle_chronoterm_command(raw_command: str, normalized_command: str) -> bool:
    if not re.match(r"^(now|time|world|tz|alarm|sw)\b", normalized_command):
        return False

    try:
        chronoterm_app(shlex.split(raw_command))
    except SystemExit:
        pass
    return True


def _handle_cd_command(raw_command: str) -> bool:
    """Handle cd natively so the shell's working directory changes permanently."""
    command, argument = _split_command(raw_command)
    if command != "cd":
        return False

    if not argument.strip():
        typer.secho("Syntax: cd <directory_path>", fg=typer.colors.YELLOW)
        return True

    target = os.path.expanduser(argument)

    try:
        os.chdir(target)
        subprocess.run("ls", shell=True, check=False, cwd=os.getcwd())
    except (FileNotFoundError, NotADirectoryError, PermissionError) as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)
    except OSError as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)

    return True


def _handle_os_fallback(raw_command: str) -> bool:
    """Pass unrecognized commands to the host OS shell."""
    command = raw_command.strip()
    if not command:
        return False

    try:
        completed = subprocess.run(command, shell=True, check=False, cwd=os.getcwd())
    except (OSError, subprocess.SubprocessError) as error:
        typer.secho("❓ Command not recognized by ATON shell or your host OS.", fg=typer.colors.YELLOW)
        typer.secho(f"OS fallback error: {error}", fg=typer.colors.RED)
        return True

    if completed.returncode != 0:
        typer.secho("❓ Command not recognized by ATON shell or your host OS.", fg=typer.colors.YELLOW)
    return True


def run_interactive_shell() -> None:
    """Persistent REPL loop for the AtOffice shell core."""
    typer.secho("Entering AtOffice Shell. Type 'exit' to quit.", fg=typer.colors.CYAN)

    while True:
        try:
            raw_command, command, argument = _prompt_command()
        except (KeyboardInterrupt, EOFError):
            typer.echo("")
            break

        local_result = _handle_local_command(command, argument)
        if local_result == "exit":
            break
        if local_result == "handled":
            continue
        if _handle_chronoterm_command(raw_command, command):
            continue
        if _handle_cd_command(raw_command):
            continue
        if _handle_edit_command(raw_command):
            continue
        if _handle_os_fallback(raw_command):
            continue

        typer.secho(f"Unknown command: {command}", fg=typer.colors.RED)
