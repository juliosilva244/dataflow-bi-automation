from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import tracemalloc
import zipfile

import pandas as pd

from services.exporter import gerar_excel
from services.metrics_engine import construir_analytics_state
from services.performance import (
    SessionScopedCache,
    TelemetryCollector,
    get_cached_analytics,
    get_cached_export,
)

SIZES = {"small": 1_000, "medium": 10_000, "large": 50_000}
KPI_FIELDS = ("faturamento_total", "ticket_medio", "total_pedidos", "quantidade_total")


def synthetic_dataframe(rows: int) -> pd.DataFrame:
    index = pd.RangeIndex(rows)
    return pd.DataFrame(
        {
            "Data": pd.Timestamp("2024-01-01") + pd.to_timedelta(index % 730, unit="D"),
            "Loja": [f"Loja {value % 25:02d}" for value in index],
            "Produto": [f"Produto {value % 250:03d}" for value in index],
            "Categoria": [f"Categoria {value % 12:02d}" for value in index],
            "Pedido": [f"P-{value:08d}" for value in index],
            "Quantidade": (index % 9) + 1,
            "Faturamento": ((index % 1_000) + 100).astype(float),
        }
    )


def measured(callable_):
    tracemalloc.start()
    started = time.perf_counter()
    result = callable_()
    elapsed_ms = (time.perf_counter() - started) * 1_000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, round(elapsed_ms, 3), round(peak / 1024 / 1024, 3)


def semantic_xlsx_digest(content: bytes) -> str:
    """Compare workbook contents while ignoring volatile creation metadata."""
    digest = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for name in sorted(archive.namelist()):
            if name == "docProps/core.xml":
                continue
            digest.update(name.encode())
            digest.update(archive.read(name))
    return digest.hexdigest()


def run_case(label: str, rows: int, include_export: bool = True) -> dict:
    df = synthetic_dataframe(rows)
    direct, direct_ms, direct_peak = measured(lambda: construir_analytics_state(df))
    cache = SessionScopedCache(max_entries=8, ttl_seconds=900)
    telemetry = TelemetryCollector()
    cold, cold_ms, cold_peak = measured(
        lambda: get_cached_analytics(df, cache, telemetry, construir_analytics_state)
    )
    warm, warm_ms, warm_peak = measured(
        lambda: get_cached_analytics(df, cache, telemetry, construir_analytics_state)
    )
    cold_state = cold[0]
    warm_state = warm[0]
    kpis_preserved = all(
        direct[field] == cold_state[field] == warm_state[field] for field in KPI_FIELDS
    )
    result = {
        "dataset": label,
        "rows": rows,
        "analytics_direct_ms": direct_ms,
        "analytics_direct_peak_mib": direct_peak,
        "analytics_cache_cold_ms": cold_ms,
        "analytics_cache_cold_peak_mib": cold_peak,
        "analytics_cache_warm_ms": warm_ms,
        "analytics_cache_warm_peak_mib": warm_peak,
        "analytics_warm_speedup": round(direct_ms / warm_ms, 2) if warm_ms else None,
        "kpis_preserved": kpis_preserved,
    }
    if include_export:
        export_cache = SessionScopedCache(max_entries=2, ttl_seconds=900)
        direct_export, export_direct_ms, export_direct_peak = measured(
            lambda: gerar_excel(df, direct).getvalue()
        )
        cached_export, export_cold_ms, export_cold_peak = measured(
            lambda: get_cached_export(
                df, direct, f"benchmark:{label}", export_cache, telemetry, gerar_excel
            )
        )
        warm_export, export_warm_ms, export_warm_peak = measured(
            lambda: get_cached_export(
                df, direct, f"benchmark:{label}", export_cache, telemetry, gerar_excel
            )
        )
        result.update(
            {
                "export_direct_ms": export_direct_ms,
                "export_direct_peak_mib": export_direct_peak,
                "export_cache_cold_ms": export_cold_ms,
                "export_cache_cold_peak_mib": export_cold_peak,
                "export_cache_warm_ms": export_warm_ms,
                "export_cache_warm_peak_mib": export_warm_peak,
                "export_warm_speedup": (
                    round(export_direct_ms / export_warm_ms, 2) if export_warm_ms else None
                ),
                "export_preserved": (
                    semantic_xlsx_digest(direct_export)
                    == semantic_xlsx_digest(cached_export[0])
                    == semantic_xlsx_digest(warm_export[0])
                ),
                "export_bytes": len(direct_export),
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", choices=SIZES, default=list(SIZES))
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args()
    results = [
        run_case(name, SIZES[name], include_export=not args.skip_export)
        for name in args.sizes
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
