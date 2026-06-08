from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


DEFAULT_FILE_PATH = Path("data/raw/vendas.xlsx")

DATE_NAME_HINTS = [
    # Evita falso positivo como "Dias no Funil" virando data 1970.
    "data", "date", "dt", "periodo", "período",
    "emissao", "emissão", "vencimento", "prazo", "created", "updated", "admissao", "admissão",
]

STRONG_DATE_NAME_HINTS = [
    "data", "date", "dt", "emissao", "emissão", "vencimento", "created", "updated", "admissao", "admissão"
]

DURATION_NAME_HINTS = [
    "dias", "dia", "idade", "tempo", "duracao", "duração", "prazo em dias", "dias no funil", "sla"
]

NUMERIC_NAME_HINTS = [
    "faturamento", "receita", "valor", "total", "venda", "vendas", "sales", "revenue", "amount",
    "preco", "preço", "price", "custo", "despesa", "lucro", "margem", "saldo", "quantidade",
    "qtd", "qtde", "volume", "horas", "salario", "salário", "ticket", "oportunidade", "pipeline", "deal",
]

NEGATIVE_ALLOWED_HINTS = [
    "lucro", "margem", "saldo", "resultado", "variacao", "variação", "delta", "desvio",
]

CANONICAL_MAPPING = {
    # Mantém compatibilidade com a base demo de vendas sem forçar planilhas genéricas.
    "data venda": "Data",
    "data_venda": "Data",
    "dt venda": "Data",
    "dt_venda": "Data",
    "sale date": "Data",
    "pedido data": "Data",
    "loja": "Loja",
    "store": "Loja",
    "filial": "Loja",
    "unidade": "Loja",
    "pdv": "Loja",
    "branch": "Loja",
    "produto": "Produto",
    "product": "Produto",
    "nome produto": "Produto",
    "produto nome": "Produto",
    "sku": "SKU",
    "categoria": "Categoria",
    "category": "Categoria",
    "grupo": "Grupo",
    "departamento": "Departamento",
    "quantidade": "Quantidade",
    "qtd": "Quantidade",
    "qtde": "Quantidade",
    "quantity": "Quantidade",
    "volume": "Quantidade",
    "preco unitario": "Preco_Unitario",
    "preço unitário": "Preco_Unitario",
    "valor unitario": "Preco_Unitario",
    "valor_unitario": "Preco_Unitario",
    "unit price": "Preco_Unitario",
    "faturamento": "Faturamento",
    "receita": "Receita",
    "valor total": "Valor_Total",
    "valor_total": "Valor_Total",
    "revenue": "Receita",
    "amount": "Valor",
}


def normalize_text(value: object) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[_\-./]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _safe_column_name(name: object) -> str:
    raw = str(name).strip()
    if not raw or raw.lower().startswith("unnamed"):
        return "Coluna"

    normalized = normalize_text(raw)
    mapped = CANONICAL_MAPPING.get(normalized)
    if mapped:
        return mapped

    cleaned = re.sub(r"\s+", " ", raw)
    cleaned = cleaned.replace("\n", " ").replace("\t", " ").strip()
    return cleaned or "Coluna"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    used: dict[str, int] = {}
    new_columns: list[str] = []

    for column in df.columns:
        base_name = _safe_column_name(column)
        count = used.get(base_name, 0)
        used[base_name] = count + 1
        new_columns.append(base_name if count == 0 else f"{base_name}_{count + 1}")

    df.columns = new_columns
    return df


