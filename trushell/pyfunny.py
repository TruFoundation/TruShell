from __future__ import annotations

from pathlib import Path

import cowsay
import pyjokes
import typer

from .chronoterm.state import StateStore
from .chronoterm.sound import (
    AudioPlaybackUnavailable,
    play_alarm,
    play_audio_file,
)

DEFAULT_JOKE_CHARACTER = "cow"
DEFAULT_JOKE_SOUND = "cow-sound.mp3"


def _sound_path(filename: str) -> Path:
    return Path(__file__).resolve().parent / "chronoterm" / "sounds" / filename


def _play_sound(filename: str) -> None:
    sound_path = _sound_path(filename)

    if not sound_path.exists():
        typer.secho(f"Sound file missing: {sound_path}", fg=typer.colors.YELLOW)
        return

    try:
        played_selected_sound = play_audio_file(sound_path)
    except AudioPlaybackUnavailable:
        typer.secho(
            "Unable to play selected sound. Falling back to alarm.",
            fg=typer.colors.YELLOW,
        )
        try:
            play_alarm()
        except Exception:
            typer.secho(
                "Unable to play sound. Continuing without audio.",
                fg=typer.colors.YELLOW,
            )
        return
    except Exception:
        typer.secho(
            "Selected sound playback failed unexpectedly. "
            "Skipping fallback to avoid overlapping audio.",
            fg=typer.colors.YELLOW,
        )
        return

    if not played_selected_sound:
        typer.secho(
            "Selected sound playback was attempted but failed. "
            "Skipping fallback to avoid overlapping audio.",
            fg=typer.colors.YELLOW,
        )


def _joke_preferences() -> tuple[str, str]:
    state = StateStore().load()
    return (
        state.joke_character or DEFAULT_JOKE_CHARACTER,
        state.joke_sound or DEFAULT_JOKE_SOUND,
    )


def _render_joke(character_name: str, text: str) -> str:
    speaker = getattr(cowsay, character_name, None)
    if not callable(speaker):
        speaker = cowsay.cow
    return speaker(text)


def joke() -> str:
    joke_text = pyjokes.get_joke()
    character_name, sound_file = _joke_preferences()
    _play_sound(sound_file)
    return _render_joke(character_name, joke_text)


def joke_trex() -> str:
    joke_text = pyjokes.get_joke()
    _play_sound("trex-sound.mp3")
    return cowsay.trex(joke_text)
