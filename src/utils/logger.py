import copy
import logging
from collections.abc import Callable

from colorama import Fore, Style, init

init(autoreset=True)

APP_LOGGER_NAME = "hw-10"

_LEVEL_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
}


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.name == APP_LOGGER_NAME:
            ts = self.formatTime(record, self.datefmt)
            level_color = _LEVEL_COLORS.get(record.levelno, "")
            level = f"{level_color}{record.levelname}{Style.RESET_ALL}"
            mark = f"{Fore.MAGENTA}{Style.BRIGHT}▶{Style.RESET_ALL}"
            log_title = getattr(record, "log_title", None)
            title_part = ""
            if log_title:
                title_part = (
                    f"{Fore.YELLOW}{Style.BRIGHT}[{log_title}]{Style.RESET_ALL} "
                )
            if record.levelno == logging.INFO:
                msg_color = Fore.GREEN
            elif record.levelno == logging.WARNING:
                msg_color = Fore.YELLOW
            elif record.levelno in (logging.ERROR, logging.CRITICAL):
                msg_color = Fore.RED
            else:
                msg_color = Fore.CYAN
            body = (
                title_part
                + f"{msg_color}{Style.BRIGHT}{record.getMessage()}{Style.RESET_ALL}"
            )
            return f"{mark} {ts} | {APP_LOGGER_NAME} | {level} | {body}"

        r = copy.copy(record)
        color = _LEVEL_COLORS.get(record.levelno, "")
        r.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(r)


def _quiet_sqlalchemy_loggers() -> None:
    for name in (
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            _quiet_sqlalchemy_loggers()

            log = logging.getLogger(APP_LOGGER_NAME)
            log.setLevel(logging.INFO)
            log.propagate = False

            if not log.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    ColoredFormatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )
                log.addHandler(handler)

            cls._instance._log = log
        return cls._instance

    def debug(self, message: str) -> None:
        self._log.debug(message)

    def info(self, message: str, *, title: str | None = None) -> None:
        """Log INFO. Optional *title* is shown as [title] in yellow; message color follows log level."""
        self._emit(self._log.info, message, title=title)

    def warning(self, message: str, *, title: str | None = None) -> None:
        """Log WARNING (e.g. missing entity). Optional ``title=`` matches ``info()``."""
        self._emit(self._log.warning, message, title=title)

    def error(self, message: str, *, title: str | None = None) -> None:
        """Log ERROR. Optional ``title=`` matches ``info()``."""
        self._emit(self._log.error, message, title=title)

    def _emit(
        self,
        log_fn: Callable[..., None],
        message: str,
        *,
        title: str | None,
    ) -> None:
        if title:
            log_fn(message, extra={"log_title": title})
        else:
            log_fn(message)