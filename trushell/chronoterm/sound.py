from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


class AudioPlaybackUnavailable(RuntimeError):
    """Raised when the host has no supported way to play a selected asset."""


def _run_quietly(cmd: list[str]) -> bool:
    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _resolve_windows_sound_path(path: Path) -> Path | None:
    if path.suffix.lower() == ".wav":
        return path

    wav_path = path.with_suffix(".wav")
    if wav_path.exists():
        return wav_path

    return None


def play_audio_file(path: str | Path) -> bool:
    """Play a specific audio asset when a platform player is available.

    Returns False when a player was attempted but did not confirm success.
    """
    sound_path = Path(path)

    if sys.platform.startswith("win"):
        playable_path = _resolve_windows_sound_path(sound_path)
        if playable_path is None:
            raise AudioPlaybackUnavailable(
                f"Windows playback requires a .wav fallback for {sound_path.name}"
            )

        import winsound

        winsound.PlaySound(str(playable_path), winsound.SND_FILENAME)
        return True

    if sys.platform == "darwin":
        if not shutil.which("afplay"):
            raise AudioPlaybackUnavailable("afplay is unavailable")
        return _run_quietly(["afplay", str(sound_path)])

    attempted_player = False
    for player in (
        ["paplay", str(sound_path)],
        ["aplay", str(sound_path)],
        ["ffplay", "-nodisp", "-autoexit", str(sound_path)],
        ["mpg123", "-q", str(sound_path)],
        ["mpg321", "-q", str(sound_path)],
    ):
        if shutil.which(player[0]):
            attempted_player = True
            if _run_quietly(player):
                return True

    if attempted_player:
        return False

    raise AudioPlaybackUnavailable(
        f"No supported Linux audio player could play {sound_path}"
    )


def play_alarm() -> None:
    """Play alarm sound compatible with all platforms and terminals."""
    try:
        if sys.platform.startswith("win"):
            import winsound

            winsound.Beep(1200, 400)
            winsound.Beep(900, 400)

        elif sys.platform == "darwin":
            _run_quietly(["afplay", "/System/Library/Sounds/Glass.aiff"])

        else:  # Linux/Unix
            for cmd in [
                [
                    "paplay",
                    "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
                ],
                ["aplay", "/usr/share/sounds/alsa/Front_Center.wav"],
                ["canberra-gtk-play", "--id=alarm-clock-elapsed"],
            ]:
                if shutil.which(cmd[0]):
                    if _run_quietly(cmd):
                        return

            sys.stdout.write("\007" * 3)
            sys.stdout.flush()

    except Exception:
        sys.stdout.write("\007")
        sys.stdout.flush()
