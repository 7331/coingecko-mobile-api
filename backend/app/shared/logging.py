import logging
import sys

import structlog

__all__ = ["configure_logging", "get_logger"]

_LOG_FORMAT = "%(message)s"


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.stdlib.get_logger(name)


def configure_logging(log_level: str | int) -> None:
    level = logging.getLevelNamesMapping().get(str(log_level).upper(), logging.WARNING)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)
    structlog.configure(
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
