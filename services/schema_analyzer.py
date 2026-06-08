from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
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
    "vendas": ["venda", "vendas", "faturamento", "receita", "produto", "loja", "pedido", "sku", "ticket", "preco", "preço", "quantidade"],
    "financeiro": ["valor", "custo", "despesa", "receita", "lucro", "conta", "centro de custo", "pagamento", "saldo", "financeiro", "boleto", "nota fiscal"],
    "rh": ["funcionario", "funcionário", "colaborador", "departamento", "cargo", "salario", "salário", "admissao", "admissão", "rh", "turnover"],
    "estoque": ["estoque", "produto", "sku", "quantidade", "qtd", "entrada", "saida", "saída", "armazem", "armazém", "lote"],
    "projetos": ["projeto", "tarefa", "status", "responsavel", "responsável", "prazo", "horas", "sprint", "backlog", "entrega"],
    "crm": ["cliente", "lead", "contato", "empresa", "oportunidade", "pipeline", "negocio", "negócio", "vendedor", "status"],
}

PRIMARY_METRIC_KEYWORDS = [
    "faturamento", "receita", "valor total", "valor_total", "total venda", "total_venda", "venda total", "venda_total",
    "total", "vendas", "sales", "revenue", "amount", "valor", "custo", "despesa", "lucro", "saldo", "horas", "salario", "salário", "oportunidade", "pipeline", "deal",
]

SECONDARY_METRIC_KEYWORDS = ["quantidade", "qtd", "qtde", "volume", "ticket", "margem", "percentual", "taxa", "dias", "unidades"]
LOW_PRIORITY_METRIC_KEYWORDS = ["id", "codigo", "código", "cod", "uuid", "numero", "número", "telefone", "cpf", "cnpj", "cep"]
DATE_KEYWORDS = ["data", "date", "dt", "periodo", "período", "emissao", "emissão", "admissao", "admissão", "vencimento", "prazo", "created", "updated"]
STRONG_DATE_KEYWORDS = ["data", "date", "dt", "emissao", "emissão", "admissao", "admissão", "vencimento", "created", "updated"]
DURATION_KEYWORDS = ["dias", "dia", "idade", "tempo", "duracao", "duração", "dias no funil", "sla"]
DIMENSION_KEYWORDS = ["loja", "produto", "categoria", "cliente", "fornecedor", "departamento", "centro", "conta", "cidade", "estado", "regiao", "região", "funcionario", "funcionário", "colaborador", "cargo", "projeto", "status", "responsavel", "responsável", "vendedor", "canal", "segmento", "grupo", "tipo", "empresa", "filial", "unidade"]
CATEGORY_KEYWORDS = ["categoria", "category", "grupo", "segmento", "classe", "tipo", "familia", "família", "linha", "departamento", "status", "canal"]
ID_KEYWORDS = ["id", "codigo", "código", "cod", "uuid", "chave", "numero", "número", "cpf", "cnpj", "telefone", "email"]


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

    raw = series.astype(str).str.strip()
    cleaned = raw.str.replace("R$", "", regex=False).str.replace("%", "", regex=False).str.replace(" ", "", regex=False)
    br_mask = cleaned.str.contains(r"^-?\d{1,3}(?:\.\d{3})+,\d+$", regex=True, na=False)
    cleaned = cleaned.where(~br_mask, cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    comma_decimal_mask = cleaned.str.contains(r"^-?\d+,\d+$", regex=True, na=False)
    cleaned = cleaned.where(~comma_decimal_mask, cleaned.str.replace(",", ".", regex=False))
    cleaned = cleaned.str.replace(r"(?<=\d),(?=\d{3}(\D|$))", "", regex=True)
    cleaned = cleaned.str.replace(r"[^\d.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _has_date_like_values(series: pd.Series, sample_size: int = 25) -> bool:
    sample = series.dropna().astype(str).head(sample_size)
    if sample.empty:
        return False
    date_pattern = r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})"
    return bool(sample.str.contains(date_pattern, regex=True, na=False).mean() >= 0.35)


