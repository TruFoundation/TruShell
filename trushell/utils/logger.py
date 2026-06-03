from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = "trushell") -> logging.Logger:
    """Create or return the centralized TruShell logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_dir = Path.home() / ".trushell" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "trushell.log"

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
