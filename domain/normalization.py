from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from domain.models import DataQualityReport
from domain.schema import CANONICAL_FIELDS, REQUIRED_FIELDS, resolve_column_name

NULL_TEXT_VALUES = {"", "-", "n/a", "na", "nan", "none", "null"}


@dataclass(frozen=True)
class NormalizationResult:
    dataframe: pd.DataFrame | None
    quality: DataQualityReport


def parse_brazilian_number(value):
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if text.casefold() in NULL_TEXT_VALUES:
        return float("nan")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = text.replace("R$", "").replace("r$", "").replace("\u00a0", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    try:
        number = float(text)
    except ValueError:
        return float("nan")
    return -number if negative else number


def coerce_brazilian_numeric(series: pd.Series) -> pd.Series:
    return series.map(parse_brazilian_number)


def _canonicalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    rename_map: dict[object, str] = {}
    detected = {field.name: None for field in CANONICAL_FIELDS}
    claimed: dict[str, object] = {}

    for column in df.columns:
        canonical = resolve_column_name(column)
        if not canonical:
            rename_map[column] = str(column).strip()
            continue
        if canonical in claimed:
            raise ValueError(
                f"As colunas '{claimed[canonical]}' e '{column}' representam o mesmo campo "
                f"canônico '{canonical}'."
            )
        claimed[canonical] = column
        detected[canonical] = str(column)
        rename_map[column] = canonical

    return df.rename(columns=rename_map).copy(), detected


def normalize_dataframe(df: pd.DataFrame) -> NormalizationResult:
    canonical, detected = _canonicalize_columns(df)
    missing = tuple(field for field in REQUIRED_FIELDS if field not in canonical.columns)
    present_required = len(REQUIRED_FIELDS) - len(missing)
    score = round((present_required / len(REQUIRED_FIELDS)) * 100, 1)

    if missing:
        quality = DataQualityReport(
            received_records=len(canonical),
            valid_records=0,
            discarded_records=len(canonical),
            duplicate_records=0,
            detected_fields=detected,
            missing_fields=missing,
            rejection_reasons={"campos_obrigatorios_ausentes": len(canonical)},
            schema_score=score,
        )
        return NormalizationResult(None, quality)

    original = canonical.copy()
    dates = canonical["Data"]
    iso_dates = dates.astype("string").str.match(r"^\d{4}-\d{2}-\d{2}(?:[T ].*)?$", na=False)
    parsed = pd.to_datetime(dates, errors="coerce", format="mixed", dayfirst=True)
    # ISO YYYY-MM-DD has an explicit order; dayfirst=True can swap its month/day.
    if iso_dates.any():
        parsed.loc[iso_dates] = pd.to_datetime(dates.loc[iso_dates], errors="coerce", format="ISO8601")
    canonical["Data"] = parsed
    canonical["Quantidade"] = coerce_brazilian_numeric(canonical["Quantidade"])
    canonical["Faturamento"] = coerce_brazilian_numeric(canonical["Faturamento"])

    for column in ("Loja", "Produto", "Categoria", "Pedido"):
        if column in canonical.columns:
            canonical[column] = canonical[column].astype("string").str.strip()
    for column in ("Lucro", "Preço Unitário"):
        if column in canonical.columns:
            canonical[column] = coerce_brazilian_numeric(canonical[column])

    invalid_masks = {
        "data_ausente_ou_invalida": canonical["Data"].isna(),
        "loja_ausente_ou_invalida": canonical["Loja"].isna()
        | canonical["Loja"].str.casefold().isin(NULL_TEXT_VALUES),
        "produto_ausente_ou_invalido": canonical["Produto"].isna()
        | canonical["Produto"].str.casefold().isin(NULL_TEXT_VALUES),
        "quantidade_ausente_ou_invalida": canonical["Quantidade"].isna()
        | (canonical["Quantidade"] <= 0),
        "faturamento_ausente_ou_invalido": canonical["Faturamento"].isna()
        | (canonical["Faturamento"] < 0),
    }
    invalid_any = pd.Series(False, index=canonical.index)
    reasons = {}
    for reason, mask in invalid_masks.items():
        count = int(mask.sum())
        if count:
            reasons[reason] = count
        invalid_any |= mask

    valid = canonical.loc[~invalid_any].copy()
    duplicate_mask = valid.duplicated(keep="first")
    duplicate_count = int(duplicate_mask.sum())
    if duplicate_count:
        reasons["registro_duplicado"] = duplicate_count
    valid = valid.loc[~duplicate_mask].copy()

    discarded = int(invalid_any.sum()) + duplicate_count
    quality = DataQualityReport(
        received_records=len(original),
        valid_records=len(valid),
        discarded_records=discarded,
        duplicate_records=duplicate_count,
        detected_fields=detected,
        missing_fields=(),
        rejection_reasons=reasons,
        schema_score=score,
    )
    valid.attrs["quality_report"] = quality
    return NormalizationResult(valid, quality)