def parse_date_series(series: pd.Series, column_name: str | None = None) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    normalized_name = normalize_text(column_name or series.name or "")

    # Evita falso positivo: "Dias no Funil" / duração / idade não são datas.
    if any(keyword in normalized_name for keyword in DURATION_KEYWORDS):
        return pd.Series(pd.NaT, index=series.index)

    has_date_keyword = any(keyword in normalized_name for keyword in DATE_KEYWORDS)
    has_strong_date_keyword = any(keyword in normalized_name for keyword in STRONG_DATE_KEYWORDS)

    if not has_date_keyword and not _has_date_like_values(series):
        return pd.Series(pd.NaT, index=series.index)

    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        excel_serial_ratio = numeric.between(20000, 60000).mean()
        if not has_strong_date_keyword or excel_serial_ratio < 0.60:
            return pd.Series(pd.NaT, index=series.index)
        return pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")

    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def get_sample_values(series: pd.Series, limit: int = 5) -> list[str]:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""].drop_duplicates().head(limit).tolist()
    return values


def confidence_from_score(score: float) -> float:
    return round(min(max(score / 100, 0), 1), 3)


def _has_keyword(normalized_name: str, keywords: list[str]) -> bool:
    return any(normalize_text(keyword) in normalized_name for keyword in keywords)


def score_numeric_column(df: pd.DataFrame, column: str) -> tuple[float, pd.Series]:
    series = clean_numeric_series(df[column])
    valid_ratio = float(series.notna().mean())
    non_zero_ratio = float((series.fillna(0) != 0).mean())
    unique_count = int(series.nunique(dropna=True))
    unique_ratio = unique_count / max(len(df), 1)
    normalized_name = normalize_text(column)

    score = 0.0
    if valid_ratio >= 0.60:
        score += valid_ratio * 42
    if non_zero_ratio >= 0.20:
        score += non_zero_ratio * 12

    for keyword in PRIMARY_METRIC_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 52
        elif normalized_keyword in normalized_name:
            score += 30

    for keyword in SECONDARY_METRIC_KEYWORDS:
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword == normalized_name:
            score += 22
        elif normalized_keyword in normalized_name:
            score += 12

    if _has_keyword(normalized_name, LOW_PRIORITY_METRIC_KEYWORDS):
        score -= 55
    if unique_count <= 1:
        score -= 25
    if unique_ratio > 0.96 and not _has_keyword(normalized_name, ["valor", "total", "receita", "faturamento", "amount", "revenue", "sales", "vendas"]):
        score -= 18

    return max(score, 0.0), series


def score_date_column(df: pd.DataFrame, column: str) -> tuple[float, pd.Series]:
    normalized_name = normalize_text(column)
    has_date_keyword = _has_keyword(normalized_name, DATE_KEYWORDS)
    if pd.api.types.is_numeric_dtype(df[column]) and not has_date_keyword:
        return 0.0, pd.Series(pd.NaT, index=df.index)

    series = parse_date_series(df[column], column)
    valid_ratio = float(series.notna().mean())
    unique_count = int(series.nunique(dropna=True))

    score = 0.0
    if valid_ratio >= 0.55:
        score += valid_ratio * 55
    if has_date_keyword:
        score += 35
    if unique_count <= 1:
        score -= 15

    return max(score, 0.0), series


def score_dimension_column(df: pd.DataFrame, column: str) -> float:
    series = df[column]
    total_rows = max(len(df), 1)
    unique_count = int(series.dropna().nunique())
    unique_ratio = unique_count / total_rows
    null_ratio = float(series.isna().mean())
    normalized_name = normalize_text(column)

    numeric_score, _ = score_numeric_column(df, column)
    date_score, _ = score_date_column(df, column)

    score = 0.0
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series) or unique_ratio <= 0.45:
        score += 22
    if 2 <= unique_count <= max(2, total_rows * 0.70):
        score += 32
    if 0.005 <= unique_ratio <= 0.70:
        score += 18
    if null_ratio <= 0.35:
        score += 10
    if _has_keyword(normalized_name, DIMENSION_KEYWORDS):
        score += 32
    if _has_keyword(normalized_name, ID_KEYWORDS):
        score -= 35
    if unique_ratio > 0.90:
        score -= 38
    if numeric_score > 75:
        score -= 30
    if date_score > 55:
        score -= 35

    return max(score, 0.0)


