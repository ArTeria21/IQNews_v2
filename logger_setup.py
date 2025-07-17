import logging
import os
import uuid
from logging import Logger

from starlite import LoggingConfig


class CorrelationLogger(Logger):
    """Logger that supports correlation_id in log records."""

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        correlation_id = kwargs.pop("correlation_id", None)
        if extra is None:
            extra = {}
        extra["correlation_id"] = correlation_id or "N/A"
        super()._log(level, msg, args, exc_info, extra, stack_info)


class CorrelationFormatter(logging.Formatter):
    """Formatter ensuring correlation_id and source_file fields."""

    def format(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "N/A"
        if not hasattr(record, "source_file"):
            record.source_file = "Unknown"
        return super().format(record)


def setup_logger(source_file: str) -> Logger:
    """Configure a logger that writes to ``./logs/system.log``."""

    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "logs")
    log_file = os.path.join(log_dir, "system.log")
    os.makedirs(log_dir, exist_ok=True)

    logging.setLoggerClass(CorrelationLogger)

    config = LoggingConfig(
        formatters={
            "default": {
                "()": CorrelationFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - Source: %(source_file)s - Correlation ID: %(correlation_id)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        handlers={
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": log_file,
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            }
        },
        loggers={"system_logger": {"level": "INFO", "handlers": ["file"], "propagate": False}},
        root={"handlers": ["file"], "level": "INFO"},
    )

    get_logger = config.configure()
    logger = get_logger("system_logger")
    adapter = logging.LoggerAdapter(logger, {"source_file": source_file})
    return adapter


def generate_correlation_id() -> str:
    """Return a new correlation ID."""

    return str(uuid.uuid4())
