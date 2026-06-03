from __future__ import annotations

import shutil
import subprocess
import sys


def play_alarm() -> None:
    """Play alarm sound compatible with all platforms and terminals."""
    try:
        if sys.platform.startswith("win"):
            import winsound

            winsound.Beep(1200, 400)
            winsound.Beep(900, 400)
        elif sys.platform == "darwin":
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            for cmd in [
                ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                ["aplay", "/usr/share/sounds/alsa/Front_Center.wav"],
                ["canberra-gtk-play", "--id=alarm-clock-elapsed"],
            ]:
                if shutil.which(cmd[0]):
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    if result.returncode == 0:
                        return
            sys.stdout.write("\007" * 3)
            sys.stdout.flush()
    except Exception:
        sys.stdout.write("\007")
        sys.stdout.flush()