def score_category_column(df: pd.DataFrame, column: str) -> float:
    normalized_name = normalize_text(column)
    base_score = score_dimension_column(df, column)
    unique_ratio = df[column].dropna().nunique() / max(len(df), 1)

    score = base_score
    if _has_keyword(normalized_name, CATEGORY_KEYWORDS):
        score += 35
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

    # Regras de desempate para bases reais: CRM costuma ter status/responsável,
    # então não pode cair em "projetos" só por causa dessas colunas genéricas.
    if "cliente" in joined_columns and ("oportunidade" in joined_columns or "lead" in joined_columns or "pipeline" in joined_columns):
        scores["crm"] = scores.get("crm", 0) + 2.5
    if "valor oportunidade" in joined_columns or "probabilidade" in joined_columns:
        scores["crm"] = scores.get("crm", 0) + 1.5
    if "projeto" in joined_columns or "tarefa" in joined_columns or "sprint" in joined_columns or "backlog" in joined_columns:
        scores["projetos"] = scores.get("projetos", 0) + 2.0
    if "faturamento" in joined_columns and ("loja" in joined_columns or "produto" in joined_columns):
        scores["vendas"] = scores.get("vendas", 0) + 2.0

    domain_priority = {"crm": 6, "vendas": 5, "financeiro": 4, "estoque": 3, "rh": 2, "projetos": 1, "generico": 0}
    best_domain = sorted(scores.items(), key=lambda item: (item[1], domain_priority.get(item[0], 0)), reverse=True)[0][0]
    best_score = scores[best_domain]
    total_score = sum(scores.values())

    if best_score <= 0:
        return "generico", 0.3

    confidence = best_score / total_score if total_score > 0 else 0.3
    return best_domain, round(float(confidence), 3)


def infer_column_dtype(series: pd.Series, column_name: str | None = None) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    numeric_ratio = clean_numeric_series(series).notna().mean()
    date_ratio = parse_date_series(series, column_name).notna().mean()
    normalized = normalize_text(column_name or series.name or "")

    if date_ratio >= 0.65 or (date_ratio >= 0.45 and _has_keyword(normalized, DATE_KEYWORDS)):
        return "date"
    if pd.api.types.is_numeric_dtype(series) or numeric_ratio >= 0.65:
        return "numeric"
    return "text"


def choose_metric_column(numeric_scores: list[tuple[float, str]]) -> tuple[str | None, float]:
    valid_scores = [(score, column) for score, column in numeric_scores if score >= 32]
    if not valid_scores:
        return None, 0.0

    priority = ["faturamento", "receita", "valor total", "valor_total", "total", "vendas", "valor", "revenue", "amount", "custo", "despesa", "lucro", "saldo", "horas"]
    for keyword in priority:
        normalized_keyword = normalize_text(keyword)
        matches = [(score, column) for score, column in valid_scores if normalized_keyword == normalize_text(column)]
        if matches:
            score, column = sorted(matches, reverse=True)[0]
            return column, confidence_from_score(score)

    for keyword in priority:
        normalized_keyword = normalize_text(keyword)
        matches = [(score, column) for score, column in valid_scores if normalized_keyword in normalize_text(column)]
        if matches:
            score, column = sorted(matches, reverse=True)[0]
            return column, confidence_from_score(score)

    score, column = sorted(valid_scores, reverse=True)[0]
    return column, confidence_from_score(score)


def choose_top_column(scores: list[tuple[float, str]], excluded: set[str], min_score: float = 35) -> tuple[str | None, float]:
    valid_scores = [(score, column) for score, column in scores if score >= min_score and column not in excluded]
    if not valid_scores:
        return None, 0.0
    score, column = sorted(valid_scores, reverse=True)[0]
    return column, confidence_from_score(score)


def choose_secondary_metrics(numeric_scores: list[tuple[float, str]], metric_column: str | None, limit: int = 4) -> list[str]:
    metrics = []
    for score, column in sorted(numeric_scores, reverse=True):
        if column == metric_column or score < 32:
            continue
        metrics.append(column)
        if len(metrics) >= limit:
            break
    return metrics


