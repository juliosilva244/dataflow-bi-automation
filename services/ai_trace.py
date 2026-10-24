"""Short-lived, allowlisted generation diagnostics: no payloads or credentials."""

import re
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from services.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class GenerationTrace:
    correlation: str
    model: str
    started: float


_CURRENT = ContextVar("dataflow_ai_trace", default=None)


def safe_model(model):
    value = str(model)
    return value if re.fullmatch(r"[A-Za-z0-9/_.-]{1,100}", value) and "gsk_" not in value else "modelo_nao_identificado"


def trace_stage(stage, error=None, *, trace=None, model=None):
    current = trace or _CURRENT.get()
    if current is None:
        return
    status = getattr(error, "status_code", None)
    status = status if type(status) is int and 100 <= status <= 599 else None
    # Call sites supply literal stage labels. Never accept exception messages.
    label = stage if re.fullmatch(r"[a-z_.]{1,50}", stage) else "unknown"
    try:
        logger.info(
            "ai_trace correlation=%s stage=%s model=%s exception=%s http=%s elapsed_ms=%.3f",
            current.correlation, label, safe_model(model or current.model),
            type(error).__name__ if error else None, status,
            (time.perf_counter() - current.started) * 1000,
        )
    except Exception:
        # Observability must not change the outcome of generation.
        pass


@contextmanager
def generation_trace(model):
    current = GenerationTrace(uuid.uuid4().hex[:16], safe_model(model), time.perf_counter())
    token = _CURRENT.set(current)
    try:
        yield current
    finally:
        _CURRENT.reset(token)
