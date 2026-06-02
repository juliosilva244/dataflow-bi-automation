import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st


DEFAULT_FILE_PATH = Path("data/raw/vendas.xlsx")


COLUMN_MAPPING = {
    # Data
    "data": "Data",
    "data venda": "Data",
    "data_venda": "Data",
    "dt venda": "Data",
    "dt_venda": "Data",
    "date": "Data",
    "sale date": "Data",
    "created at": "Data",
    "emissao": "Data",
    "pedido data": "Data",

    # Loja
    "loja": "Loja",
    "store": "Loja",
    "unidade": "Loja",
    "filial": "Loja",
    "empresa": "Loja",
    "ponto venda": "Loja",
    "pdv": "Loja",
    "branch": "Loja",

    # Produto
    "produto": "Produto",
    "product": "Produto",
    "item": "Produto",
    "sku": "Produto",
    "descricao": "Produto",
    "descrição": "Produto",
    "nome produto": "Produto",
    "produto nome": "Produto",

    # Categoria
    "categoria": "Categoria",
    "category": "Categoria",
    "grupo": "Categoria",
    "departamento": "Categoria",
    "linha": "Categoria",

    # Quantidade
    "quantidade": "Quantidade",
    "qtd": "Quantidade",
    "qtde": "Quantidade",
    "quantity": "Quantidade",
    "volume": "Quantidade",
    "unidades": "Quantidade",

    # Preço unitário
    "preco unitario": "Preco_Unitario",
    "preço unitário": "Preco_Unitario",
    "preco_unitario": "Preco_Unitario",
    "valor unitario": "Preco_Unitario",
    "valor_unitario": "Preco_Unitario",
    "unit price": "Preco_Unitario",
    "price": "Preco_Unitario",

    # Faturamento / Receita / Valor total
    "faturamento": "Faturamento",
    "receita": "Faturamento",
    "valor total": "Faturamento",
    "valor_total": "Faturamento",
    "total": "Faturamento",
    "venda": "Faturamento",
    "vendas": "Faturamento",
    "sales": "Faturamento",
    "revenue": "Faturamento",
    "amount": "Faturamento",
    "valor": "Faturamento",
}


TEXT_FALLBACK = {
    "Loja": "Geral",
    "Produto": "Não informado",
    "Categoria": "Sem categoria",
}


