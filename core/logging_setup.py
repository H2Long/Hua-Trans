"""Structured logging for TranslateTor.

Writes to ~/.translatetor/app.log with automatic rotation (5 MB max, 3 backups).
Also mirrors WARNING+ messages to stderr.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from .config import CONFIG_DIR, ensure_dirs

_logger: logging.Logger | None = None
_log_path: Path | None = None


def get_logger() -> logging.Logger:
    """Return the application-wide logger, initializing it on first call."""
    global _logger, _log_path
    if _logger is not None:
        return _logger

    ensure_dirs()
    _log_path = CONFIG_DIR / "app.log"

    _logger = logging.getLogger("hua-trans")
    _logger.setLevel(logging.DEBUG)

    # File handler with rotation
    fh = logging.handlers.RotatingFileHandler(
        str(_log_path), maxBytes=5 * 1024 * 1024, backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _logger.addHandler(fh)

    # Stderr handler for warnings and above
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    ))
    _logger.addHandler(sh)

    _logger.info("Logging initialized")
    return _logger


def get_log_path() -> str:
    """Return the path to the log file."""
    if _log_path is None:
        get_logger()
    return str(_log_path)


def export_diagnostics() -> str:
    """Read and return the full log file contents for diagnostics export."""
    if _log_path is None or not _log_path.exists():
        return "No log file found."
    try:
        with open(_log_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read log: {e}"
