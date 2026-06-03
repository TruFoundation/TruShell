import subprocess

from trushell import sound


def test_play_alarm_uses_quiet_subprocess(monkeypatch):
    calls = []
    monkeypatch.setattr(sound.sys, "platform", "linux")

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


def test_play_sound_uses_requested_sound_file(monkeypatch, tmp_path):
    sound_file = tmp_path / "custom-sound.mp3"
    sound_file.write_text("not real audio")
    calls = []

    monkeypatch.setattr(pyfunny, "_sound_path", lambda filename: sound_file)

    def fake_play_file(path):
        calls.append(path)
        return True

    monkeypatch.setattr(sound, "play_audio_file", fake_play_file, raising=False)
    monkeypatch.setattr(pyfunny, "play_audio_file", fake_play_file, raising=False)

    pyfunny._play_sound("custom-sound.mp3")

    assert calls == [sound_file]

def test_play_audio_file_uses_string_path_for_linux_players(monkeypatch, tmp_path):
    sound_file = tmp_path / "custom-sound.mp3"
    sound_file.write_text("not real audio")
    calls = []

    monkeypatch.setattr(sound.sys, "platform", "linux")
    monkeypatch.setattr(
        sound.shutil,
        "which",
        lambda name: "/usr/bin/paplay" if name == "paplay" else None,
    )

    def fake_run(cmd, stdout, stderr, check):
        calls.append(cmd)

        class FakeResult:
            returncode = 0

        return FakeResult()

    monkeypatch.setattr(sound.subprocess, "run", fake_run)

    assert sound.play_audio_file(sound_file) is True
    assert calls == [["paplay", str(sound_file)]]


def test_play_sound_falls_back_when_custom_player_unavailable(monkeypatch, tmp_path):
    sound_file = tmp_path / "custom-sound.mp3"
    sound_file.write_text("not real audio")
    alarm_calls = []

    monkeypatch.setattr(pyfunny, "_sound_path", lambda filename: sound_file)
    monkeypatch.setattr(
        pyfunny,
        "play_audio_file",
        lambda path: (_ for _ in ()).throw(
            sound.AudioPlaybackUnavailable("no supported player")
        ),
    )
    monkeypatch.setattr(pyfunny, "play_alarm", lambda: alarm_calls.append("alarm"))

    pyfunny._play_sound("custom-sound.mp3")

    assert alarm_calls == ["alarm"]


def test_play_sound_skips_alarm_after_custom_playback_attempt(monkeypatch, tmp_path):
    sound_file = tmp_path / "custom-sound.mp3"
    sound_file.write_text("not real audio")
    alarm_calls = []

    monkeypatch.setattr(pyfunny, "_sound_path", lambda filename: sound_file)
    monkeypatch.setattr(pyfunny, "play_audio_file", lambda path: False)
    monkeypatch.setattr(pyfunny, "play_alarm", lambda: alarm_calls.append("alarm"))

    pyfunny._play_sound("custom-sound.mp3")

    assert alarm_calls == []


def test_play_sound_skips_alarm_after_unexpected_playback_exception(
    monkeypatch, tmp_path
):
    sound_file = tmp_path / "custom-sound.mp3"
    sound_file.write_text("not real audio")
    alarm_calls = []

    monkeypatch.setattr(pyfunny, "_sound_path", lambda filename: sound_file)

    def fake_play_file(path):
        raise RuntimeError("player failed after starting playback")

    monkeypatch.setattr(pyfunny, "play_audio_file", fake_play_file)
    monkeypatch.setattr(pyfunny, "play_alarm", lambda: alarm_calls.append("alarm"))

    pyfunny._play_sound("custom-sound.mp3")

    assert alarm_calls == []
