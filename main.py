from pyfunny import joke, joke_trex
from todocli import addtask, deletetask, updatetask, completetask, showtask
from settings import launch_settings

from chronoterm.shell import app as chronoterm_app

import typer
import re
import shlex


app = typer.Typer(help="Joke REPL: Type 'cow', 'trex', or 'exit'.")


# Interactive Shell
@app.command()
def atoffice():
    """Starts an interactive shell for jokes."""
    typer.secho("Entering AtOffice REPL. Type 'exit' to quit.", fg=typer.colors.CYAN)
    
    # The Loop
    while True:
        # Shell prompt
        raw_command = typer.prompt("atoffice-shell").strip()
        command = raw_command.lower()

        

        # PyJoke module
        if command in ["exit", "quit"]:
            break
        elif command == "joke":
            print(joke())
        elif command == "joke_trex":
            print(joke_trex())

      
        # ToDoCLI module
        elif match := re.match(r"deletetask\s(\d+)", command):
            position = int(match.group(1))
            deletetask(position)

        elif match := re.match(r'addtask\s+"([^"]+)"\s+"([^"]+)"', command):
            task_name = match.group(1)
            category_name = match.group(2)
            addtask(task_name, category_name)

        elif match := re.match(r'updatetask\s+(\d+)\s+"([^"]+)"\s+"([^"]+)"', command):
            position = int(match.group(1))
            task = match.group(2)
            category = match.group(3)
            updatetask(position, task, category)

        elif match := re.match(r'completetask\s+(\d+)', command):
            position = int(match.group(1))
            completetask(position)

        elif command == "showtasks":
            showtask()

        elif command == "settings":
            launch_settings()

        # Chronoterm module
        elif re.match(r"^(now|time|world|tz|alarm|sw)\b", command):
            try:
                chronoterm_app(shlex.split(raw_command))
            except SystemExit:
                # Typer exits after each command; keep the at-office shell running.
                pass


        # additionals...
        elif command == "help":
            print("Available commands: joke, joke_trex, \n addtask, deletetask, updatetask, completetask, showtask, \nnow, time, world, tz, alarm, sw, \nsettings, exit, help")
        else:
            typer.secho(f"Unknown command: {command}", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
