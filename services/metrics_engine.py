from dataclasses import dataclass
from typing import Any

import pandas as pd

try:
    from services.schema_analyzer import analyze_schema
except Exception:
    analyze_schema = None


@dataclass(frozen=True)
class ColumnMap:
    data: str | None
    loja: str | None
    produto: str | None
    faturamento: str | None
    quantidade: str | None
    pedido: str | None
    categoria: str | None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def find_column(df: pd.DataFrame, possible_names: list[str]) -> str | None:
    normalized_targets = {name.strip().lower() for name in possible_names}

    for column in df.columns:
        if str(column).strip().lower() in normalized_targets:
            return column

    return None


def get_schema_analysis(df: pd.DataFrame) -> dict[str, Any]:
    if analyze_schema is None:
        return {
            "metric_column": None,
            "date_column": None,
            "primary_dimension": None,
            "secondary_dimension": None,
            "category_dimension": None,
            "dimension_columns": [],
            "numeric_columns": [],
            "date_columns": [],
            "text_columns": [],
            "secondary_metrics": [],
            "domain": "generico",
            "confidence": 0.0,
            "metric_confidence": 0.0,
            "date_confidence": 0.0,
            "primary_dimension_confidence": 0.0,
            "secondary_dimension_confidence": 0.0,
            "category_dimension_confidence": 0.0,
            "columns": [],
            "warnings": ["schema_analyzer.py não está disponível."],
        }

    schema = analyze_schema(df)

    if hasattr(schema, "to_dict"):
        return schema.to_dict()

    return dict(schema)


def get_column_map(df: pd.DataFrame) -> ColumnMap:
    schema = get_schema_analysis(df)

    data = find_column(df, ["data", "date", "dt_venda", "data_venda"])
    loja = find_column(df, ["loja", "store", "unidade", "filial"])
    produto = find_column(df, ["produto", "product", "item", "sku"])
    faturamento = find_column(
        df,
        ["faturamento", "receita", "vendas", "valor", "total", "revenue"],
    )
    quantidade = find_column(
        df,
        ["quantidade", "qtd", "volume", "itens", "qty", "quantity"],
    )
    pedido = find_column(
        df,
        ["pedido", "id_pedido", "order_id", "venda", "id_venda"],
    )
    categoria = find_column(df, ["categoria", "category", "segmento", "grupo"])

    if not data:
        data = schema.get("date_column")

    if not faturamento:
        faturamento = schema.get("metric_column")

    if not loja:
        loja = schema.get("primary_dimension")

    if not produto:
        produto = schema.get("secondary_dimension")

    if not categoria:
        categoria = schema.get("category_dimension")

    dimensions = schema.get("dimension_columns", [])

    if not categoria and len(dimensions) >= 3:
        categoria = dimensions[2]

    return ColumnMap(
        data=data,
        loja=loja,
        produto=produto,
        faturamento=faturamento,
        quantidade=quantidade,
        pedido=pedido,
        categoria=categoria,
    )


def prepare_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, ColumnMap, dict[str, Any]]:
    df = normalize_columns(df)
    schema = get_schema_analysis(df)
    columns = get_column_map(df)

    if columns.data and columns.data in df.columns:
        df[columns.data] = pd.to_datetime(
            df[columns.data],
            errors="coerce",
            dayfirst=True,
        )

    if columns.faturamento and columns.faturamento in df.columns:
        df[columns.faturamento] = pd.to_numeric(
            df[columns.faturamento],
            errors="coerce",
        ).fillna(0)

    if columns.quantidade and columns.quantidade in df.columns:
        df[columns.quantidade] = pd.to_numeric(
            df[columns.quantidade],
            errors="coerce",
        ).fillna(0)

    for metric in schema.get("secondary_metrics", []) or []:
        if metric and metric in df.columns:
            df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

    if not columns.quantidade:
        df["_Quantidade_Automatica"] = 1
        columns = ColumnMap(
            data=columns.data,
            loja=columns.loja,
            produto=columns.produto,
            faturamento=columns.faturamento,
            quantidade="_Quantidade_Automatica",
            pedido=columns.pedido,
            categoria=columns.categoria,
        )

    return df, columns, schema