def clean_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    raw = series.astype(str).str.strip()
    raw = raw.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "null": pd.NA})

    cleaned = (
        raw.str.replace("R$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # Caso brasileiro: 1.234,56 -> 1234.56
    br_mask = cleaned.str.contains(r"^-?\d{1,3}(?:\.\d{3})+,\d+$", regex=True, na=False)
    cleaned_br = cleaned.where(~br_mask, cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))

    # Caso simples com vírgula decimal: 123,45 -> 123.45
    comma_decimal_mask = cleaned_br.str.contains(r"^-?\d+,\d+$", regex=True, na=False)
    cleaned_br = cleaned_br.where(~comma_decimal_mask, cleaned_br.str.replace(",", ".", regex=False))

    # Remove separadores residuais de milhar em números americanos mal misturados.
    cleaned_br = cleaned_br.str.replace(r"(?<=\d),(?=\d{3}(\D|$))", "", regex=True)
    cleaned_br = cleaned_br.str.replace(r"[^\d.\-]", "", regex=True)

    return pd.to_numeric(cleaned_br, errors="coerce")


def _has_date_like_values(series: pd.Series, sample_size: int = 25) -> bool:
    sample = series.dropna().astype(str).head(sample_size)
    if sample.empty:
        return False
    date_pattern = r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})"
    return bool(sample.str.contains(date_pattern, regex=True, na=False).mean() >= 0.35)


def parse_date_series(series: pd.Series, column_name: str | None = None) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    normalized = normalize_text(column_name or series.name or "")

    # Colunas de duração/idade/tempo não são datas, mesmo quando contêm a palavra "dia".
    if any(hint in normalized for hint in DURATION_NAME_HINTS):
        return pd.Series(pd.NaT, index=series.index)

    has_date_hint = any(hint in normalized for hint in DATE_NAME_HINTS)
    has_strong_date_hint = any(hint in normalized for hint in STRONG_DATE_NAME_HINTS)

    if not has_date_hint and not _has_date_like_values(series):
        return pd.Series(pd.NaT, index=series.index)

    # Números simples como 13, 25, 70 não podem virar 1970-01-01.
    # Só aceitamos número como data se parecer serial real do Excel e tiver nome forte de data.
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        excel_serial_ratio = numeric.between(20000, 60000).mean()
        if not has_strong_date_hint or excel_serial_ratio < 0.60:
            return pd.Series(pd.NaT, index=series.index)
        return pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")

    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
    return parsed


def _looks_numeric(column: str, series: pd.Series) -> bool:
    normalized = normalize_text(column)
    converted = clean_numeric_series(series)
    valid_ratio = float(converted.notna().mean())

    if valid_ratio >= 0.85:
        return True

    if valid_ratio >= 0.55 and any(hint in normalized for hint in NUMERIC_NAME_HINTS):
        return True

    return False


def _looks_date(column: str, series: pd.Series) -> bool:
    normalized = normalize_text(column)
    has_date_hint = any(hint in normalized for hint in DATE_NAME_HINTS)

    if pd.api.types.is_numeric_dtype(series) and not has_date_hint:
        return False

    parsed = parse_date_series(series, column)
    valid_ratio = float(parsed.notna().mean())

    if valid_ratio >= 0.80:
        return True

    if valid_ratio >= 0.45 and has_date_hint:
        return True

    return False


def _clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .fillna("Não informado")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .replace({"": "Não informado", "nan": "Não informado", "None": "Não informado"})
    )


def _drop_empty_rows_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    empty_cols = []
    for column in df.columns:
        values = df[column].astype(str).str.strip().str.lower()
        if values.isin(["", "nan", "none", "null"]).all():
            empty_cols.append(column)

    if empty_cols:
        df = df.drop(columns=empty_cols)

    return df


def limpar_dados(df: pd.DataFrame) -> tuple[pd.DataFrame | None, str | None]:
    if df is None or df.empty:
        return None, "A base enviada está vazia."

    df = _drop_empty_rows_and_columns(df)
    df = normalize_columns(df)

    if df.empty or len(df.columns) == 0:
        return None, "A base não possui linhas ou colunas válidas."

    for column in list(df.columns):
        if _looks_date(column, df[column]):
            df[column] = parse_date_series(df[column], column)
        elif _looks_numeric(column, df[column]):
            df[column] = clean_numeric_series(df[column])
        elif pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column]):
            df[column] = _clean_text_series(df[column])

    # Compatibilidade útil: cria Faturamento apenas quando Quantidade e Preco_Unitario existem de verdade.
    if "Faturamento" not in df.columns and {"Quantidade", "Preco_Unitario"}.issubset(df.columns):
        quantidade = clean_numeric_series(df["Quantidade"]).fillna(0)
        preco = clean_numeric_series(df["Preco_Unitario"]).fillna(0)
        computed = quantidade * preco
        if computed.notna().any() and float(computed.sum()) > 0:
            df["Faturamento"] = computed

    numeric_columns = [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]
    if not numeric_columns:
        return None, (
            "Não consegui identificar nenhuma coluna numérica analisável. "
            "Inclua pelo menos uma coluna como Valor, Receita, Faturamento, Quantidade, Custo ou Total."
        )

    # Remove linhas totalmente inúteis sem exigir modelo de vendas.
    df = df.dropna(axis=0, how="all").reset_index(drop=True)

    if df.empty:
        return None, "A base não possui dados válidos após a limpeza."

    return df, None