def analyze_schema(df: pd.DataFrame) -> SchemaAnalysis:
    if df is None or df.empty:
        return SchemaAnalysis(None, None, None, None, None, [], [], [], [], [], "vazio", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [], ["A base está vazia ou não foi carregada."])

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
        dtype = infer_column_dtype(df[column], column)
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

        best_role = max([
            ("metric", numeric_score),
            ("date", date_score),
            ("dimension", dimension_score),
            ("category", category_score),
        ], key=lambda item: item[1])

        semantic_columns.append(SemanticColumn(column, best_role[0], confidence_from_score(best_role[1]), dtype, unique_count, round(unique_ratio, 3), round(null_ratio, 3), get_sample_values(df[column])))

    numeric_scores.sort(reverse=True)
    date_scores.sort(reverse=True)
    dimension_scores.sort(reverse=True)
    category_scores.sort(reverse=True)

    metric_column, metric_confidence = choose_metric_column(numeric_scores)
    date_column, date_confidence = choose_top_column(date_scores, excluded={metric_column} if metric_column else set(), min_score=35)

    excluded = {value for value in [metric_column, date_column] if value}
    valid_dimensions = [column for score, column in dimension_scores if score >= 35 and column not in excluded]

    domain, domain_confidence = classify_domain(df)

    def _dimension_priority(column: str) -> tuple[int, int]:
        normalized = normalize_text(column)
        domain_preferences = {
            "crm": ["cliente", "status", "segmento", "canal", "responsavel", "vendedor", "cidade", "empresa"],
            "vendas": ["loja", "produto", "categoria", "cliente", "vendedor", "cidade", "canal"],
            "financeiro": ["centro de custo", "conta", "tipo", "categoria", "departamento", "fornecedor"],
            "rh": ["departamento", "cargo", "funcionario", "colaborador", "cidade", "status"],
            "estoque": ["produto", "sku", "categoria", "armazem", "unidade", "fornecedor"],
            "projetos": ["projeto", "status", "responsavel", "departamento", "cliente", "sprint"],
        }
        preferred = domain_preferences.get(domain, ["centro de custo", "cliente", "empresa", "loja", "filial", "unidade", "produto", "departamento", "projeto", "responsavel", "vendedor", "cidade", "estado", "regiao"])
        secondary = ["categoria", "grupo", "segmento", "tipo", "status", "canal"]
        for index, item in enumerate(preferred):
            if item in normalized:
                return (3, 100 - index)
        if any(item in normalized for item in secondary):
            return (2, -len(normalized))
        return (1, -len(normalized))

    valid_dimensions = sorted(valid_dimensions, key=_dimension_priority, reverse=True)

    primary_dimension = valid_dimensions[0] if len(valid_dimensions) >= 1 else None
    secondary_dimension = valid_dimensions[1] if len(valid_dimensions) >= 2 else None

    primary_dimension_confidence = next((confidence_from_score(score) for score, column in dimension_scores if column == primary_dimension), 0.0)
    secondary_dimension_confidence = next((confidence_from_score(score) for score, column in dimension_scores if column == secondary_dimension), 0.0)

    category_candidates = [(score, column) for score, column in category_scores if score >= 45 and column not in excluded]
    if category_candidates:
        category_score, category_dimension = sorted(category_candidates, reverse=True)[0]
        category_dimension_confidence = confidence_from_score(category_score)
    else:
        category_dimension = None
        category_dimension_confidence = 0.0

    if category_dimension in [primary_dimension, secondary_dimension]:
        # Categoria pode ser igual à dimensão principal, mas não duplicamos a leitura.
        category_dimension = None
        category_dimension_confidence = 0.0

    secondary_metrics = choose_secondary_metrics(numeric_scores, metric_column)

    warnings: list[str] = []
    if not metric_column:
        warnings.append("Nenhuma métrica principal foi detectada com confiança suficiente.")
    if not date_column:
        warnings.append("Nenhuma coluna de data foi detectada com confiança suficiente.")
    if not primary_dimension:
        warnings.append("Nenhuma dimensão principal foi detectada com confiança suficiente.")
    if metric_confidence and metric_confidence < 0.55:
        warnings.append("A métrica principal foi detectada com confiança moderada/baixa.")
    if primary_dimension_confidence and primary_dimension_confidence < 0.55:
        warnings.append("A dimensão principal foi detectada com confiança moderada/baixa.")

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
