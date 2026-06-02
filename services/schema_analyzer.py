from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SemanticColumn:
    name: str
    role: str
    confidence: float
    dtype: str
    unique_count: int
    unique_ratio: float
    null_ratio: float
    sample_values: list[str]


@dataclass(frozen=True)
class SchemaAnalysis:
    metric_column: str | None
    date_column: str | None
    primary_dimension: str | None
    secondary_dimension: str | None
    category_dimension: str | None
    secondary_metrics: list[str]
    dimension_columns: list[str]
    numeric_columns: list[str]
    date_columns: list[str]
    text_columns: list[str]
    domain: str
    confidence: float
    metric_confidence: float
    date_confidence: float
    primary_dimension_confidence: float
    secondary_dimension_confidence: float
    category_dimension_confidence: float
    columns: list[SemanticColumn]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["columns"] = [asdict(column) for column in self.columns]
        return data


DOMAIN_KEYWORDS = {
    "vendas": [
        "venda", "vendas", "faturamento", "receita", "produto", "loja",
        "pedido", "cliente", "sku", "ticket", "preco", "preço", "quantidade",
    ],
    "financeiro": [
        "valor", "custo", "despesa", "receita", "lucro", "conta",
        "centro de custo", "pagamento", "saldo", "financeiro",
    ],
    "rh": [
        "funcionario", "funcionário", "colaborador", "departamento", "cargo",
        "salario", "salário", "admissao", "admissão", "rh",
    ],
    "estoque": [
        "estoque", "produto", "sku", "quantidade", "qtd", "entrada",
        "saida", "saída", "armazem", "armazém",
    ],
    "projetos": [
        "projeto", "tarefa", "status", "responsavel", "responsável",
        "prazo", "horas", "sprint", "backlog",
    ],
    "crm": [
        "cliente", "lead", "contato", "empresa", "oportunidade",
        "pipeline", "negocio", "negócio", "vendedor",
    ],
}


PRIMARY_METRIC_KEYWORDS = [
    "faturamento", "receita", "valor total", "valor_total", "total venda",
    "total_venda", "venda total", "venda_total", "total", "vendas",
    "sales", "revenue", "amount", "valor",
]

SECONDARY_METRIC_KEYWORDS = [
    "lucro", "margem", "custo", "despesa", "saldo", "salario", "salário",
    "horas", "volume", "quantidade", "qtd",
]

LOW_PRIORITY_METRIC_KEYWORDS = [
    "preco unitario", "preço unitário", "preco_unitario", "valor unitario",
    "valor_unitario", "unit price", "price", "preco", "preço",
]

DATE_KEYWORDS = [
    "data", "date", "dt", "dia", "mes", "mês", "ano", "periodo",
    "período", "emissao", "emissão", "admissao", "admissão",
    "vencimento", "prazo", "created", "updated",
]

DIMENSION_KEYWORDS = [
    "loja", "produto", "categoria", "cliente", "fornecedor", "departamento",
    "centro", "conta", "cidade", "estado", "regiao", "região", "funcionario",
    "funcionário", "colaborador", "cargo", "projeto", "status",
    "responsavel", "responsável", "vendedor", "canal", "segmento", "grupo",
    "tipo",
]

CATEGORY_KEYWORDS = [
    "categoria", "category", "grupo", "group", "segmento", "segment",
    "classe", "class", "tipo", "type", "familia", "família", "family",
    "linha", "line", "departamento", "department", "status", "canal",
]

ID_KEYWORDS = [
    "id", "codigo", "código", "cod", "uuid", "chave", "numero", "número",
]


def normalize_text(value: object) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[_\-./]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
    )

    return pd.to_numeric(cleaned, errors="coerce")


def parse_date_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def get_sample_values(series: pd.Series, limit: int = 5) -> list[str]:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""].drop_duplicates().head(limit).tolist()
    return values


def confidence_from_score(score: float) -> float:
    return round(min(max(score / 100, 0), 1), 3)


