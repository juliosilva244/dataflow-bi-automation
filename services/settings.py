from __future__ import annotations

import os
from dataclasses import dataclass


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "sim", "on"}


def _bounded_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)


@dataclass(frozen=True)
class SecuritySettings:
    max_upload_bytes: int
    max_rows: int
    max_columns: int
    max_xlsx_uncompressed_bytes: int
    max_xlsx_entries: int
    max_zip_compression_ratio: int
    ai_anonymize_default: bool
    ai_timeout_seconds: int
    ai_max_retries: int
    ai_requests_per_minute: int
    ai_max_output_tokens: int


@dataclass(frozen=True)
class InsightSettings:
    product_share_warning: float
    product_share_critical: float
    store_performance_warning: float
    store_performance_critical: float
    revenue_growth_positive: float
    revenue_growth_negative: float
    ticket_reference_minimum: float
    ticket_growth_positive: float


@dataclass(frozen=True)
class PerformanceSettings:
    cache_ttl_seconds: int
    cache_max_entries: int
    table_page_size: int
    excel_width_sample_rows: int


def get_security_settings() -> SecuritySettings:
    max_upload_mb = _bounded_int("DATAFLOW_MAX_UPLOAD_MB", 10, 1, 200)
    max_uncompressed_mb = _bounded_int(
        "DATAFLOW_MAX_XLSX_UNCOMPRESSED_MB", 100, max_upload_mb, 500
    )
    return SecuritySettings(
        max_upload_bytes=max_upload_mb * 1024 * 1024,
        max_rows=_bounded_int("DATAFLOW_MAX_ROWS", 100_000, 1, 1_000_000),
        max_columns=_bounded_int("DATAFLOW_MAX_COLUMNS", 100, 1, 1_000),
        max_xlsx_uncompressed_bytes=max_uncompressed_mb * 1024 * 1024,
        max_xlsx_entries=_bounded_int("DATAFLOW_MAX_XLSX_ENTRIES", 5_000, 10, 50_000),
        max_zip_compression_ratio=_bounded_int(
            "DATAFLOW_MAX_ZIP_COMPRESSION_RATIO", 100, 2, 1_000
        ),
        ai_anonymize_default=_env_bool("DATAFLOW_AI_ANONYMIZE_DEFAULT", True),
        ai_timeout_seconds=_bounded_int("DATAFLOW_AI_TIMEOUT_SECONDS", 20, 1, 120),
        ai_max_retries=_bounded_int("DATAFLOW_AI_MAX_RETRIES", 1, 0, 5),
        ai_requests_per_minute=_bounded_int(
            "DATAFLOW_AI_REQUESTS_PER_MINUTE", 5, 1, 60
        ),
        ai_max_output_tokens=_bounded_int("DATAFLOW_AI_MAX_OUTPUT_TOKENS", 700, 64, 4_096),
    )


def get_insight_settings() -> InsightSettings:
    warning = _bounded_float("DATAFLOW_INSIGHT_PRODUCT_SHARE_WARNING", 30, 0, 100)
    critical = _bounded_float("DATAFLOW_INSIGHT_PRODUCT_SHARE_CRITICAL", 45, warning, 100)
    store_critical = _bounded_float("DATAFLOW_INSIGHT_STORE_CRITICAL", 60, 0, 100)
    store_warning = _bounded_float("DATAFLOW_INSIGHT_STORE_WARNING", 80, store_critical, 200)
    return InsightSettings(
        product_share_warning=warning,
        product_share_critical=critical,
        store_performance_warning=store_warning,
        store_performance_critical=store_critical,
        revenue_growth_positive=_bounded_float(
            "DATAFLOW_INSIGHT_REVENUE_GROWTH_POSITIVE", 15, 0, 1_000
        ),
        revenue_growth_negative=_bounded_float(
            "DATAFLOW_INSIGHT_REVENUE_GROWTH_NEGATIVE", -10, -1_000, 0
        ),
        ticket_reference_minimum=_bounded_float(
            "DATAFLOW_INSIGHT_TICKET_REFERENCE_MINIMUM", 100, 0, 1_000_000
        ),
        ticket_growth_positive=_bounded_float(
            "DATAFLOW_INSIGHT_TICKET_GROWTH_POSITIVE", 8, 0, 1_000
        ),
    )


def get_performance_settings() -> PerformanceSettings:
    return PerformanceSettings(
        cache_ttl_seconds=_bounded_int("DATAFLOW_CACHE_TTL_SECONDS", 900, 30, 86_400),
        cache_max_entries=_bounded_int("DATAFLOW_CACHE_MAX_ENTRIES", 8, 2, 64),
        table_page_size=_bounded_int("DATAFLOW_TABLE_PAGE_SIZE", 100, 25, 1_000),
        excel_width_sample_rows=_bounded_int(
            "DATAFLOW_EXCEL_WIDTH_SAMPLE_ROWS", 200, 10, 2_000
        ),
    )

