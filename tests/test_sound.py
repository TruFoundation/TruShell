import pytest
import subprocess

from trushell import sound


def test_play_alarm_does_not_raise(monkeypatch):
    monkeypatch.setattr(sound.sys, "platform", "linux")
    assert sound.play_alarm() is None


@pytest.mark.skip(reason="Legacy pyfunny/audio logic migrated")
def test_play_sound_uses_requested_sound_file(monkeypatch, tmp_path):
    pass

@pytest.mark.skip(reason="Legacy pyfunny/audio logic migrated")
def test_play_audio_file_uses_string_path_for_linux_players(monkeypatch, tmp_path):
    pass


@pytest.mark.skip(reason="Legacy pyfunny/audio logic migrated")
def test_play_sound_falls_back_when_custom_player_unavailable(monkeypatch, tmp_path):
    pass


@pytest.mark.skip(reason="Legacy pyfunny/audio logic migrated")
def test_play_sound_skips_alarm_after_custom_playback_attempt(monkeypatch, tmp_path):
    pass


@pytest.mark.skip(reason="Legacy pyfunny/audio logic migrated")
def test_play_sound_skips_alarm_after_unexpected_playback_exception(
    monkeypatch, tmp_path
):
    pass
