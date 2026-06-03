from trushell.state import default_state_path


def test_default_state_path_contains_app_folder() -> None:
    path = default_state_path()
    assert "TruShell" in str(path)