def _keyword_score(normalized_name: str) -> float:
    score = 0.0

    for keyword in PRIMARY_METRIC_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 70
        elif normalized_keyword in normalized_name:
            score += 45

    for keyword in SECONDARY_METRIC_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 35
        elif normalized_keyword in normalized_name:
            score += 22

    for keyword in LOW_PRIORITY_METRIC_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score -= 28
        elif normalized_keyword in normalized_name:
            score -= 18

    return score


def score_numeric_column(df: pd.DataFrame, column: str) -> tuple[float, pd.Series]:
    series = clean_numeric_series(df[column])
    valid_ratio = float(series.notna().mean())
    non_zero_ratio = float((series.fillna(0) != 0).mean())
    unique_count = int(series.nunique(dropna=True))
    unique_ratio = unique_count / max(len(df), 1)
    normalized_name = normalize_text(column)

    score = 0.0

    if valid_ratio >= 0.65:
        score += valid_ratio * 40

    if non_zero_ratio >= 0.25:
        score += non_zero_ratio * 12

    score += _keyword_score(normalized_name)

    if any(keyword in normalized_name for keyword in ["id", "codigo", "cod", "numero", "uuid"]):
        score -= 45

    if unique_count <= 2:
        score -= 20

    if unique_ratio > 0.95 and not any(
        keyword in normalized_name
        for keyword in ["faturamento", "receita", "valor", "total", "venda", "revenue", "amount"]
    ):
        score -= 18

    return max(score, 0.0), series


def score_date_column(df: pd.DataFrame, column: str) -> tuple[float, pd.Series]:
    normalized_name = normalize_text(column)

    # Evita classificar números puros como datas por acidente.
    # Pandas consegue converter inteiros para timestamps de 1970, o que gerava falsos positivos
    # em colunas como Quantidade, Preço Unitário e Faturamento.
    has_date_keyword = any(normalize_text(keyword) in normalized_name for keyword in DATE_KEYWORDS)
    if pd.api.types.is_numeric_dtype(df[column]) and not has_date_keyword:
        empty_series = pd.Series(pd.NaT, index=df.index)
        return 0.0, empty_series

    series = parse_date_series(df[column])
    valid_ratio = float(series.notna().mean())

    score = 0.0

    if valid_ratio >= 0.55:
        score += valid_ratio * 55

    for keyword in DATE_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 35
        elif normalized_keyword in normalized_name:
            score += 15

    if series.nunique(dropna=True) <= 1:
        score -= 15

    return max(score, 0.0), series


def score_dimension_column(df: pd.DataFrame, column: str) -> float:
    series = df[column]
    total_rows = max(len(df), 1)
    unique_count = int(series.dropna().nunique())
    unique_ratio = unique_count / total_rows
    null_ratio = float(series.isna().mean())
    normalized_name = normalize_text(column)

    score = 0.0

    if series.dtype == "object" or pd.api.types.is_string_dtype(series):
        score += 20

    if 2 <= unique_count <= max(2, total_rows * 0.65):
        score += 30

    if 0.01 <= unique_ratio <= 0.65:
        score += 20

    if null_ratio <= 0.35:
        score += 10

    for keyword in DIMENSION_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 35
        elif normalized_keyword in normalized_name:
            score += 15

    for keyword in ID_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name or normalized_keyword in normalized_name:
            score -= 20

    if unique_ratio > 0.9:
        score -= 35

    return max(score, 0.0)


def score_category_column(df: pd.DataFrame, column: str) -> float:
    base_score = score_dimension_column(df, column)
    normalized_name = normalize_text(column)

    score = base_score

    for keyword in CATEGORY_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 45
        elif normalized_keyword in normalized_name:
            score += 25

    unique_ratio = df[column].dropna().nunique() / max(len(df), 1)

    if unique_ratio > 0.75:
        score -= 25

    return max(score, 0.0)


def classify_domain(df: pd.DataFrame) -> tuple[str, float]:
    joined_columns = " ".join(normalize_text(column) for column in df.columns)
    scores: dict[str, float] = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0.0

        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword in joined_columns:
                score += 1.0

        scores[domain] = score

    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]
    total_score = sum(scores.values())

    if best_score <= 0:
        return "generico", 0.3

    confidence = best_score / total_score if total_score > 0 else 0.3
    return best_domain, round(float(confidence), 3)