def _normalize_text(value: object) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[_\-./]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_money_series(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    normalized_columns = []
    used_columns = set()

    for original_col in df.columns:
        normalized = _normalize_text(original_col)
        mapped = COLUMN_MAPPING.get(normalized, str(original_col).strip())

        if mapped in used_columns:
            counter = 2
            new_name = f"{mapped}_{counter}"
            while new_name in used_columns:
                counter += 1
                new_name = f"{mapped}_{counter}"
            mapped = new_name

        used_columns.add(mapped)
        normalized_columns.append(mapped)

    df.columns = normalized_columns
    return df


def _find_numeric_columns(df: pd.DataFrame) -> list[str]:
    numeric_candidates = []

    for column in df.columns:
        converted = _clean_money_series(df[column])
        valid_ratio = converted.notna().mean()

        if valid_ratio >= 0.6:
            numeric_candidates.append(column)

    return numeric_candidates


def _auto_detect_revenue_column(df: pd.DataFrame) -> pd.DataFrame:
    if "Faturamento" in df.columns:
        return df

    numeric_columns = _find_numeric_columns(df)

    if not numeric_columns:
        return df

    priority_keywords = [
        "faturamento",
        "receita",
        "valor",
        "total",
        "venda",
        "sales",
        "revenue",
        "amount",
    ]

    scored = []

    for column in numeric_columns:
        normalized = _normalize_text(column)
        score = 0

        for keyword in priority_keywords:
            if keyword in normalized:
                score += 10

        median_value = _clean_money_series(df[column]).median()
        if pd.notna(median_value):
            score += min(float(median_value), 1_000_000) / 1_000_000

        scored.append((score, column))

    scored.sort(reverse=True)
    best_column = scored[0][1]

    df["Faturamento"] = _clean_money_series(df[best_column])
    return df


def _auto_detect_date_column(df: pd.DataFrame) -> pd.DataFrame:
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
        return df

    best_column = None
    best_ratio = 0

    for column in df.columns:
        converted = pd.to_datetime(df[column], errors="coerce", dayfirst=True)
        ratio = converted.notna().mean()

        normalized = _normalize_text(column)
        if any(term in normalized for term in ["data", "date", "dt"]):
            ratio += 0.25

        if ratio > best_ratio:
            best_ratio = ratio
            best_column = column

    if best_column is not None and best_ratio >= 0.45:
        df["Data"] = pd.to_datetime(df[best_column], errors="coerce", dayfirst=True)
    else:
        df["Data"] = pd.Timestamp.today().normalize()

    return df


def _auto_detect_dimension_column(
    df: pd.DataFrame,
    target_column: str,
    keywords: list[str],
    fallback_value: str,
) -> pd.DataFrame:
    if target_column in df.columns:
        df[target_column] = df[target_column].astype(str).str.strip()
        return df

    candidates = []

    for column in df.columns:
        if column in ["Data", "Faturamento", "Quantidade", "Preco_Unitario"]:
            continue

        normalized = _normalize_text(column)
        unique_ratio = df[column].nunique(dropna=True) / max(len(df), 1)

        score = 0

        for keyword in keywords:
            if keyword in normalized:
                score += 10

        if 0 < unique_ratio <= 0.6:
            score += 2

        if df[column].dtype == "object":
            score += 1

        candidates.append((score, column))

    candidates.sort(reverse=True)

    if candidates and candidates[0][0] > 0:
        df[target_column] = df[candidates[0][1]].astype(str).str.strip()
    else:
        df[target_column] = fallback_value

    return df


def _prepare_quantity(df: pd.DataFrame) -> pd.DataFrame:
    if "Quantidade" in df.columns:
        df["Quantidade"] = _clean_money_series(df["Quantidade"])
    else:
        df["Quantidade"] = 1

    return df


def _prepare_revenue(df: pd.DataFrame) -> pd.DataFrame:
    if "Faturamento" not in df.columns and {"Quantidade", "Preco_Unitario"}.issubset(df.columns):
        quantidade = _clean_money_series(df["Quantidade"])
        preco = _clean_money_series(df["Preco_Unitario"])
        df["Faturamento"] = quantidade * preco

    df = _auto_detect_revenue_column(df)

    if "Faturamento" in df.columns:
        df["Faturamento"] = _clean_money_series(df["Faturamento"])

    return df


def validar_base_minima(df: pd.DataFrame) -> str | None:
    if "Faturamento" not in df.columns:
        return (
            "Não consegui identificar uma coluna de valor/faturamento. "
            "Use uma coluna como Faturamento, Receita, Valor Total, Total, Vendas ou Valor."
        )

    if df["Faturamento"].dropna().empty:
        return "A coluna de faturamento foi identificada, mas não possui valores numéricos válidos."

    return None


def limpar_dados(df: pd.DataFrame):
    df = df.copy()
    df = normalize_columns(df)

    df = _auto_detect_date_column(df)
    df = _auto_detect_dimension_column(
        df,
        "Loja",
        ["loja", "store", "filial", "unidade", "empresa", "pdv"],
        TEXT_FALLBACK["Loja"],
    )
    df = _auto_detect_dimension_column(
        df,
        "Produto",
        ["produto", "product", "item", "sku", "descricao"],
        TEXT_FALLBACK["Produto"],
    )

    if "Categoria" not in df.columns:
        df["Categoria"] = TEXT_FALLBACK["Categoria"]

    df = _prepare_quantity(df)
    df = _prepare_revenue(df)

    erro = validar_base_minima(df)
    if erro:
        return None, erro

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(1)
    df["Faturamento"] = pd.to_numeric(df["Faturamento"], errors="coerce")

    df["Loja"] = df["Loja"].fillna(TEXT_FALLBACK["Loja"]).astype(str).str.strip()
    df["Produto"] = df["Produto"].fillna(TEXT_FALLBACK["Produto"]).astype(str).str.strip()
    df["Categoria"] = df["Categoria"].fillna(TEXT_FALLBACK["Categoria"]).astype(str).str.strip()

    df = df.dropna(subset=["Faturamento"])
    df = df[df["Faturamento"] >= 0]
    df = df[df["Quantidade"] > 0]

    if df["Data"].isna().all():
        df["Data"] = pd.Timestamp.today().normalize()
    else:
        df["Data"] = df["Data"].fillna(df["Data"].max())

    if df.empty:
        return None, "A base não possui dados válidos após a limpeza."

    return df.reset_index(drop=True), None


@st.cache_data(ttl=3600)
def ler_arquivo_upload(arquivo_upload):
    nome_arquivo = arquivo_upload.name.lower()

    if nome_arquivo.endswith(".xlsx") or nome_arquivo.endswith(".xls"):
        return pd.read_excel(arquivo_upload)

    if nome_arquivo.endswith(".csv"):
        try:
            return pd.read_csv(arquivo_upload, sep=None, engine="python")
        except Exception:
            arquivo_upload.seek(0)
            return pd.read_csv(arquivo_upload, sep=";")

    raise ValueError("Formato de arquivo não suportado. Envie apenas .xlsx, .xls ou .csv.")


def aplicar_filtro_periodo(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    if periodo == "Tudo" or "Data" not in df.columns:
        return df

    data_maxima = pd.to_datetime(df["Data"], errors="coerce").max()

    if pd.isna(data_maxima):
        return df

    if periodo == "Últimos 7 dias":
        limite = data_maxima - pd.Timedelta(days=7)
        return df[df["Data"] >= limite]

    if periodo == "Últimos 30 dias":
        limite = data_maxima - pd.Timedelta(days=30)
        return df[df["Data"] >= limite]

    if periodo == "Últimos 90 dias":
        limite = data_maxima - pd.Timedelta(days=90)
        return df[df["Data"] >= limite]

    if periodo == "Ano atual":
        return df[df["Data"].dt.year == data_maxima.year]

    return df


@st.cache_data(ttl=3600)
def carregar_dados(arquivo_upload=None, periodo="Tudo"):
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

        if df.empty:
            return None, origem, "Não existem dados para o período selecionado."

        df = df.sort_values("Data").reset_index(drop=True)

        return df, origem, None

    except FileNotFoundError:
        return None, None, f"Arquivo padrão não encontrado em: {DEFAULT_FILE_PATH}"

    except Exception as erro:
        return None, None, f"Erro ao carregar dados: {erro}"