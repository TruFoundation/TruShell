import subprocess

from trushell import sound


def test_play_alarm_uses_quiet_subprocess(monkeypatch):
    calls = []

    def fake_which(name: str) -> str | None:
        return "/usr/bin/" + name if name == "paplay" else None

    class FakeResult:
        returncode = 0

    def fake_run(cmd, stdout, stderr, check):
        calls.append({"cmd": cmd, "stdout": stdout, "stderr": stderr, "check": check})
        return FakeResult()

    monkeypatch.setattr(sound.shutil, "which", fake_which)
    monkeypatch.setattr(sound.subprocess, "run", fake_run)

    sound.play_alarm()

    assert calls
    assert calls[0]["stdout"] == subprocess.DEVNULL
    assert calls[0]["stderr"] == subprocess.DEVNULL
    assert calls[0]["check"] is False
    assert calls[0]["cmd"][0] == "paplay"
