from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cowsay
import pyjokes


def _sound_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[1] / "chronoterm" / "sounds" / filename


def _play_sound(filename: str) -> None:
    try:
        # lazy import to avoid optional dependency at kernel import time
        from trushell.chronoterm.sound import play_alarm

        sound_path = _sound_path(filename)
        if not sound_path.exists():
            return
        play_alarm()
    except Exception:
        # best-effort: do not raise from sound playing
        return


def _joke_preferences() -> Tuple[str, str]:
    try:
        from trushell.chronoterm.state import StateStore

        state = StateStore().load()
        return state.joke_character or "cow", state.joke_sound or "cow-sound.mp3"
    except Exception:
        return "cow", "cow-sound.mp3"


def run_joke_command(_: str) -> str:
    """Return a formatted joke string (cow art by default)."""
    joke_text = pyjokes.get_joke()
    character_name, sound_file = _joke_preferences()
    _play_sound(sound_file)
    speaker = getattr(cowsay, character_name, cowsay.cow)
    return speaker(joke_text)


def run_joke_trex_command(_: str) -> str:
    """Return a T-Rex joke string."""
    joke_text = pyjokes.get_joke()
    _play_sound("trex-sound.mp3")
    return cowsay.trex(joke_text)
from __future__ import annotations

from trushell.pyfunny import joke, joke_trex


def run_joke_command(_: str) -> None:
    """Tell a random joke with the default TruShell humor engine."""
    try:
        print(joke())
    except Exception as error:
        print(f"Joke error: {error}")


def run_joke_trex_command(_: str) -> None:
    """Tell a T-Rex joke with sound."""
    try:
        print(joke_trex())
    except Exception as error:
        print(f"Joke error: {error}")
