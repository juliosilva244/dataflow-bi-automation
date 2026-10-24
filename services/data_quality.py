from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from numbers import Number
from typing import Any

import pandas as pd

from domain.normalization import NULL_TEXT_VALUES, coerce_brazilian_numeric
from domain.schema import FIELD_BY_NAME, REQUIRED_FIELDS
from services.anomalies import detect_extreme_monetary_values

CLASSIFICATIONS = ("Erro confirmado", "Alerta", "Informativo", "Não avaliado")


@dataclass(frozen=True)
class QualityFinding:
    row_id: str
    column: str
    category: str
    classification: str
    description: str
    observed_value: str
    rule: str


@dataclass(frozen=True)
class QualityCheck:
    name: str
    status: str
    occurrences: int
    affected_records: int
    criterion: str


@dataclass(frozen=True)
class QualityAudit:
    records_analyzed: int
    columns_analyzed: int
    eligible_cells: int
    filled_cells: int
    completeness: float
    alerted_records: int
    checks: tuple[QualityCheck, ...]
    findings: tuple[QualityFinding, ...]
    completeness_table: pd.DataFrame
    source_scope: str
    limitations: tuple[str, ...]

    @property
    def approved_checks(self) -> int:
        return sum(check.status == "Aprovada" for check in self.checks)

    @property
    def executed_checks(self) -> int:
        return sum(check.status != "Não avaliada" for check in self.checks)

    @property
    def alert_percentage(self) -> float:
        if not self.records_analyzed:
            return 0.0
        return (self.alerted_records / self.records_analyzed) * 100


def _missing_mask(series: pd.Series) -> pd.Series:
    missing = series.isna()
    if pd.api.types.is_object_dtype(series.dtype) or isinstance(series.dtype, pd.StringDtype):
        text = series.astype("string").str.strip().str.casefold()
        missing |= text.isin(NULL_TEXT_VALUES)
    return missing.fillna(True)


def _safe_value(value: Any) -> str:
    if pd.isna(value):
        return "Ausente"
    if isinstance(value, Number) and not isinstance(value, bool):
        try:
            decimal = Decimal(str(value))
            if decimal == decimal.to_integral_value():
                return f"{int(decimal):,}".replace(",", ".")
            formatted = f"{decimal:,.2f}"
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        except (InvalidOperation, ValueError, OverflowError):
            pass
    text = str(value)
    return text if len(text) <= 120 else f"{text[:117]}..."


def _row_id(index: Any) -> str:
    return f"linha:{index}"


