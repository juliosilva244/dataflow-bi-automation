from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Callable

import pandas as pd

from services.logging_config import get_logger
from services.settings import get_insight_settings

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    value: Any
    created_at: float


class SessionScopedCache:
    """Small LRU/TTL cache intended to live inside one Streamlit session."""

    def __init__(self, max_entries: int = 8, ttl_seconds: int = 900):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str, default=None):
        entry = self._entries.get(key)
        if entry is None:
            return default
        if time.monotonic() - entry.created_at > self.ttl_seconds:
            self._entries.pop(key, None)
            return default
        self._entries.move_to_end(key)
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = CacheEntry(value=value, created_at=time.monotonic())
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


class TelemetryCollector:
    def __init__(self):
        self.latest: dict[str, dict[str, Any]] = {}

    def record(
        self,
        operation: str,
        duration_seconds: float,
        *,
        rows: int | None = None,
        cache_hit: bool = False,
        failed: bool = False,
    ) -> None:
        measurement = {
            "duration_ms": round(duration_seconds * 1_000, 3),
            "rows": rows,
            "cache_hit": cache_hit,
            "failed": failed,
        }
        self.latest[operation] = measurement
        logger.info(
            "telemetria operacao=%s duracao_ms=%.3f linhas=%s cache_hit=%s falha=%s",
            operation,
            measurement["duration_ms"],
            rows if rows is not None else "n/a",
            cache_hit,
            failed,
        )

    @contextmanager
    def measure(self, operation: str, *, rows: int | None = None, cache_hit: bool = False):
        started = time.perf_counter()
        failed = False
        try:
            yield
        except Exception:
            failed = True
            raise
        finally:
            self.record(
                operation,
                time.perf_counter() - started,
                rows=rows,
                cache_hit=cache_hit,
                failed=failed,
            )


def content_signature(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def dataframe_fingerprint(df: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps([str(column) for column in df.columns]).encode())
    digest.update(json.dumps([str(dtype) for dtype in df.dtypes]).encode())
    digest.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    quality = df.attrs.get("quality_report")
    if quality is not None:
        quality_value = asdict(quality) if hasattr(quality, "__dataclass_fields__") else quality
        digest.update(json.dumps(quality_value, sort_keys=True, default=str).encode())
    return digest.hexdigest()


def get_cached_analytics(
    df: pd.DataFrame,
    cache: SessionScopedCache,
    telemetry: TelemetryCollector,
    builder: Callable[[pd.DataFrame], dict[str, Any]],
) -> tuple[dict[str, Any], str, bool]:
    fingerprint = dataframe_fingerprint(df)
    key = f"analytics:v3-exact-rankings:{fingerprint}"
    cached = cache.get(key)
    if cached is not None:
        with telemetry.measure("agregacao", rows=len(df), cache_hit=True):
            return cached, key, True
    with telemetry.measure("agregacao", rows=len(df), cache_hit=False):
        state = builder(df)
    cache.set(key, state)
    return state, key, False


def get_cached_export(
    df: pd.DataFrame,
    analytics_state: dict[str, Any],
    analytics_key: str,
    cache: SessionScopedCache,
    telemetry: TelemetryCollector,
    exporter: Callable[[pd.DataFrame, dict[str, Any]], Any],
):
    key = get_export_cache_key(analytics_key)
    cached = cache.get(key)
    if cached is not None:
        with telemetry.measure("exportacao", rows=len(df), cache_hit=True):
            return cached, key, True
    with telemetry.measure("exportacao", rows=len(df), cache_hit=False):
        output = exporter(df, analytics_state)
        value = output.getvalue() if hasattr(output, "getvalue") else bytes(output)
    cache.set(key, value)
    return value, key, False


def get_export_cache_key(analytics_key: str) -> str:
    insight_config = json.dumps(asdict(get_insight_settings()), sort_keys=True)
    config_signature = hashlib.sha256(insight_config.encode()).hexdigest()
    return f"export:v2:{analytics_key}:{config_signature}"