def infer_column_dtype(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    numeric_ratio = clean_numeric_series(series).notna().mean()

    if pd.api.types.is_numeric_dtype(series) and numeric_ratio >= 0.65:
        return "numeric"

    date_ratio = parse_date_series(series).notna().mean()

    if date_ratio >= 0.65:
        return "date"

    if numeric_ratio >= 0.65:
        return "numeric"

    return "text"


def choose_metric_column(numeric_scores: list[tuple[float, str]]) -> tuple[str | None, float]:
    if not numeric_scores:
        return None, 0.0

    valid_scores = [(score, column) for score, column in numeric_scores if score >= 35]

    if not valid_scores:
        return None, 0.0

    exact_priority = [
        "faturamento", "receita", "valor total", "total", "vendas",
        "valor", "revenue", "amount",
    ]

    for priority in exact_priority:
        normalized_priority = normalize_text(priority)

        for score, column in valid_scores:
            normalized_column = normalize_text(column)
            if normalized_column == normalized_priority:
                return column, confidence_from_score(score)

    contains_priority = [
        "faturamento", "receita", "valor total", "total", "vendas",
        "revenue", "amount",
    ]

    for priority in contains_priority:
        normalized_priority = normalize_text(priority)

        for score, column in valid_scores:
            normalized_column = normalize_text(column)
            if normalized_priority in normalized_column:
                return column, confidence_from_score(score)

    valid_scores.sort(reverse=True)
    score, column = valid_scores[0]
    return column, confidence_from_score(score)


def choose_top_column(scores: list[tuple[float, str]], min_score: float = 35) -> tuple[str | None, float]:
    valid_scores = [(score, column) for score, column in scores if score >= min_score]

    if not valid_scores:
        return None, 0.0

    valid_scores.sort(reverse=True)
    score, column = valid_scores[0]
    return column, confidence_from_score(score)


def choose_secondary_metrics(
    numeric_scores: list[tuple[float, str]],
    metric_column: str | None,
    limit: int = 4,
) -> list[str]:
    metrics = []

    for score, column in sorted(numeric_scores, reverse=True):
        if column == metric_column:
            continue

        if score < 35:
            continue

        metrics.append(column)

        if len(metrics) >= limit:
            break

    return metrics


def analyze_schema(df: pd.DataFrame) -> SchemaAnalysis:
    if df is None or df.empty:
        return SchemaAnalysis(
            metric_column=None,
            date_column=None,
            primary_dimension=None,
            secondary_dimension=None,
            category_dimension=None,
            secondary_metrics=[],
            dimension_columns=[],
            numeric_columns=[],
            date_columns=[],
            text_columns=[],
            domain="vazio",
            confidence=0.0,
            metric_confidence=0.0,
            date_confidence=0.0,
            primary_dimension_confidence=0.0,
            secondary_dimension_confidence=0.0,
            category_dimension_confidence=0.0,
            columns=[],
            warnings=["A base está vazia ou não foi carregada."],
        )

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    numeric_scores: list[tuple[float, str]] = []
    date_scores: list[tuple[float, str]] = []
    dimension_scores: list[tuple[float, str]] = []
    category_scores: list[tuple[float, str]] = []

    semantic_columns: list[SemanticColumn] = []
    numeric_columns: list[str] = []
    date_columns: list[str] = []
    text_columns: list[str] = []

    for column in df.columns:
        dtype = infer_column_dtype(df[column])
        unique_count = int(df[column].dropna().nunique())
        unique_ratio = float(unique_count / max(len(df), 1))
        null_ratio = float(df[column].isna().mean())

        numeric_score, _ = score_numeric_column(df, column)
        date_score, _ = score_date_column(df, column)
        dimension_score = score_dimension_column(df, column)
        category_score = score_category_column(df, column)

        numeric_scores.append((numeric_score, column))
        date_scores.append((date_score, column))
        dimension_scores.append((dimension_score, column))
        category_scores.append((category_score, column))

        if dtype == "numeric":
            numeric_columns.append(column)
        elif dtype == "date":
            date_columns.append(column)
        else:
            text_columns.append(column)

        best_role = max(
            [
                ("metric", numeric_score),
                ("date", date_score),
                ("dimension", dimension_score),
                ("category", category_score),
            ],
            key=lambda item: item[1],
        )

        semantic_columns.append(
            SemanticColumn(
                name=column,
                role=best_role[0],
                confidence=confidence_from_score(best_role[1]),
                dtype=dtype,
                unique_count=unique_count,
                unique_ratio=round(unique_ratio, 3),
                null_ratio=round(null_ratio, 3),
                sample_values=get_sample_values(df[column]),
            )
        )

    numeric_scores.sort(reverse=True)
    date_scores.sort(reverse=True)
    dimension_scores.sort(reverse=True)
    category_scores.sort(reverse=True)

    metric_column, metric_confidence = choose_metric_column(numeric_scores)
    date_column, date_confidence = choose_top_column(date_scores, min_score=35)

    valid_dimensions = [
        column
        for score, column in dimension_scores
        if score >= 35 and column not in [metric_column, date_column]
    ]

    primary_dimension = valid_dimensions[0] if len(valid_dimensions) >= 1 else None
    secondary_dimension = valid_dimensions[1] if len(valid_dimensions) >= 2 else None

    primary_dimension_confidence = 0.0
    secondary_dimension_confidence = 0.0

    for score, column in dimension_scores:
        if column == primary_dimension:
            primary_dimension_confidence = confidence_from_score(score)

        if column == secondary_dimension:
            secondary_dimension_confidence = confidence_from_score(score)

    category_candidates = [
        (score, column)
        for score, column in category_scores
        if score >= 45 and column not in [metric_column, date_column]
    ]

    if category_candidates:
        category_candidates.sort(reverse=True)
        category_score, category_dimension = category_candidates[0]
        category_dimension_confidence = confidence_from_score(category_score)
    else:
        category_dimension = None
        category_dimension_confidence = 0.0

    secondary_metrics = choose_secondary_metrics(numeric_scores, metric_column)

    domain, domain_confidence = classify_domain(df)

    warnings: list[str] = []

    if not metric_column:
        warnings.append("Nenhuma métrica principal foi detectada com confiança suficiente.")

    if not date_column:
        warnings.append("Nenhuma coluna de data foi detectada com confiança suficiente.")

    if not primary_dimension:
        warnings.append("Nenhuma dimensão principal foi detectada com confiança suficiente.")

    if metric_confidence and metric_confidence < 0.6:
        warnings.append("A métrica principal foi detectada com baixa confiança.")

    if primary_dimension_confidence and primary_dimension_confidence < 0.6:
        warnings.append("A dimensão principal foi detectada com baixa confiança.")

    confidence_parts = [
        1.0 if metric_column else 0.0,
        1.0 if date_column else 0.0,
        1.0 if primary_dimension else 0.0,
        domain_confidence,
        metric_confidence,
        primary_dimension_confidence,
    ]

    confidence = round(sum(confidence_parts) / len(confidence_parts), 3)

    return SchemaAnalysis(
        metric_column=metric_column,
        date_column=date_column,
        primary_dimension=primary_dimension,
        secondary_dimension=secondary_dimension,
        category_dimension=category_dimension,
        secondary_metrics=secondary_metrics,
        dimension_columns=valid_dimensions,
        numeric_columns=numeric_columns,
        date_columns=date_columns,
        text_columns=text_columns,
        domain=domain,
        confidence=confidence,
        metric_confidence=metric_confidence,
        date_confidence=date_confidence,
        primary_dimension_confidence=primary_dimension_confidence,
        secondary_dimension_confidence=secondary_dimension_confidence,
        category_dimension_confidence=category_dimension_confidence,
        columns=semantic_columns,
        warnings=warnings,
    )


def analisar_schema(df: pd.DataFrame) -> dict[str, Any]:
    return analyze_schema(df).to_dict()


def get_primary_metric(df: pd.DataFrame) -> str | None:
    return analyze_schema(df).metric_column


def get_primary_dimension(df: pd.DataFrame) -> str | None:
    return analyze_schema(df).primary_dimension


def get_date_column(df: pd.DataFrame) -> str | None:
    return analyze_schema(df).date_column