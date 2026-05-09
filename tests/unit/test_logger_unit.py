"""Unit tests for application Logger."""

import logging

from src.utils.logger import ColoredFormatter, Logger


def test_logger_singleton_returns_same_instance():
    Logger._instance = None
    first = Logger()
    second = Logger()
    assert first is second


def test_colored_formatter_non_app_logger_falls_back():
    fmt = ColoredFormatter("%(levelname)s %(message)s")
    record = logging.LogRecord("other", logging.INFO, __file__, 1, "msg", (), None)
    out = fmt.format(record)
    assert "msg" in out or "INFO" in out
