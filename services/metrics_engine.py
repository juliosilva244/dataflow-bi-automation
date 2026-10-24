from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

import pandas as pd

from domain.models import AnalyticalKPIs, DataQualityReport, GrowthMetrics
from domain.normalization import normalize_dataframe
from domain.periods import split_equivalent_periods
from domain.schema import resolve_column_name


@dataclass(frozen=True)
class ColumnMap:
    data: str | None
    loja: str | None
    produto: str | None
    faturamento: str | None
    quantidade: str | None
    pedido: str | None
    categoria: str | None = None
    lucro: str | None = None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    source_quality = df.attrs.get("quality_report")
    result = normalize_dataframe(df)
    if result.dataframe is not None:
        if isinstance(source_quality, DataQualityReport):
            result.dataframe.attrs["quality_report"] = source_quality
        return result.dataframe
    empty = pd.DataFrame(columns=df.columns)
    empty.attrs["quality_report"] = result.quality
    return empty


def find_column(df: pd.DataFrame, possible_names: list[str]) -> str | None:
    targets = {resolve_column_name(name) for name in possible_names}
    for column in df.columns:
        canonical = resolve_column_name(column)
        if canonical and canonical in targets:
            return column

    return None


def get_column_map(df: pd.DataFrame) -> ColumnMap:
    return ColumnMap(
        data="Data" if "Data" in df.columns else None,
        loja="Loja" if "Loja" in df.columns else None,
        produto="Produto" if "Produto" in df.columns else None,
        faturamento="Faturamento" if "Faturamento" in df.columns else None,
        quantidade="Quantidade" if "Quantidade" in df.columns else None,
        pedido="Pedido" if "Pedido" in df.columns else None,
        categoria="Categoria" if "Categoria" in df.columns else None,
        lucro="Lucro" if "Lucro" in df.columns else None,
    )


def prepare_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, ColumnMap]:
    df = normalize_columns(df)
    columns = get_column_map(df)
    return df, columns


def safe_sum(df: pd.DataFrame, column: str | None) -> float:
    if not column or column not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def exact_decimal_sum(values: pd.Series) -> Decimal:
    """Sum decimal representations without a lossy intermediate float conversion."""
    numbers = []
    for value in values.dropna():
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            continue
        if not number.is_nan():
            numbers.append(number)
    finite = [value for value in numbers if value.is_finite()]
    integer_digits = max((value.adjusted() + 1 for value in finite), default=1)
    fractional_digits = max((-value.as_tuple().exponent for value in finite), default=0)
    with localcontext() as context:
        context.prec = max(28, integer_digits + fractional_digits + len(str(len(numbers))) + 2)
        return sum(numbers, Decimal("0"))


def exact_revenue_ranking(df, dimension, revenue_column):
    if not dimension or not revenue_column or df.empty:
        return []
    rows = [(str(name), exact_decimal_sum(group[revenue_column])) for name, group in df.groupby(dimension, dropna=False)]
    return sorted(sorted(rows, key=lambda row: (row[0].casefold(), row[0])), key=lambda row: row[1], reverse=True)


def safe_count_unique(df: pd.DataFrame, column: str | None) -> int:
    if not column or column not in df.columns:
        return 0

    return int(df[column].dropna().nunique())