def safe_sum(df: pd.DataFrame, column: str | None) -> float:
    if not column or column not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def safe_count_unique(df: pd.DataFrame, column: str | None) -> int:
    if not column or column not in df.columns:
        return 0

    return int(df[column].dropna().nunique())


def calculate_growth(current: float, previous: float) -> float:
    if previous == 0 and current > 0:
        return 100.0

    if previous == 0:
        return 0.0

    return ((current - previous) / previous) * 100


def split_current_previous_period(
    df: pd.DataFrame,
    data_col: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not data_col or data_col not in df.columns:
        midpoint = len(df) // 2
        previous_df = df.iloc[:midpoint].copy()
        current_df = df.iloc[midpoint:].copy()
        return current_df, previous_df

    valid_df = df.dropna(subset=[data_col]).sort_values(data_col).copy()

    if valid_df.empty or len(valid_df) < 2:
        return df.copy(), pd.DataFrame(columns=df.columns)

    start_date = valid_df[data_col].min()
    end_date = valid_df[data_col].max()

    if pd.isna(start_date) or pd.isna(end_date) or start_date == end_date:
        midpoint = len(valid_df) // 2
        previous_df = valid_df.iloc[:midpoint].copy()
        current_df = valid_df.iloc[midpoint:].copy()
        return current_df, previous_df

    midpoint_date = start_date + ((end_date - start_date) / 2)

    previous_df = valid_df[valid_df[data_col] <= midpoint_date].copy()
    current_df = valid_df[valid_df[data_col] > midpoint_date].copy()

    return current_df, previous_df


def build_revenue_by_month(
    df: pd.DataFrame,
    data_col: str | None,
    metric_col: str | None,
) -> pd.DataFrame:
    if not data_col or not metric_col:
        return pd.DataFrame(columns=["periodo", "faturamento"])

    if data_col not in df.columns or metric_col not in df.columns:
        return pd.DataFrame(columns=["periodo", "faturamento"])

    chart_df = df.dropna(subset=[data_col]).copy()

    if chart_df.empty:
        return pd.DataFrame(columns=["periodo", "faturamento"])

    grouped = (
        chart_df.groupby(pd.Grouper(key=data_col, freq="ME"))[metric_col]
        .sum()
        .reset_index()
        .sort_values(data_col)
    )

    grouped = grouped.rename(
        columns={
            data_col: "periodo",
            metric_col: "faturamento",
        }
    )

    return grouped


def build_dynamic_dimension_summary(
    df: pd.DataFrame,
    dimension_col: str | None,
    metric_col: str | None,
    label_name: str = "dimensao",
    value_name: str = "valor",
    limit: int = 12,
    ascending: bool = False,
) -> pd.DataFrame:
    if not dimension_col or not metric_col:
        return pd.DataFrame(columns=[label_name, value_name])

    if dimension_col not in df.columns or metric_col not in df.columns:
        return pd.DataFrame(columns=[label_name, value_name])

    grouped = (
        df.groupby(dimension_col, dropna=False)[metric_col]
        .sum()
        .reset_index()
        .sort_values(metric_col, ascending=ascending)
        .head(limit)
    )

    grouped = grouped.rename(
        columns={
            dimension_col: label_name,
            metric_col: value_name,
        }
    )

    grouped[label_name] = grouped[label_name].fillna("Não informado").astype(str)

    return grouped


def build_revenue_by_store(
    df: pd.DataFrame,
    dimension_col: str | None,
    metric_col: str | None,
) -> pd.DataFrame:
    return build_dynamic_dimension_summary(
        df=df,
        dimension_col=dimension_col,
        metric_col=metric_col,
        label_name="loja",
        value_name="faturamento",
        limit=30,
        ascending=True,
    )


def build_top_products(
    df: pd.DataFrame,
    dimension_col: str | None,
    metric_col: str | None,
    limit: int = 8,
) -> pd.DataFrame:
    return build_dynamic_dimension_summary(
        df=df,
        dimension_col=dimension_col,
        metric_col=metric_col,
        label_name="produto",
        value_name="faturamento",
        limit=limit,
        ascending=False,
    )


def build_revenue_by_category(
    df: pd.DataFrame,
    category_col: str | None,
    metric_col: str | None,
) -> pd.DataFrame:
    return build_dynamic_dimension_summary(
        df=df,
        dimension_col=category_col,
        metric_col=metric_col,
        label_name="categoria",
        value_name="faturamento",
        limit=12,
        ascending=False,
    )


def build_revenue_by_day(
    df: pd.DataFrame,
    data_col: str | None,
    metric_col: str | None,
) -> pd.DataFrame:
    if not data_col or not metric_col:
        return pd.DataFrame(columns=["data", "faturamento"])

    if data_col not in df.columns or metric_col not in df.columns:
        return pd.DataFrame(columns=["data", "faturamento"])

    valid_df = df.dropna(subset=[data_col]).copy()

    if valid_df.empty:
        return pd.DataFrame(columns=["data", "faturamento"])

    grouped = (
        valid_df.groupby(valid_df[data_col].dt.date)[metric_col]
        .sum()
        .reset_index()
        .sort_values(data_col)
    )

    grouped = grouped.rename(
        columns={
            data_col: "data",
            metric_col: "faturamento",
        }
    )

    grouped["data"] = pd.to_datetime(grouped["data"], errors="coerce")

    return grouped


def get_top_record(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    fallback_label: str = "Não informado",
) -> tuple[str, float]:
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return fallback_label, 0.0

    top_row = df.sort_values(value_col, ascending=False).iloc[0]

    label = str(top_row[label_col])
    value = float(top_row[value_col])

    return label, value


def get_bottom_dimension_performance(
    summary_df: pd.DataFrame,
    label_col: str,
    value_col: str,
) -> tuple[str, float]:
    if summary_df.empty or label_col not in summary_df.columns or value_col not in summary_df.columns:
        return "Não informado", 100.0

    avg_value = float(summary_df[value_col].mean())

    if avg_value <= 0:
        return "Não informado", 100.0

    bottom_row = summary_df.sort_values(value_col, ascending=True).iloc[0]

    label = str(bottom_row[label_col])
    value = float(bottom_row[value_col])

    performance = (value / avg_value) * 100

    return label, performance


def get_bottom_store_performance(revenue_by_store: pd.DataFrame) -> tuple[str, float]:
    return get_bottom_dimension_performance(
        summary_df=revenue_by_store,
        label_col="loja",
        value_col="faturamento",
    )


def calculate_core_metrics(
    df: pd.DataFrame,
    columns: ColumnMap,
    revenue_by_store: pd.DataFrame,
    top_products: pd.DataFrame,
    revenue_by_day: pd.DataFrame,
    revenue_by_category: pd.DataFrame,
    schema: dict[str, Any],
    primary_dimension_summary: pd.DataFrame,
    secondary_dimension_summary: pd.DataFrame,
) -> dict[str, Any]:
    metric_col = schema.get("metric_column") or columns.faturamento
    primary_dimension_col = schema.get("primary_dimension") or columns.loja
    secondary_dimension_col = schema.get("secondary_dimension") or columns.produto
    category_dimension_col = schema.get("category_dimension") or columns.categoria
    domain = schema.get("domain", "generico")

    faturamento_total = safe_sum(df, metric_col)
    quantidade_total = safe_sum(df, columns.quantidade)

    if columns.pedido:
        total_pedidos = safe_count_unique(df, columns.pedido)
    else:
        total_pedidos = len(df)

    ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0.0

    primary_dimension_count = safe_count_unique(df, primary_dimension_col)
    secondary_dimension_count = safe_count_unique(df, secondary_dimension_col)
    category_dimension_count = safe_count_unique(df, category_dimension_col)

    top_primary_dimension, top_primary_dimension_value = get_top_record(
        primary_dimension_summary,
        "dimensao",
        "valor",
        "Não informado",
    )

    top_secondary_dimension, top_secondary_dimension_value = get_top_record(
        secondary_dimension_summary,
        "dimensao",
        "valor",
        "Não informado",
    )

    bottom_primary_dimension, bottom_primary_dimension_performance = (
        get_bottom_dimension_performance(
            primary_dimension_summary,
            "dimensao",
            "valor",
        )
    )

    top_secondary_dimension_share = (
        (top_secondary_dimension_value / faturamento_total) * 100
        if faturamento_total > 0
        else 0.0
    )

    melhor_categoria, valor_melhor_categoria = get_top_record(
        revenue_by_category,
        "categoria",
        "faturamento",
        "Categoria não identificada",
    )

    if revenue_by_day.empty:
        dia_top = pd.Timestamp.today()
        valor_dia_top = 0.0
    else:
        day_row = revenue_by_day.sort_values("faturamento", ascending=False).iloc[0]
        dia_top = pd.to_datetime(day_row["data"], errors="coerce")
        valor_dia_top = float(day_row["faturamento"])

    return {
        "faturamento_total": faturamento_total,
        "ticket_medio": ticket_medio,
        "total_pedidos": total_pedidos,
        "quantidade_total": quantidade_total,
        "lojas_ativas": primary_dimension_count,
        "primary_dimension_count": primary_dimension_count,
        "secondary_dimension_count": secondary_dimension_count,
        "category_dimension_count": category_dimension_count,
        "top_primary_dimension": top_primary_dimension,
        "top_primary_dimension_value": top_primary_dimension_value,
        "top_secondary_dimension": top_secondary_dimension,
        "top_secondary_dimension_value": top_secondary_dimension_value,
        "top_secondary_dimension_share": top_secondary_dimension_share,
        "bottom_primary_dimension": bottom_primary_dimension,
        "bottom_primary_dimension_performance": bottom_primary_dimension_performance,
        "melhor_loja": top_primary_dimension,
        "valor_melhor_loja": top_primary_dimension_value,
        "pior_loja": bottom_primary_dimension,
        "desempenho_pior_loja": bottom_primary_dimension_performance,
        "produto_top": top_secondary_dimension,
        "valor_produto_top": top_secondary_dimension_value,
        "participacao_produto_top": top_secondary_dimension_share,
        "dia_top": dia_top,
        "valor_dia_top": valor_dia_top,
        "melhor_categoria": melhor_categoria,
        "valor_melhor_categoria": valor_melhor_categoria,
        "metric_column": metric_col,
        "primary_dimension": primary_dimension_col,
        "secondary_dimension": secondary_dimension_col,
        "category_dimension": category_dimension_col,
        "secondary_metrics": schema.get("secondary_metrics", []),
        "domain": domain,
        "schema_confidence": schema.get("confidence", 0),
        "metric_confidence": schema.get("metric_confidence", 0),
        "date_confidence": schema.get("date_confidence", 0),
        "primary_dimension_confidence": schema.get("primary_dimension_confidence", 0),
        "secondary_dimension_confidence": schema.get("secondary_dimension_confidence", 0),
        "category_dimension_confidence": schema.get("category_dimension_confidence", 0),
    }


def calculate_growth_metrics(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    columns: ColumnMap,
    schema: dict[str, Any],
) -> dict[str, float]:
    metric_col = schema.get("metric_column") or columns.faturamento
    primary_dimension_col = schema.get("primary_dimension") or columns.loja
    secondary_dimension_col = schema.get("secondary_dimension") or columns.produto
    category_dimension_col = schema.get("category_dimension") or columns.categoria

    current_revenue = safe_sum(current_df, metric_col)
    previous_revenue = safe_sum(previous_df, metric_col)

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

    current_primary_count = safe_count_unique(current_df, primary_dimension_col)
    previous_primary_count = safe_count_unique(previous_df, primary_dimension_col)

    current_secondary_count = safe_count_unique(current_df, secondary_dimension_col)
    previous_secondary_count = safe_count_unique(previous_df, secondary_dimension_col)

    current_category_count = safe_count_unique(current_df, category_dimension_col)
    previous_category_count = safe_count_unique(previous_df, category_dimension_col)

    return {
        "crescimento_faturamento": calculate_growth(current_revenue, previous_revenue),
        "crescimento_ticket": calculate_growth(current_ticket, previous_ticket),
        "crescimento_pedidos": calculate_growth(current_orders, previous_orders),
        "crescimento_quantidade": calculate_growth(current_quantity, previous_quantity),
        "crescimento_lojas": calculate_growth(current_primary_count, previous_primary_count),
        "crescimento_primary_dimension": calculate_growth(
            current_primary_count,
            previous_primary_count,
        ),
        "crescimento_secondary_dimension": calculate_growth(
            current_secondary_count,
            previous_secondary_count,
        ),
        "crescimento_category_dimension": calculate_growth(
            current_category_count,
            previous_category_count,
        ),
    }


def build_quality_report(
    df: pd.DataFrame,
    columns: ColumnMap,
    schema: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "data": columns.data,
        "dimensão principal": schema.get("primary_dimension") or columns.loja,
        "dimensão secundária": schema.get("secondary_dimension") or columns.produto,
        "métrica principal": schema.get("metric_column") or columns.faturamento,
        "categoria": schema.get("category_dimension") or columns.categoria,
        "quantidade": columns.quantidade,
    }

    missing = [name for name, column in required.items() if not column]

    return {
        "linhas": len(df),
        "colunas": len(df.columns),
        "colunas_detectadas": required,
        "colunas_ausentes": missing,
        "score_schema": round(((len(required) - len(missing)) / len(required)) * 100, 1),
        "schema_domain": schema.get("domain", "generico"),
        "schema_confidence": schema.get("confidence", 0),
        "metric_confidence": schema.get("metric_confidence", 0),
        "date_confidence": schema.get("date_confidence", 0),
        "primary_dimension_confidence": schema.get("primary_dimension_confidence", 0),
        "secondary_dimension_confidence": schema.get("secondary_dimension_confidence", 0),
        "category_dimension_confidence": schema.get("category_dimension_confidence", 0),
        "secondary_metrics": schema.get("secondary_metrics", []),
        "schema_warnings": schema.get("warnings", []),
    }


def build_kpi_cards(metricas: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    domain = schema.get("domain", "generico")
    metric_label = schema.get("metric_column") or "Métrica Principal"
    primary_dimension = schema.get("primary_dimension") or "Dimensão Principal"
    secondary_dimension = schema.get("secondary_dimension") or "Dimensão Secundária"

    domain_badges = {
        "vendas": "Receita",
        "financeiro": "Financeiro",
        "rh": "RH",
        "estoque": "Estoque",
        "crm": "CRM",
        "projetos": "Projetos",
        "generico": "Universal",
    }

    return [
        {
            "icon": "💰" if domain in ["vendas", "financeiro"] else "📊",
            "title": f"Total de {metric_label}",
            "metric_key": "faturamento_total",
            "growth_key": "crescimento_faturamento",
            "badge": domain_badges.get(domain, "Métrica"),
            "featured": True,
        },
        {
            "icon": "🎯",
            "title": "Média por Registro",
            "metric_key": "ticket_medio",
            "growth_key": "crescimento_ticket",
            "badge": "Eficiência",
            "featured": True,
        },
        {
            "icon": "📄",
            "title": "Registros Analisados",
            "metric_key": "total_pedidos",
            "growth_key": "crescimento_pedidos",
            "badge": "Base",
            "featured": True,
        },
        {
            "icon": "🧮",
            "title": "Quantidade Total",
            "metric_key": "quantidade_total",
            "growth_key": "crescimento_quantidade",
            "badge": "Volume",
            "featured": False,
        },
        {
            "icon": "🧭",
            "title": f"Qtd. {primary_dimension}",
            "metric_key": "primary_dimension_count",
            "growth_key": "crescimento_primary_dimension",
            "badge": "Dimensão",
            "featured": False,
        },
        {
            "icon": "🏆",
            "title": f"Top {secondary_dimension}",
            "metric_key": "top_secondary_dimension",
            "growth_key": None,
            "badge": "Ranking",
            "featured": False,
        },
        {
            "icon": "🥇",
            "title": f"Top {primary_dimension}",
            "metric_key": "top_primary_dimension",
            "growth_key": None,
            "badge": "Destaque",
            "featured": False,
        },
        {
            "icon": "🧠",
            "title": "Domínio Detectado",
            "metric_key": "domain",
            "growth_key": None,
            "badge": "Schema",
            "featured": False,
        },
    ]


def construir_analytics_state(df: pd.DataFrame) -> dict[str, Any]:
    prepared_df, columns, schema = prepare_dataframe(df)

    # Correção importante:
    # O schema universal pode classificar Produto como dimensão principal porque tem score alto.
    # Para domínio de vendas, quando existem colunas explícitas Loja e Produto, elas devem mandar.
    store_dimension = columns.loja or schema.get("primary_dimension")
    product_dimension = columns.produto or schema.get("secondary_dimension")
    primary_dimension = store_dimension or schema.get("primary_dimension")
    secondary_dimension = product_dimension or schema.get("secondary_dimension")

    category_dimension = columns.categoria or schema.get("category_dimension")
    if category_dimension in [primary_dimension, secondary_dimension]:
        category_dimension = None

    metric_column = schema.get("metric_column") or columns.faturamento

    revenue_by_month = build_revenue_by_month(
        prepared_df,
        columns.data,
        metric_column,
    )

    revenue_by_store = build_revenue_by_store(
        prepared_df,
        store_dimension,
        metric_column,
    )

    top_products = build_top_products(
        prepared_df,
        product_dimension,
        metric_column,
    )

    revenue_by_day = build_revenue_by_day(
        prepared_df,
        columns.data,
        metric_column,
    )

    revenue_by_category = build_revenue_by_category(
        prepared_df,
        category_dimension,
        metric_column,
    )

    primary_dimension_summary = build_dynamic_dimension_summary(
        prepared_df,
        primary_dimension,
        metric_column,
        label_name="dimensao",
        value_name="valor",
        limit=12,
    )

    secondary_dimension_summary = build_dynamic_dimension_summary(
        prepared_df,
        secondary_dimension,
        metric_column,
        label_name="dimensao",
        value_name="valor",
        limit=12,
    )

    category_dimension_summary = build_dynamic_dimension_summary(
        prepared_df,
        category_dimension,
        metric_column,
        label_name="dimensao",
        value_name="valor",
        limit=12,
    )

    metricas = calculate_core_metrics(
        prepared_df,
        columns,
        revenue_by_store,
        top_products,
        revenue_by_day,
        revenue_by_category,
        schema,
        primary_dimension_summary,
        secondary_dimension_summary,
    )

    current_df, previous_df = split_current_previous_period(prepared_df, columns.data)

    growth_metrics = calculate_growth_metrics(
        current_df,
        previous_df,
        columns,
        schema,
    )

    metricas.update(growth_metrics)

    charts = {
        "revenue_by_month": revenue_by_month,
        "revenue_by_store": revenue_by_store,
        "top_products": top_products,
        "revenue_by_day": revenue_by_day,
        "revenue_by_category": revenue_by_category,
        "primary_dimension_summary": primary_dimension_summary,
        "secondary_dimension_summary": secondary_dimension_summary,
        "category_dimension_summary": category_dimension_summary,
    }

    quality = build_quality_report(prepared_df, columns, schema)

    return {
        **metricas,
        "metricas": metricas,
        "charts": charts,
        "quality": quality,
        "columns": columns,
        "schema": {
            **schema,
            "primary_dimension": primary_dimension,
            "secondary_dimension": secondary_dimension,
            "category_dimension": category_dimension,
            "store_dimension": store_dimension,
            "product_dimension": product_dimension,
        },
        "prepared_df": prepared_df,
        "kpi_cards": build_kpi_cards(metricas, schema),
    }


def calcular_metricas(df: pd.DataFrame) -> dict[str, Any]:
    return construir_analytics_state(df)