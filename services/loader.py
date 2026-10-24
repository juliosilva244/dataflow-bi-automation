import time
from pathlib import Path

import pandas as pd

from domain.normalization import (
    NULL_TEXT_VALUES,
    coerce_brazilian_numeric,
    normalize_dataframe,
    parse_brazilian_number,
)
from domain.schema import REQUIRED_FIELDS, resolve_column_name
from services.errors import DataFlowError
from services.logging_config import get_logger
from services.performance import SessionScopedCache, TelemetryCollector, content_signature
from services.settings import get_security_settings
from services.upload_security import read_limited_bytes, read_validated_content

logger = get_logger(__name__)
ROLLING_CALENDAR_DAYS = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data/raw/vendas.xlsx"
DEMO_DATA_PATH = PROJECT_ROOT / "data/demo/vendas_demo.csv"

__all__ = [
    "NULL_TEXT_VALUES",
    "aplicar_filtro_periodo",
    "carregar_dados",
    "coerce_brazilian_numeric",
    "ler_arquivo_upload",
    "limpar_dados",
    "parse_brazilian_number",
    "validar_colunas",
]

COLUNAS_OBRIGATORIAS = list(REQUIRED_FIELDS)


def validar_colunas(df):
    detected = {resolve_column_name(column) for column in df.columns}
    return [column for column in COLUNAS_OBRIGATORIAS if column not in detected]


def ler_arquivo_upload(arquivo_upload):
    settings = get_security_settings()
    content = read_limited_bytes(arquivo_upload, settings)
    return read_validated_content(content, str(getattr(arquivo_upload, "name", "")), settings)


def limpar_dados(df):
    try:
        result = normalize_dataframe(df)
    except ValueError as error:
        return None, str(error)

    if result.quality.missing_fields:
        return None, "Colunas obrigatórias ausentes: " + ", ".join(
            result.quality.missing_fields
        )

    if result.dataframe is None or result.dataframe.empty:
        return None, "A base não possui dados válidos após a limpeza."

    return result.dataframe, None


def aplicar_filtro_periodo(df, periodo):
    if periodo == "Tudo":
        return df

    data_maxima = df["Data"].max()

    days = ROLLING_CALENDAR_DAYS.get(periodo)
    if days:
        if pd.isna(data_maxima):
            return df.iloc[0:0]
        final_day = data_maxima.normalize()
        start = final_day - pd.Timedelta(days=days - 1)
        return df[(df["Data"] >= start) & (df["Data"] < final_day + pd.Timedelta(days=1))]

    if periodo == "Ano atual":
        ano_atual = data_maxima.year
        return df[df["Data"].dt.year == ano_atual]

    return df


def carregar_dados(
    arquivo_upload=None,
    periodo="Tudo",
    cache: SessionScopedCache | None = None,
    telemetry: TelemetryCollector | None = None,
):
    telemetry = telemetry or TelemetryCollector()
    load_started = time.perf_counter()
    try:
        settings = get_security_settings()
        if arquivo_upload is not None:
            safe_filename = Path(str(arquivo_upload.name)).name
            origem = f"Arquivo enviado: {safe_filename}"
            filename = safe_filename
            content = read_limited_bytes(arquivo_upload, settings)
        else:
            source_path = DEFAULT_DATA_PATH
            origem = "Arquivo padrão do sistema"
            try:
                default_file = source_path.open("rb")
            except FileNotFoundError:
                # Only absence selects the demo; invalid/inaccessible local data
                # must still report its error instead of silently changing source.
                source_path = DEMO_DATA_PATH
                origem = "Demonstração — dados fictícios"
                default_file = source_path.open("rb")
            with default_file:
                content = read_limited_bytes(default_file, settings)
            filename = source_path.name

        signature = content_signature(content)
        limits = (
            settings.max_upload_bytes,
            settings.max_rows,
            settings.max_columns,
            settings.max_xlsx_uncompressed_bytes,
        )
        revision = "v4-calendar-days" if periodo in ROLLING_CALENDAR_DAYS else "v3-iso-dates"
        cache_key = f"prepared:{revision}:{signature}:{Path(filename).suffix.casefold()}:{periodo}:{limits}"
        cached = cache.get(cache_key) if cache is not None else None
        if cached is not None:
            df = cached.copy(deep=False)
            df.attrs = cached.attrs.copy()
            telemetry.record(
                "carregamento",
                time.perf_counter() - load_started,
                rows=len(cached),
                cache_hit=True,
            )
            return df, origem, None

        raw_df = read_validated_content(content, filename, settings)
        telemetry.record(
            "carregamento",
            time.perf_counter() - load_started,
            rows=len(raw_df),
            cache_hit=False,
        )

        with telemetry.measure("normalizacao", rows=len(raw_df), cache_hit=False):
            df, erro_limpeza = limpar_dados(raw_df)

        if erro_limpeza:
            return None, origem, erro_limpeza

        # O filtro temporal é aplicado uma única vez, usando a data máxima da
        # própria base como referência. Isso mantém bases históricas utilizáveis.
        quality_report = df.attrs.get("quality_report")
        df = aplicar_filtro_periodo(df, periodo)

        if df.empty:
            return None, origem, "Não existem dados para o período selecionado."

        df = df.sort_values("Data").reset_index(drop=True)
        if quality_report is not None:
            df.attrs["quality_report"] = quality_report
        df.attrs["dataset_signature"] = signature

        if cache is not None:
            cache.set(cache_key, df)

        return df, origem, None

    except FileNotFoundError as error:
        telemetry.record("carregamento", time.perf_counter() - load_started, failed=True)
        logger.warning("Arquivo de dados ausente tipo=%s", type(error).__name__)
        return (
            None,
            None,
            "Base operacional e base de demonstração não encontradas. "
            "Envie um arquivo CSV ou XLSX pelo menu Dados.",
        )

    except DataFlowError as error:
        telemetry.record("carregamento", time.perf_counter() - load_started, failed=True)
        logger.warning("Upload rejeitado codigo=%s tipo=%s", error.code, type(error).__name__)
        return None, None, f"{error.public_message} (código: {error.code})"

    except Exception as error:
        telemetry.record("carregamento", time.perf_counter() - load_started, failed=True)
        logger.exception("Falha interna ao carregar dados tipo=%s", type(error).__name__)
        return (
            None,
            None,
            "Não foi possível processar o arquivo. Verifique o formato e tente novamente. "
            "(código: LOAD_INTERNAL)",
        )