def calculate_growth(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0

    return ((current - previous) / previous) * 100


def split_current_previous_period(
    df: pd.DataFrame,
    data_col: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    current, previous, _ = split_equivalent_periods(df, data_col)
    return current, previous


def build_revenue_by_month(
    df: pd.DataFrame,
    data_col: str | None,
    faturamento_col: str | None,
) -> pd.DataFrame:
    if not data_col or not faturamento_col:
        return pd.DataFrame(columns=["periodo", "faturamento"])

    chart_df = df.dropna(subset=[data_col]).copy()

    if chart_df.empty:
        return pd.DataFrame(columns=["periodo", "faturamento"])

    grouped = (
        chart_df.groupby(pd.Grouper(key=data_col, freq="ME"))[faturamento_col]
        .sum()
        .reset_index()
        .sort_values(data_col)
    )

    grouped = grouped.rename(
        columns={
            data_col: "periodo",
            faturamento_col: "faturamento",
        }
    )

    return grouped


def build_revenue_by_store(
    df: pd.DataFrame,
    loja_col: str | None,
    faturamento_col: str | None,
) -> pd.DataFrame:
    if not loja_col or not faturamento_col:
        return pd.DataFrame(columns=["loja", "faturamento"])

    grouped = (
        df.groupby(loja_col, dropna=False)[faturamento_col]
        .sum()
        .reset_index()
        .sort_values(faturamento_col, ascending=True)
    )

    grouped = grouped.rename(
        columns={
            loja_col: "loja",
            faturamento_col: "faturamento",
        }
    )

    grouped["loja"] = grouped["loja"].fillna("Não informado").astype(str)

    return grouped


def build_top_products(
    df: pd.DataFrame,
    produto_col: str | None,
    faturamento_col: str | None,
    limit: int = 8,
) -> pd.DataFrame:
    if not produto_col or not faturamento_col:
        return pd.DataFrame(columns=["produto", "faturamento"])

    grouped = (
        df.groupby(produto_col, dropna=False)[faturamento_col]
        .sum()
        .reset_index()
        .sort_values(faturamento_col, ascending=False)
        .head(limit)
    )

    grouped = grouped.rename(
        columns={
            produto_col: "produto",
            faturamento_col: "faturamento",
        }
    )

    grouped["produto"] = grouped["produto"].fillna("Não informado").astype(str)

    return grouped


def build_revenue_by_day(
    df: pd.DataFrame,
    data_col: str | None,
    faturamento_col: str | None,
) -> pd.DataFrame:
    if not data_col or not faturamento_col:
        return pd.DataFrame(columns=["data", "faturamento"])

    valid_df = df.dropna(subset=[data_col]).copy()

    if valid_df.empty:
        return pd.DataFrame(columns=["data", "faturamento"])

    grouped = (
        valid_df.groupby(valid_df[data_col].dt.date)[faturamento_col]
        .sum()
        .reset_index()
        .sort_values(data_col)
    )

    grouped = grouped.rename(
        columns={
            data_col: "data",
            faturamento_col: "faturamento",
        }
    )

    grouped["data"] = pd.to_datetime(grouped["data"], errors="coerce")

    return grouped


def get_top_record(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    fallback_label: str,
) -> tuple[str, float]:
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return fallback_label, 0.0

    top_row = df.sort_values(value_col, ascending=False).iloc[0]

    label = str(top_row[label_col])
    value = float(top_row[value_col])

    return label, value


def get_bottom_store_performance(
    revenue_by_store: pd.DataFrame,
) -> tuple[str, float]:
    if revenue_by_store.empty:
        return "Não informado", 100.0

    avg_revenue = float(revenue_by_store["faturamento"].mean())

    if avg_revenue <= 0:
        return "Não informado", 100.0

    bottom_row = revenue_by_store.sort_values("faturamento", ascending=True).iloc[0]

    store_name = str(bottom_row["loja"])
    store_value = float(bottom_row["faturamento"])

    performance = (store_value / avg_revenue) * 100

    return store_name, performance


def calculate_core_metrics(
    df: pd.DataFrame,
    columns: ColumnMap,
    revenue_by_store: pd.DataFrame,
    top_products: pd.DataFrame,
    revenue_by_day: pd.DataFrame,
) -> dict[str, Any]:
    faturamento_total = safe_sum(df, columns.faturamento)
    quantidade_total = safe_sum(df, columns.quantidade)

    if columns.pedido:
        total_pedidos = safe_count_unique(df, columns.pedido)
    else:
        total_pedidos = len(df)

    ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0.0
    lojas_ativas = safe_count_unique(df, columns.loja)

    melhor_loja, valor_melhor_loja = get_top_record(
        revenue_by_store,
        "loja",
        "faturamento",
        "Não informado",
    )

    pior_loja, desempenho_pior_loja = get_bottom_store_performance(revenue_by_store)

    produto_top, valor_produto_top = get_top_record(
        top_products,
        "produto",
        "faturamento",
        "Não informado",
    )

    # Float chart aggregates are not a reliable ordering criterion for huge values.
    store_ranking = exact_revenue_ranking(df, columns.loja, columns.faturamento)
    product_ranking = exact_revenue_ranking(df, columns.produto, columns.faturamento)
    if store_ranking:
        melhor_loja, best_value = store_ranking[0]
        worst_value = store_ranking[-1][1]
        pior_loja = next(name for name, value in store_ranking if value == worst_value)
        valor_melhor_loja = float(best_value)
        exact_average = exact_decimal_sum(pd.Series([value for _, value in store_ranking])) / len(store_ranking)
        desempenho_pior_loja = float(worst_value / exact_average * 100) if exact_average else 0.0
    if product_ranking:
        produto_top, top_value = product_ranking[0]
        valor_produto_top = float(top_value)

    participacao_produto_top = (
        (valor_produto_top / faturamento_total) * 100 if faturamento_total > 0 else 0.0
    )

    if revenue_by_day.empty:
        dia_top = pd.Timestamp.today()
        valor_dia_top = 0.0
    else:
        day_row = revenue_by_day.sort_values("faturamento", ascending=False).iloc[0]
        dia_top = pd.to_datetime(day_row["data"], errors="coerce")
        valor_dia_top = float(day_row["faturamento"])

    model = AnalyticalKPIs(
        total_revenue=faturamento_total,
        average_ticket=ticket_medio,
        total_orders=total_pedidos,
        total_quantity=quantidade_total,
        active_stores=lojas_ativas,
        best_store=melhor_loja,
        best_store_value=valor_melhor_loja,
        worst_store=pior_loja,
        worst_store_performance=desempenho_pior_loja,
        top_product=produto_top,
        top_product_value=valor_produto_top,
        top_product_share=participacao_produto_top,
        top_day=dia_top,
        top_day_value=valor_dia_top,
        ticket_methodology=(
            "receita por pedido único"
            if columns.pedido
            else "receita por registro de venda"
        ),
    )
    return model.to_legacy_dict()


def calculate_growth_metrics(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    columns: ColumnMap,
) -> dict[str, float]:
    current_revenue = safe_sum(current_df, columns.faturamento)
    previous_revenue = safe_sum(previous_df, columns.faturamento)

    current_quantity = safe_sum(current_df, columns.quantidade)
    previous_quantity = safe_sum(previous_df, columns.quantidade)

    current_orders = (
        safe_count_unique(current_df, columns.pedido)
        if columns.pedido
        else len(current_df)
    )
    previous_orders = (
        safe_count_unique(previous_df, columns.pedido)
        if columns.pedido
        else len(previous_df)
    )

    current_ticket = current_revenue / current_orders if current_orders > 0 else 0.0
    previous_ticket = previous_revenue / previous_orders if previous_orders > 0 else 0.0

    current_stores = safe_count_unique(current_df, columns.loja)
    previous_stores = safe_count_unique(previous_df, columns.loja)

    model = GrowthMetrics(
        revenue=calculate_growth(current_revenue, previous_revenue),
        average_ticket=calculate_growth(current_ticket, previous_ticket),
        orders=calculate_growth(current_orders, previous_orders),
        quantity=calculate_growth(current_quantity, previous_quantity),
        stores=calculate_growth(current_stores, previous_stores),
        comparison_available=bool(len(current_df) > 0 and len(previous_df) > 0),
    )
    return model.to_legacy_dict()


def build_quality_report(df: pd.DataFrame, columns: ColumnMap) -> dict[str, Any]:
    imported_report = df.attrs.get("quality_report")
    if isinstance(imported_report, DataQualityReport):
        report = imported_report.to_dict()
        report["linhas_analisadas"] = len(df)
        report["colunas"] = len(df.columns)
        return report

    required = {
        "data": columns.data,
        "loja": columns.loja,
        "produto": columns.produto,
        "faturamento": columns.faturamento,
        "quantidade": columns.quantidade,
    }

    missing = [name for name, column in required.items() if not column]

    model = DataQualityReport(
        received_records=len(df),
        valid_records=len(df),
        discarded_records=0,
        duplicate_records=0,
        detected_fields=required,
        missing_fields=tuple(missing),
        rejection_reasons={},
        schema_score=round(((len(required) - len(missing)) / len(required)) * 100, 1),
    )
    return {**model.to_dict(), "linhas_analisadas": len(df), "colunas": len(df.columns)}


def build_kpi_cards(metricas: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "icon": "💰",
            "title": "Faturamento Total",
            "metric_key": "faturamento_total",
            "growth_key": "crescimento_faturamento",
            "badge": "Receita",
            "featured": True,
        },
        {
            "icon": "🎯",
            "title": "Ticket Médio",
            "metric_key": "ticket_medio",
            "growth_key": "crescimento_ticket",
            "badge": "Eficiência",
            "featured": True,
        },
        {
            "icon": "📦",
            "title": "Pedidos",
            "metric_key": "total_pedidos",
            "growth_key": "crescimento_pedidos",
            "badge": "Pedidos",
            "featured": True,
        },
        {
            "icon": "🛒",
            "title": "Quantidade Vendida",
            "metric_key": "quantidade_total",
            "growth_key": "crescimento_quantidade",
            "badge": "Volume",
            "featured": False,
        },
        {
            "icon": "🏪",
            "title": "Lojas Ativas",
            "metric_key": "lojas_ativas",
            "growth_key": "crescimento_lojas",
            "badge": "Cobertura",
            "featured": False,
        },
    ]


def construir_analytics_state(df: pd.DataFrame) -> dict[str, Any]:
    prepared_df, columns = prepare_dataframe(df)

    revenue_by_month = build_revenue_by_month(
        prepared_df,
        columns.data,
        columns.faturamento,
    )
    revenue_by_store = build_revenue_by_store(
        prepared_df,
        columns.loja,
        columns.faturamento,
    )
    top_products = build_top_products(
        prepared_df,
        columns.produto,
        columns.faturamento,
    )
    revenue_by_day = build_revenue_by_day(
        prepared_df,
        columns.data,
        columns.faturamento,
    )

    metricas = calculate_core_metrics(
        prepared_df,
        columns,
        revenue_by_store,
        top_products,
        revenue_by_day,
    )
    exact_revenue = exact_decimal_sum(prepared_df[columns.faturamento]) if columns.faturamento else Decimal("0")
    order_denominator = metricas["total_pedidos"]
    metricas["faturamento_total_exato"] = exact_revenue
    metricas["ticket_medio_exato"] = exact_revenue / order_denominator if order_denominator else Decimal("0")

    current_df, previous_df, comparison = split_equivalent_periods(prepared_df, columns.data)
    growth_metrics = calculate_growth_metrics(current_df, previous_df, columns)

    metricas.update(growth_metrics)

    charts = {
        "revenue_by_month": revenue_by_month,
        "revenue_by_store": revenue_by_store,
        "top_products": top_products,
        "revenue_by_day": revenue_by_day,
    }

    quality = build_quality_report(prepared_df, columns)

    return {
        **metricas,
        "metricas": metricas,
        "charts": charts,
        "quality": quality,
        "columns": columns,
        "kpi_cards": build_kpi_cards(metricas),
        "prepared_df": prepared_df,
        "comparison": comparison.to_dict(),
        "typed": {
            "comparison": comparison,
            "quality": prepared_df.attrs.get("quality_report"),
        },
    }


def calcular_metricas(df: pd.DataFrame) -> dict[str, Any]:
    return construir_analytics_state(df)
