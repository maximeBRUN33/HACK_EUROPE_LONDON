from __future__ import annotations

import logging
import os

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging() -> None:
    level_name = os.getenv("LEGACY_ATLAS_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_format = os.getenv("LEGACY_ATLAS_LOG_FORMAT", DEFAULT_LOG_FORMAT)

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=log_format)
        return

    root.setLevel(level)
    for handler in root.handlers:
        handler.setLevel(level)
        if handler.formatter is None:
            handler.setFormatter(logging.Formatter(log_format))
