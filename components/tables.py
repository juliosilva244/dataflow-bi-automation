import pandas as pd
import streamlit as st

from services.formatter import format_currency, format_percent, safe_divide

try:
    from services.schema_analyzer import analyze_schema
except Exception:
    analyze_schema = None


def _empty_table(message: str):
    st.markdown(
        f"""
        <div class="empty-state">
            <h4>Tabela indisponível</h4>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _get_schema(df: pd.DataFrame) -> dict:
    if df is None or df.empty or analyze_schema is None:
        return {
            "metric_column": None,
            "date_column": None,
            "primary_dimension": None,
            "secondary_dimension": None,
            "dimension_columns": [],
            "numeric_columns": [],
            "date_columns": [],
            "text_columns": [],
            "domain": "generico",
            "confidence": 0,
            "warnings": [],
        }

    schema = analyze_schema(df)

    if hasattr(schema, "to_dict"):
        return schema.to_dict()

    return dict(schema)


def _clean_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0)

    cleaned = (
        series.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
    )

    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    formatted = df.copy()

    for col in formatted.columns:
        normalized = str(col).lower()

        if any(
            term in normalized
            for term in [
                "faturamento",
                "receita",
                "valor",
                "vendas",
                "total",
                "lucro",
                "ticket",
                "custo",
                "despesa",
                "saldo",
                "salário",
                "salario",
                "métrica",
                "metrica",
            ]
        ):
            formatted[col] = formatted[col].apply(format_currency)

        if any(term in normalized for term in ["participação", "participacao", "%"]):
            formatted[col] = formatted[col].apply(format_percent)

    return formatted


def _build_dimension_summary(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    quantity_col: str | None = None,
    limit: int = 30,
) -> pd.DataFrame:
    work_df = df.copy()

    if metric_col not in work_df.columns or dimension_col not in work_df.columns:
        return pd.DataFrame()

    work_df[metric_col] = _clean_numeric(work_df[metric_col])
    work_df[dimension_col] = work_df[dimension_col].fillna("Não informado").astype(str)

    agg = {
        metric_col: "sum",
    }

    if quantity_col and quantity_col in work_df.columns:
        work_df[quantity_col] = _clean_numeric(work_df[quantity_col])
        agg[quantity_col] = "sum"

    summary = work_df.groupby(dimension_col, as_index=False, dropna=False).agg(agg)

    total_metric = summary[metric_col].sum()

    summary["Participação %"] = (
        summary[metric_col] / total_metric * 100 if total_metric else 0
    )

    summary["Registros"] = work_df.groupby(dimension_col, dropna=False).size().values

    if quantity_col and quantity_col in summary.columns:
        summary["Média por Quantidade"] = summary.apply(
            lambda row: safe_divide(row[metric_col], row[quantity_col]),
            axis=1,
        )

    summary = summary.sort_values(metric_col, ascending=False).head(limit)

    rename_map = {
        dimension_col: dimension_col,
        metric_col: "Valor Total",
    }

    if quantity_col and quantity_col in summary.columns:
        rename_map[quantity_col] = "Quantidade"

    summary = summary.rename(columns=rename_map)

    return summary


def table_dynamic_dimension(
    df: pd.DataFrame,
    dimension_col: str | None,
    metric_col: str | None,
    quantity_col: str | None,
    title: str,
):
    if not dimension_col or not metric_col:
        _empty_table("Não foi possível detectar dimensão e métrica suficientes para esta tabela.")
        return

    if dimension_col not in df.columns or metric_col not in df.columns:
        _empty_table("As colunas detectadas não existem na base atual.")
        return

    summary = _build_dimension_summary(
        df=df,
        dimension_col=dimension_col,
        metric_col=metric_col,
        quantity_col=quantity_col,
    )

    if summary.empty:
        _empty_table("Não existem dados suficientes para montar o resumo.")
        return

    st.markdown(f"### {title}")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )


def table_numeric_summary(df: pd.DataFrame, schema: dict):
    numeric_columns = schema.get("numeric_columns", []) or []

    if not numeric_columns:
        _empty_table("Nenhuma coluna numérica foi detectada.")
        return

    rows = []

    for column in numeric_columns:
        if column not in df.columns:
            continue

        values = _clean_numeric(df[column])

        rows.append(
            {
                "Métrica": column,
                "Total": values.sum(),
                "Média": values.mean(),
                "Mínimo": values.min(),
                "Máximo": values.max(),
                "Valores válidos": int(values.notna().sum()),
            }
        )

    summary = pd.DataFrame(rows)

    if summary.empty:
        _empty_table("Não foi possível consolidar as métricas numéricas.")
        return

    st.markdown("### Resumo Numérico")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )


def table_schema_summary(schema: dict):
    columns = schema.get("columns", []) or []

    if not columns:
        _empty_table("Nenhuma leitura de schema está disponível.")
        return

    rows = []

    for column in columns:
        rows.append(
            {
                "Coluna": column.get("name"),
                "Função Detectada": column.get("role"),
                "Confiança": column.get("confidence"),
                "Tipo": column.get("dtype"),
                "Valores Únicos": column.get("unique_count"),
                "Nulos %": column.get("null_ratio", 0) * 100,
                "Exemplos": ", ".join(column.get("sample_values", [])[:3]),
            }
        )

    summary = pd.DataFrame(rows)

    st.markdown("### Leitura Automática do Schema")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )

    warnings = schema.get("warnings", []) or []

    if warnings:
        st.warning(" | ".join(warnings))


def table_raw_data(df: pd.DataFrame):
    if df is None or df.empty:
        _empty_table("Nenhuma base carregada.")
        return

    st.markdown("### Base Completa")
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )


def render_tables(df: pd.DataFrame):
    st.markdown("## Tabelas Executivas")

    if df is None or df.empty:
        _empty_table("Nenhuma base de dados foi carregada.")
        return

    schema = _get_schema(df)

    metric_col = schema.get("metric_column")
    primary_dimension = schema.get("primary_dimension")
    secondary_dimension = schema.get("secondary_dimension")
    dimension_columns = schema.get("dimension_columns", []) or []

    quantity_col = None

    for candidate in ["Quantidade", "quantidade", "qtd", "qtde", "volume"]:
        if candidate in df.columns:
            quantity_col = candidate
            break

    tab_labels = [
        "Dimensão Principal",
        "Dimensão Secundária",
        "Resumo Numérico",
        "Schema Detectado",
        "Base Completa",
    ]

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        table_dynamic_dimension(
            df=df,
            dimension_col=primary_dimension,
            metric_col=metric_col,
            quantity_col=quantity_col,
            title=f"Resumo por {primary_dimension or 'Dimensão Principal'}",
        )

    with tabs[1]:
        if secondary_dimension:
            table_dynamic_dimension(
                df=df,
                dimension_col=secondary_dimension,
                metric_col=metric_col,
                quantity_col=quantity_col,
                title=f"Resumo por {secondary_dimension}",
            )
        elif len(dimension_columns) >= 2:
            table_dynamic_dimension(
                df=df,
                dimension_col=dimension_columns[1],
                metric_col=metric_col,
                quantity_col=quantity_col,
                title=f"Resumo por {dimension_columns[1]}",
            )
        else:
            _empty_table("Nenhuma dimensão secundária foi detectada.")

    with tabs[2]:
        table_numeric_summary(df, schema)

    with tabs[3]:
        table_schema_summary(schema)

    with tabs[4]:
        table_raw_data(df)


def render_table(df: pd.DataFrame):
    render_tables(df)


show_tables = render_tables
display_tables = render_tables
tables_section = render_tables