from __future__ import annotations

import logging
import os
import re
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*(?:bearer\s+)?[^\s,;]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+"),
    re.compile(r"\bgsk_[A-Za-z0-9_-]+\b"),
)


def redact_secrets(value: object) -> str:
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[SEGREDO_REMOVIDO]", text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_secrets(super().format(record))


class SafeRotatingFileHandler(RotatingFileHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        # logging's default error handler prints raw args/tracebacks to stderr.
        # Logging failure must never disclose a provider body or break the app.
        try:
            sys.stderr.write("DataFlow: falha ao gravar log técnico.\n")
        except OSError:
            pass


_HANDLER_LOCK = threading.RLock()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    with _HANDLER_LOCK:
        directory = Path(__file__).resolve().parents[1] / "outputs"
        directory.mkdir(parents=True, exist_ok=True)
        log_path = directory / f"dataflow-{os.getpid()}.log"
        # Registry survives module reloads. All named loggers in a process use
        # one file handle/rotation lock, while different processes use other files.
        registry = logging.getLogger("dataflow._handler_registry")
        handler = next((h for h in registry.handlers if getattr(h, "_dataflow_path", None) == str(log_path)), None)
        if handler is None:
            handler = SafeRotatingFileHandler(
                log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8", delay=True,
            )
            handler._dataflow_path = str(log_path)
            handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
            registry.addHandler(handler)
        # Retire only this application's old file handlers on hot reload.
        for previous in list(logger.handlers):
            if previous is not handler and isinstance(previous, RotatingFileHandler) and Path(previous.baseFilename).parent == directory:
                logger.removeHandler(previous)
                if previous not in registry.handlers:
                    previous.close()
        if handler not in logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

