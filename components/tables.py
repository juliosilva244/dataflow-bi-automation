import pandas as pd
import streamlit as st

from domain.normalization import normalize_dataframe
from domain.schema import resolve_column_name
from services.settings import get_performance_settings


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = normalize_dataframe(df)
    return result.dataframe if result.dataframe is not None else pd.DataFrame()


def _find_col(df: pd.DataFrame, options: list[str]):
    targets = {resolve_column_name(option) for option in options}
    for column in df.columns:
        if resolve_column_name(column) in targets:
            return column
    return None


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalize_columns(df)

    revenue_col = "Faturamento" if "Faturamento" in df.columns else None
    quantity_col = "Quantidade" if "Quantidade" in df.columns else None
    profit_col = "Lucro" if "Lucro" in df.columns else None
    store_col = "Loja" if "Loja" in df.columns else None
    category_col = "Categoria" if "Categoria" in df.columns else None
    product_col = "Produto" if "Produto" in df.columns else None
    order_col = "Pedido" if "Pedido" in df.columns else None

    df.attrs["revenue_col"] = revenue_col
    df.attrs["quantity_col"] = quantity_col
    df.attrs["profit_col"] = profit_col
    df.attrs["store_col"] = store_col
    df.attrs["category_col"] = category_col
    df.attrs["product_col"] = product_col
    df.attrs["order_col"] = order_col

    return df


def _money(value):
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return value


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


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    formatted = df.copy()
    formatted.attrs = {}

    for col in formatted.columns:
        if any(term in col.lower() for term in ["faturamento", "receita", "valor", "vendas", "total", "lucro", "ticket"]):
            formatted[col] = formatted[col].apply(_money)

    return formatted


def paginate_dataframe(df: pd.DataFrame, page: int, page_size: int):
    page_size = max(int(page_size), 1)
    total_pages = max((len(df) + page_size - 1) // page_size, 1)
    page = min(max(int(page), 1), total_pages)
    start = (page - 1) * page_size
    result = df.iloc[start : start + page_size].copy()
    result.attrs = {}
    return result, total_pages, page


def table_store_summary(df: pd.DataFrame):
    df = _prepare_df(df)

    store_col = df.attrs["store_col"]
    revenue_col = df.attrs["revenue_col"]
    quantity_col = df.attrs["quantity_col"]
    profit_col = df.attrs["profit_col"]
    order_col = df.attrs["order_col"]

    if not store_col or not revenue_col:
        _empty_table("Não encontrei colunas de loja e faturamento/valor.")
        return

    agg = {revenue_col: "sum"}

    if quantity_col:
        agg[quantity_col] = "sum"

    if profit_col:
        agg[profit_col] = "sum"

    if order_col:
        agg[order_col] = "nunique"

    summary = df.groupby(store_col, as_index=False).agg(agg)

    rename_map = {
        store_col: "Loja",
        revenue_col: "Faturamento",
    }

    if quantity_col:
        rename_map[quantity_col] = "Quantidade"

    if profit_col:
        rename_map[profit_col] = "Lucro"

    if order_col:
        rename_map[order_col] = "Pedidos"

    summary = summary.rename(columns=rename_map)

    if "Pedidos" in summary.columns:
        denominator = summary["Pedidos"]
    else:
        record_counts = df.groupby(store_col).size()
        denominator = summary["Loja"].map(record_counts)

    summary["Ticket Médio"] = (
        summary["Faturamento"] / denominator.replace(0, pd.NA)
    ).fillna(0)

    summary = summary.sort_values("Faturamento", ascending=False)

    st.markdown("### Resumo por Loja")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )


def table_product_summary(df: pd.DataFrame):
    df = _prepare_df(df)

    product_col = df.attrs["product_col"]
    category_col = df.attrs["category_col"]
    revenue_col = df.attrs["revenue_col"]
    quantity_col = df.attrs["quantity_col"]

    if not product_col or not revenue_col:
        _empty_table("Não encontrei colunas de produto e faturamento/valor.")
        return

    group_cols = [product_col]

    if category_col:
        group_cols.append(category_col)

    agg = {revenue_col: "sum"}

    if quantity_col:
        agg[quantity_col] = "sum"

    summary = df.groupby(group_cols, as_index=False).agg(agg)

    rename_map = {
        product_col: "Produto",
        revenue_col: "Faturamento",
    }

    if category_col:
        rename_map[category_col] = "Categoria"

    if quantity_col:
        rename_map[quantity_col] = "Quantidade"

    summary = summary.rename(columns=rename_map)
    summary = summary.sort_values("Faturamento", ascending=False).head(20)

    st.markdown("### Top Produtos")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )


def table_category_summary(df: pd.DataFrame):
    df = _prepare_df(df)

    category_col = df.attrs["category_col"]
    revenue_col = df.attrs["revenue_col"]
    quantity_col = df.attrs["quantity_col"]

    if not category_col or not revenue_col:
        _empty_table("Não encontrei colunas de categoria e faturamento/valor.")
        return

    agg = {revenue_col: "sum"}

    if quantity_col:
        agg[quantity_col] = "sum"

    summary = df.groupby(category_col, as_index=False).agg(agg)

    total_revenue = summary[revenue_col].sum()

    summary["participacao_%"] = (
        summary[revenue_col] / total_revenue * 100 if total_revenue else 0
    )

    rename_map = {
        category_col: "Categoria",
        revenue_col: "Faturamento",
        "participacao_%": "Participação %",
    }

    if quantity_col:
        rename_map[quantity_col] = "Quantidade"

    summary = summary.rename(columns=rename_map)
    summary = summary.sort_values("Faturamento", ascending=False)

    summary["Participação %"] = summary["Participação %"].map(lambda x: f"{x:.2f}%")

    st.markdown("### Desempenho por Categoria")
    st.dataframe(
        _format_table(summary),
        width="stretch",
        hide_index=True,
    )


def table_raw_data(df: pd.DataFrame):
    if df is None or df.empty:
        _empty_table("Nenhuma base carregada.")
        return

    st.markdown("### Base de Dados")
    default_size = get_performance_settings().table_page_size
    size_options = sorted({50, 100, 250, 500, default_size})
    col_size, col_page = st.columns([1, 1])
    with col_size:
        page_size = st.selectbox(
            "Linhas por página",
            size_options,
            index=size_options.index(default_size),
            key="raw_table_page_size",
        )
    total_pages = max((len(df) + page_size - 1) // page_size, 1)
    with col_page:
        page = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"raw_table_page_{total_pages}",
        )
    display_df, total_pages, page = paginate_dataframe(df, page, page_size)
    start = (page - 1) * page_size + 1
    end = min(page * page_size, len(df))
    st.caption(
        f"Exibindo registros {start:,} a {end:,} de {len(df):,} "
        f"(página {page} de {total_pages}). Cálculos e exportação usam a base completa."
    )
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )


def render_tables(df: pd.DataFrame):
    st.markdown("## Tabelas Executivas")

    if df is None or df.empty:
        _empty_table("Nenhuma base de dados foi carregada.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Resumo por Loja",
            "Top Produtos",
            "Categorias",
            "Base Completa",
        ]
    )

    with tab1:
        table_store_summary(df)

    with tab2:
        table_product_summary(df)

    with tab3:
        table_category_summary(df)

    with tab4:
        table_raw_data(df)


def render_table(df: pd.DataFrame):
    render_tables(df)


show_tables = render_tables
display_tables = render_tables
tables_section = render_tables