def audit_data_quality(
    dataframe: pd.DataFrame,
    *,
    source_scope: str = "Base carregada após validação e normalização",
) -> QualityAudit:
    """Audit available data without mutating it or inferring unavailable raw history."""
    frame = dataframe.copy(deep=True)
    frame.attrs = dataframe.attrs.copy()
    findings: list[QualityFinding] = []
    checks: list[QualityCheck] = []
    limitations = [
        "A auditoria detalha os dados disponíveis após a normalização; valores brutos de linhas "
        "rejeitadas não são preservados pelo pipeline atual.",
        "Valores atípicos são sinais estatísticos para investigação, não evidência de erro ou fraude.",
    ]

    canonical_columns = [column for column in FIELD_BY_NAME if column in frame.columns]
    completeness_rows: list[dict[str, Any]] = []
    eligible_cells = 0
    filled_cells = 0
    required_missing_occurrences = 0

    for column in canonical_columns:
        missing = _missing_mask(frame[column])
        missing_count = int(missing.sum())
        total = len(frame)
        filled = total - missing_count
        eligible_cells += total
        filled_cells += filled
        definition = FIELD_BY_NAME[column]
        completeness_rows.append(
            {
                "Coluna": column,
                "Obrigatória": "Sim" if definition.required else "Não",
                "Preenchidos": filled,
                "Ausentes": missing_count,
                "Completude (%)": round((filled / total) * 100, 2) if total else 0.0,
            }
        )
        if definition.required and missing_count:
            required_missing_occurrences += missing_count
            for index in frame.index[missing]:
                findings.append(
                    QualityFinding(
                        _row_id(index),
                        column,
                        "Valores ausentes",
                        "Erro confirmado",
                        f"Campo obrigatório {column} sem valor utilizável.",
                        _safe_value(frame.at[index, column]),
                        "Campo obrigatório não pode ser nulo, vazio ou marcador textual de ausência.",
                    )
                )

    missing_columns = [column for column in REQUIRED_FIELDS if column not in frame.columns]
    for column in missing_columns:
        completeness_rows.append(
            {
                "Coluna": column,
                "Obrigatória": "Sim",
                "Preenchidos": 0,
                "Ausentes": len(frame),
                "Completude (%)": 0.0,
            }
        )
        findings.append(
            QualityFinding(
                "base",
                column,
                "Schema",
                "Erro confirmado",
                f"Coluna obrigatória {column} não está disponível.",
                "Coluna ausente",
                "Presença definida pelo schema canônico.",
            )
        )

    checks.append(
        QualityCheck(
            "Campos obrigatórios",
            "Aprovada" if not required_missing_occurrences and not missing_columns else "Reprovada",
            required_missing_occurrences + len(missing_columns),
            required_missing_occurrences,
            "Nulos, strings vazias e marcadores textuais de ausência em campos obrigatórios.",
        )
    )

    duplicate_mask = frame.duplicated(keep="first") if not frame.empty else pd.Series(False, index=frame.index)
    duplicate_count = int(duplicate_mask.sum())
    for index in frame.index[duplicate_mask]:
        findings.append(
            QualityFinding(
                _row_id(index),
                "Todas",
                "Duplicidade exata",
                "Erro confirmado",
                "Linha idêntica a uma ocorrência anterior em todas as colunas disponíveis.",
                "Conteúdo omitido",
                "Duplicidade exata de linha; repetições não idênticas não são classificadas.",
            )
        )
    checks.append(
        QualityCheck(
            "Duplicidade exata",
            "Aprovada" if not duplicate_count else "Reprovada",
            duplicate_count,
            duplicate_count,
            "Somente linhas exatamente iguais; nenhuma chave comercial foi presumida.",
        )
    )

    date_invalid = pd.Series(False, index=frame.index)
    if "Data" in frame.columns:
        date_missing = _missing_mask(frame["Data"])
        parsed_dates = pd.to_datetime(frame["Data"], errors="coerce", format="mixed", dayfirst=True)
        date_invalid = parsed_dates.isna() & ~date_missing
        for index in frame.index[date_invalid]:
            findings.append(
                QualityFinding(
                    _row_id(index),
                    "Data",
                    "Datas",
                    "Erro confirmado",
                    "Valor não pôde ser interpretado como data.",
                    _safe_value(frame.at[index, "Data"]),
                    "Conversão de data com coerção segura e preferência dia/mês.",
                )
            )
        checks.append(
            QualityCheck(
                "Datas interpretáveis",
                "Aprovada" if not date_invalid.any() else "Reprovada",
                int(date_invalid.sum()),
                int(date_invalid.sum()),
                "Datas futuras não são classificadas sem regra de negócio.",
            )
        )
    else:
        checks.append(QualityCheck("Datas interpretáveis", "Não avaliada", 0, 0, "Coluna Data indisponível."))

    def audit_numeric(column: str, category: str) -> tuple[pd.Series, pd.Series]:
        if column not in frame.columns:
            checks.append(QualityCheck(category, "Não avaliada", 0, 0, f"Coluna {column} indisponível."))
            return pd.Series(False, index=frame.index), pd.Series(dtype=float)
        missing = _missing_mask(frame[column])
        numeric = coerce_brazilian_numeric(frame[column])
        invalid = numeric.isna() & ~missing
        for index in frame.index[invalid]:
            findings.append(
                QualityFinding(
                    _row_id(index), column, category, "Erro confirmado",
                    "Valor não pôde ser interpretado numericamente.",
                    _safe_value(frame.at[index, column]),
                    "Conversão numérica brasileira centralizada.",
                )
            )
        return invalid, numeric

    money_invalid, money = audit_numeric("Faturamento", "Valores monetários")
    if "Faturamento" in frame.columns:
        negatives = money.lt(0).fillna(False)
        for index in frame.index[negatives]:
            findings.append(
                QualityFinding(
                    _row_id(index), "Faturamento", "Valores monetários", "Alerta",
                    "Valor monetário negativo; pode representar devolução ou ajuste.",
                    _safe_value(frame.at[index, "Faturamento"]),
                    "Valor menor que zero; requer contexto de negócio.",
                )
            )
        checks.append(
            QualityCheck(
                "Valores monetários",
                "Aprovada" if not money_invalid.any() and not negatives.any() else "Com alertas",
                int(money_invalid.sum() + negatives.sum()),
                int((money_invalid | negatives).sum()),
                "Não interpretáveis são erros; negativos são alertas e permanecem nos dados.",
            )
        )

    quantity_invalid, quantity = audit_numeric("Quantidade", "Quantidades")
    if "Quantidade" in frame.columns:
        non_positive = quantity.le(0).fillna(False)
        for index in frame.index[non_positive]:
            value = quantity.at[index]
            description = "Quantidade igual a zero." if value == 0 else "Quantidade negativa."
            findings.append(
                QualityFinding(
                    _row_id(index), "Quantidade", "Quantidades", "Alerta", description,
                    _safe_value(frame.at[index, "Quantidade"]),
                    "Quantidade menor ou igual a zero; exige contexto operacional.",
                )
            )
        checks.append(
            QualityCheck(
                "Quantidades",
                "Aprovada" if not quantity_invalid.any() and not non_positive.any() else "Com alertas",
                int(quantity_invalid.sum() + non_positive.sum()),
                int((quantity_invalid | non_positive).sum()),
                "Não interpretáveis são erros; zero e negativos são alertas.",
            )
        )

    identifier_occurrences = 0
    for column in ("Loja", "Produto"):
        if column not in frame.columns:
            continue
        mask = _missing_mask(frame[column])
        identifier_occurrences += int(mask.sum())
    checks.append(
        QualityCheck(
            "Identificadores essenciais",
            "Aprovada" if not identifier_occurrences else "Reprovada",
            identifier_occurrences,
            identifier_occurrences,
            "Loja e Produto devem estar identificados; nenhum identificador é inventado.",
        )
    )

    anomalies = detect_extreme_monetary_values(frame)
    for row in anomalies.itertuples(index=False):
        findings.append(
            QualityFinding(
                _row_id(row.indice), "Faturamento", "Valores extremos", "Alerta",
                "Valor monetário acima do limiar conservador; permanece nos cálculos.",
                _safe_value(row.valor), str(row.criterio),
            )
        )
    checks.append(
        QualityCheck(
            "Valores monetários extremos",
            "Com alertas" if len(anomalies) else "Aprovada",
            len(anomalies), len(anomalies),
            "Acima do maior limite entre 10×IQR e 1.000×mediana; não comprova erro.",
        )
    )

    quality_report = dataframe.attrs.get("quality_report")
    if quality_report is None:
        checks.append(
            QualityCheck(
                "Rastreabilidade da ingestão", "Não avaliada", 0, 0,
                "Relatório histórico de normalização indisponível.",
            )
        )
    else:
        discarded = int(getattr(quality_report, "discarded_records", 0))
        checks.append(
            QualityCheck(
                "Rastreabilidade da ingestão",
                "Com alertas" if discarded else "Aprovada",
                discarded,
                discarded,
                "Resumo de recebidos, válidos, descartados e duplicados preservado pela carga; "
                "valores brutos rejeitados não são retidos.",
            )
        )

    affected_rows = {
        finding.row_id for finding in findings if finding.row_id.startswith("linha:")
    }
    completeness = (filled_cells / eligible_cells) * 100 if eligible_cells else 0.0
    completeness_table = pd.DataFrame(completeness_rows)
    return QualityAudit(
        records_analyzed=len(frame),
        columns_analyzed=len(canonical_columns),
        eligible_cells=eligible_cells,
        filled_cells=filled_cells,
        completeness=round(completeness, 2),
        alerted_records=len(affected_rows),
        checks=tuple(checks),
        findings=tuple(findings),
        completeness_table=completeness_table,
        source_scope=source_scope,
        limitations=tuple(limitations),
    )