@st.cache_data(ttl=3600, show_spinner=False)
def ler_arquivo_upload(arquivo_upload: Any) -> pd.DataFrame:
    nome_arquivo = arquivo_upload.name.lower()

    if nome_arquivo.endswith((".xlsx", ".xls")):
        return pd.read_excel(arquivo_upload)

    if nome_arquivo.endswith(".csv"):
        try:
            return pd.read_csv(arquivo_upload, sep=None, engine="python", encoding="utf-8")
        except UnicodeDecodeError:
            arquivo_upload.seek(0)
            return pd.read_csv(arquivo_upload, sep=None, engine="python", encoding="latin1")
        except Exception:
            arquivo_upload.seek(0)
            return pd.read_csv(arquivo_upload, sep=";", encoding="utf-8")

    raise ValueError("Formato de arquivo não suportado. Envie apenas .xlsx, .xls ou .csv.")


def _find_best_date_column(df: pd.DataFrame) -> str | None:
    best_column = None
    best_score = 0.0

    for column in df.columns:
        parsed = parse_date_series(df[column], column)
        valid_ratio = float(parsed.notna().mean())
        normalized = normalize_text(column)
        score = valid_ratio + (0.25 if any(hint in normalized for hint in DATE_NAME_HINTS) else 0)

        if score > best_score and valid_ratio >= 0.35:
            best_score = score
            best_column = column

    return best_column


def aplicar_filtro_periodo(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    if periodo == "Tudo" or df is None or df.empty:
        return df

    date_column = _find_best_date_column(df)
    if not date_column:
        return df

    filtered_df = df.copy()
    filtered_df[date_column] = parse_date_series(filtered_df[date_column], date_column)
    data_maxima = filtered_df[date_column].max()

    if pd.isna(data_maxima):
        return df

    if periodo == "Últimos 7 dias":
        limite = data_maxima - pd.Timedelta(days=7)
        return filtered_df[filtered_df[date_column] >= limite]

    if periodo == "Últimos 30 dias":
        limite = data_maxima - pd.Timedelta(days=30)
        return filtered_df[filtered_df[date_column] >= limite]

    if periodo == "Últimos 90 dias":
        limite = data_maxima - pd.Timedelta(days=90)
        return filtered_df[filtered_df[date_column] >= limite]

    if periodo == "Ano atual":
        return filtered_df[filtered_df[date_column].dt.year == data_maxima.year]

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados(arquivo_upload=None, periodo: str = "Tudo"):
    try:
        if arquivo_upload is not None:
            df = ler_arquivo_upload(arquivo_upload)
            origem = f"Arquivo enviado: {arquivo_upload.name}"
        else:
            df = pd.read_excel(DEFAULT_FILE_PATH)
            origem = "Arquivo padrão do sistema"

        df, erro_limpeza = limpar_dados(df)
        if erro_limpeza:
            return None, origem, erro_limpeza

        df = aplicar_filtro_periodo(df, periodo)

        if df is None or df.empty:
            return None, origem, "Não existem dados para o período selecionado."

        date_column = _find_best_date_column(df)
        if date_column and date_column in df.columns:
            df = df.sort_values(date_column).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)

        return df, origem, None

    except FileNotFoundError:
        return None, None, f"Arquivo padrão não encontrado em: {DEFAULT_FILE_PATH}"

    except Exception as erro:
        return None, None, f"Erro ao carregar dados: {erro}"
