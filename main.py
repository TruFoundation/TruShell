from pyfunny import joke, joke_trex
from todocli import addtask, deletetask, updatetask, completetask, showtask
from settings import launch_settings

from chronoterm.shell import app as chronoterm_app

import typer
import re
import shlex


app = typer.Typer(help="Joke REPL: Type 'cow', 'trex', or 'exit'.")


HELP_TEXT = (
    "Available commands: joke, joke_trex, \n"
    " addtask, deletetask, updatetask, completetask, showtask, \n"
    "now, time, world, tz, alarm, sw, \n"
    "settings, exit, help"
)


def _prompt_command() -> tuple[str, str]:
    raw_command = typer.prompt("atoffice-shell").strip()
    normalized_command = raw_command.lower()
    return raw_command, normalized_command


def _handle_joke_command(command: str) -> bool:
    if command == "joke":
        print(joke())
        return True
    if command == "joke_trex":
        print(joke_trex())
        return True
    return False


def _handle_todo_command(command: str) -> bool:
    delete_match = re.match(r"deletetask\s(\d+)", command)
    if delete_match:
        deletetask(int(delete_match.group(1)))
        return True

    add_match = re.match(r'addtask\s+"([^"]+)"\s+"([^"]+)"', command)
    if add_match:
        addtask(add_match.group(1), add_match.group(2))
        return True

    update_match = re.match(r'updatetask\s+(\d+)\s+"([^"]+)"\s+"([^"]+)"', command)
    if update_match:
        updatetask(int(update_match.group(1)), update_match.group(2), update_match.group(3))
        return True

    complete_match = re.match(r'completetask\s+(\d+)', command)
    if complete_match:
        completetask(int(complete_match.group(1)))
        return True

    if command == "showtasks":
        showtask()
        return True

    return False


def _handle_local_command(command: str) -> str:
    if command in ["exit", "quit"]:
        return "exit"
    if _handle_joke_command(command):
        return "handled"
    if _handle_todo_command(command):
        return "handled"
    if command == "settings":
        launch_settings()
        return "handled"
    if command == "help":
        print(HELP_TEXT)
        return "handled"
    return "unhandled"


def _handle_chronoterm_command(raw_command: str, normalized_command: str) -> bool:
    if not re.match(r"^(now|time|world|tz|alarm|sw)\b", normalized_command):
        return False

    try:
        chronoterm_app(shlex.split(raw_command))
    except SystemExit:
        # Typer exits after each command, keep the at-office shell running.
        pass
    return True


# Interactive Shell
@app.command()
def atoffice():
    """Starts an interactive shell for jokes."""
    typer.secho("Entering AtOffice REPL. Type 'exit' to quit.", fg=typer.colors.CYAN)
    
    # The Loop
    while True:
        raw_command, command = _prompt_command()

        local_result = _handle_local_command(command)
        if local_result == "exit":
            break
        if local_result == "handled":
            continue
        if _handle_chronoterm_command(raw_command, command):
            continue

        if local_result == "unhandled":
            typer.secho(f"Unknown command: {command}", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
