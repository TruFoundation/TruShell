import cowsay
import pyjokes

import typer
from pathlib import Path

from playsound import playsound

from chronoterm.state import StateStore

app = typer.Typer(help="Joke REPL: Type 'cow', 'trex', or 'exit'.")

DEFAULT_JOKE_CHARACTER = "cow"
DEFAULT_JOKE_SOUND = "cow-sound.mp3"


def _joke_preferences() -> tuple[str, str]:
    state = StateStore().load()
    character_name = state.joke_character or DEFAULT_JOKE_CHARACTER
    sound_file = state.joke_sound or DEFAULT_JOKE_SOUND
    return character_name, sound_file


def _render_joke(character_name: str, text: str) -> str:
    speaker = getattr(cowsay, character_name, None)
    if not callable(speaker):
        speaker = cowsay.cow
    return speaker(text)


def _sound_path(filename: str) -> str:
    return str(Path(__file__).resolve().parent / "chronoterm" / "sounds" / filename)

# Individual Commands

@app.command()
def joke():
    joke_text = pyjokes.get_joke()
    character_name, sound_file = _joke_preferences()
    playsound(_sound_path(sound_file))
    return _render_joke(character_name, joke_text)

@app.command()
def joke_trex():
    joke_text = pyjokes.get_joke()

    
    # Play only one of them. Either trex-sound or bruh-sound.
    playsound(r'chronoterm/sounds/trex-sound.mp3')
    playsound(r'chronoterm/sounds/bruh-sound.mp3')
    return cowsay.trex(joke_text)

# # Interactive Shell
# @app.command()
# def repl():
#     """Starts an interactive shell for jokes."""
#     typer.secho("Entering Joke REPL. Type 'exit' to quit.", fg=typer.colors.CYAN)
    
#     # The Loop
#     while True:
#         # Read
#         command = typer.prompt("joke-shell").lower().strip()

#         # Evaluate & Print
#         if command in ["exit", "quit"]:
#             break
#         elif command == "cow":
#             cow()
#         elif command == "trex":
#             trex()
#         elif command == "help":
#             print("Available commands: cow, trex, exit, help")
#         else:
#             typer.secho(f"Unknown command: {command}", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
