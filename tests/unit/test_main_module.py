"""Smoke import for application entry module (coverage)."""


def test_main_app_metadata():
    import main

    assert main.app.title == "Contacts API"
