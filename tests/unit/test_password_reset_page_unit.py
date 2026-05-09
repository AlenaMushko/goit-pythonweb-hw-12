"""Unit tests for password reset HTML helper."""

from src.services.password_reset_page_service import render_password_reset_page


def test_render_password_reset_page_escapes_message():
    html = render_password_reset_page(token="t", user_id=1, message='<script>alert(1)</script>')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_password_reset_page_includes_hidden_user_id():
    html = render_password_reset_page(token="x", user_id=42, message="hi")
    assert 'name="user_id"' in html
    assert "42" in html
