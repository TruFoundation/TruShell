import chronoterm_project as project


def test_main(monkeypatch):
    called = False

    def fake_run_shell():
        nonlocal called
        called = True

    monkeypatch.setattr(project, "run_shell", fake_run_shell)

    project.main()

    assert called is True