def findings_dataframe(audit: QualityAudit) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Linha técnica": item.row_id,
                "Coluna": item.column,
                "Categoria": item.category,
                "Classificação": item.classification,
                "Descrição": item.description,
                "Valor observado": item.observed_value,
                "Regra aplicada": item.rule,
            }
            for item in audit.findings
        ]
    )


def filter_findings(
    findings: pd.DataFrame,
    *,
    category: str = "Todas",
    classification: str = "Todas",
    query: str = "",
) -> pd.DataFrame:
    filtered = findings.copy()
    if category != "Todas" and not filtered.empty:
        filtered = filtered[filtered["Categoria"] == category]
    if classification != "Todas" and not filtered.empty:
        filtered = filtered[filtered["Classificação"] == classification]
    if query.strip() and not filtered.empty:
        searchable = filtered.astype("string").agg(" ".join, axis=1)
        filtered = filtered[searchable.str.contains(query.strip(), case=False, na=False, regex=False)]
    return filtered.reset_index(drop=True)


def paginate_findings(findings: pd.DataFrame, page: int, page_size: int) -> tuple[pd.DataFrame, int, int]:
    safe_size = max(int(page_size), 1)
    total_pages = max((len(findings) + safe_size - 1) // safe_size, 1)
    safe_page = min(max(int(page), 1), total_pages)
    start = (safe_page - 1) * safe_size
    return findings.iloc[start : start + safe_size].copy(), total_pages, safe_page
