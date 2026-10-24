from __future__ import annotations

import html
import math
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import _log_currency_ticks, apply_layout
from domain.periods import split_equivalent_periods
from services.anomalies import detect_extreme_monetary_values
from services.formatter import moeda, moeda_resumida, numero
from services.metrics_engine import exact_decimal_sum


@dataclass(frozen=True)
class ProductKPIs:
    revenue: float
    quantity: float
    distinct_products: int
    average_revenue_per_product: float | None


def _percentage_change(current: float, previous: float) -> float | None:
    return None if previous == 0 else ((current - previous) / previous) * 100


def build_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Posição", "Produto", "Receita", "Quantidade", "Participação na receita",
        "Participação na quantidade", "Receita média por unidade", "Registros",
    ]
    if df.empty or not {"Produto", "Faturamento", "Quantidade"}.issubset(df.columns):
        return pd.DataFrame(columns=columns)
    valid = df.dropna(subset=["Produto"]).copy()
    valid["Produto"] = valid["Produto"].astype(str).str.strip()
    valid = valid[valid["Produto"].ne("")]
    if valid.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        valid.groupby("Produto", as_index=False)
        .agg(
            Receita=("Faturamento", "sum"),
            Quantidade=("Quantidade", "sum"),
            Registros=("Produto", "size"),
        )
        .sort_values(["Receita", "Produto"], ascending=[False, True], kind="mergesort")
        .reset_index(drop=True)
    )
    revenue_total = float(summary["Receita"].sum())
    quantity_total = float(summary["Quantidade"].sum())
    summary.insert(0, "Posição", summary.index + 1)
    summary["Participação na receita"] = (
        summary["Receita"].div(revenue_total).mul(100) if revenue_total else 0.0
    )
    summary["Participação na quantidade"] = (
        summary["Quantidade"].div(quantity_total).mul(100) if quantity_total else 0.0
    )
    summary["Receita média por unidade"] = summary["Receita"].div(
        summary["Quantidade"].replace(0, pd.NA)
    )
    return summary[columns]


def calculate_product_kpis(df: pd.DataFrame) -> ProductKPIs:
    summary = build_product_summary(df)
    revenue = float(summary["Receita"].sum()) if not summary.empty else 0.0
    quantity = float(summary["Quantidade"].sum()) if not summary.empty else 0.0
    distinct = len(summary)
    average = revenue / distinct if distinct else None
    return ProductKPIs(revenue, quantity, distinct, average)


def build_product_kpi_comparison(df: pd.DataFrame) -> tuple[dict[str, float | None], str, bool]:
    current, previous, period = split_equivalent_periods(df, "Data")
    if not period.available:
        return {}, period.label, False
    now, before = calculate_product_kpis(current), calculate_product_kpis(previous)
    values = {
        "revenue": _percentage_change(now.revenue, before.revenue),
        "quantity": _percentage_change(now.quantity, before.quantity),
        "distinct_products": _percentage_change(now.distinct_products, before.distinct_products),
        "average_revenue_per_product": _percentage_change(
            now.average_revenue_per_product or 0.0,
            before.average_revenue_per_product or 0.0,
        ),
    }
    return values, period.label, True


def build_product_concentration(summary: pd.DataFrame) -> dict[str, float]:
    shares = summary["Participação na receita"] if not summary.empty else pd.Series(dtype=float)
    return {
        "leader": float(shares.head(1).sum()),
        "top3": float(shares.head(3).sum()),
        "top5": float(shares.head(5).sum()),
    }


def build_product_comparison(df: pd.DataFrame) -> tuple[pd.DataFrame, str, bool]:
    current, previous, period = split_equivalent_periods(df, "Data")
    columns = [
        "Produto", "Receita atual", "Receita anterior", "Diferença de receita",
        "Variação da receita (%)", "Quantidade atual", "Quantidade anterior",
        "Diferença de quantidade", "Variação da quantidade (%)",
    ]
    if not period.available:
        return pd.DataFrame(columns=columns), period.label, False

    def grouped(frame: pd.DataFrame, suffix: str) -> pd.DataFrame:
        return frame.groupby("Produto", as_index=False).agg(
            **{f"Receita {suffix}": ("Faturamento", "sum"),
               f"Quantidade {suffix}": ("Quantidade", "sum")}
        )

    result = grouped(current, "atual").merge(grouped(previous, "anterior"), on="Produto", how="outer").fillna(0)
    result["Diferença de receita"] = result["Receita atual"] - result["Receita anterior"]
    result["Diferença de quantidade"] = result["Quantidade atual"] - result["Quantidade anterior"]
    result["Variação da receita (%)"] = result.apply(
        lambda row: _percentage_change(row["Receita atual"], row["Receita anterior"]), axis=1
    )
    result["Variação da quantidade (%)"] = result.apply(
        lambda row: _percentage_change(row["Quantidade atual"], row["Quantidade anterior"]), axis=1
    )
    result = result.sort_values(["Receita atual", "Produto"], ascending=[False, True], kind="mergesort")
    return result[columns].reset_index(drop=True), period.label, True


def build_product_time_series(
    df: pd.DataFrame, products: list[str], metric: str, excluded_indices: set | None = None
) -> pd.DataFrame:
    value_column = "Faturamento" if metric == "Receita" else "Quantidade"
    work = df[df["Produto"].astype(str).isin(products)].copy()
    if excluded_indices:
        work = work.drop(index=list(excluded_indices), errors="ignore")
    work = work.dropna(subset=["Data"])
    if work.empty:
        return pd.DataFrame(columns=["Período", "Produto", metric])
    result = (
        work.groupby([pd.Grouper(key="Data", freq="ME"), "Produto"], as_index=False)[value_column]
        .sum()
        .rename(columns={"Data": "Período", value_column: metric})
        .sort_values(["Período", "Produto"])
    )
    return result


def paginate_products(summary: pd.DataFrame, page: int, page_size: int) -> pd.DataFrame:
    safe_size = max(int(page_size), 1)
    total_pages = max(math.ceil(len(summary) / safe_size), 1)
    safe_page = min(max(int(page), 1), total_pages)
    start = (safe_page - 1) * safe_size
    return summary.iloc[start : start + safe_size].copy()


def _growth_badge(value: float | None, available: bool) -> tuple[str, str]:
    if not available or value is None:
        return "Comparação indisponível", "neutral"
    tone = "positive" if value > 0 else "negative" if value < 0 else "neutral"
    arrow = "↑" if value > 0 else "↓" if value < 0 else "→"
    return f"{arrow} {abs(value):.1f}%".replace(".", ","), tone


def _kpi(label: str, value: str, full: str, badge: str, tone: str, icon: str) -> str:
    return f"""
    <div class="product-kpi"><div class="product-kpi-head"><span>{icon}</span><strong>{html.escape(label)}</strong>
    <em class="fusion-delta fusion-delta-{tone}">{html.escape(badge)}</em></div>
    <div class="product-kpi-value" title="{html.escape(full)}">{html.escape(value)}</div>
    <div class="product-kpi-foot">Valor integral disponível ao passar o cursor</div></div>
    """


def _ranking_figure(summary: pd.DataFrame, metric: str, limit: int) -> go.Figure:
    data = summary.sort_values([metric, "Produto"], ascending=[False, True]).head(limit).sort_values(metric)
    currency = metric == "Receita"
    compact = data[metric].map(moeda_resumida if currency else numero)
    full = data[metric].map(moeda if currency else numero)
    palette = ["#22D3EE", "#38BDF8", "#3B82F6", "#6366F1", "#8B5CF6", "#A855F7"]
    colors = [palette[index % len(palette)] for index in range(len(data))]
    fig = go.Figure(go.Bar(
        x=data[metric], y=data["Produto"], orientation="h", text=compact, customdata=full,
        textposition="auto", cliponaxis=False,
        marker=dict(color=colors),
        hovertemplate=f"<b>%{{y}}</b><br>{metric}: %{{customdata}}<extra></extra>",
    ))
    apply_layout(fig, f"Ranking por {metric.lower()}", height=350)
    fig.update_layout(margin=dict(l=18, r=32, t=58, b=42))
    fig.update_yaxes(title=None, automargin=True)
    if currency and (data[metric] > 0).all():
        ticks, labels = _log_currency_ticks(data[metric])
        fig.update_xaxes(type="log", tickvals=ticks, ticktext=labels, title="Receita (R$ · escala log)")
    else:
        fig.update_xaxes(title="Unidades", tickformat=",.0f")
    return fig


def _concentration_figure(summary: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=summary["Produto"], values=summary["Receita"], hole=.66,
        textinfo="none", customdata=summary["Receita"].map(moeda),
        hovertemplate="<b>%{label}</b><br>Receita: %{customdata}<br>Participação: %{percent}<extra></extra>",
        marker=dict(colors=["#22D3EE", "#3B82F6", "#6366F1", "#8B5CF6", "#D946EF", "#10B981"]),
    ))
    apply_layout(fig, "Distribuição da receita", height=350)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", x=.5, xanchor="center", y=-.04, yanchor="top"),
        margin=dict(l=8, r=8, t=58, b=60),
    )
    return fig


def _time_figure(data: pd.DataFrame, metric: str, log_scale: bool) -> go.Figure:
    fig = go.Figure()
    month_names = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
    for product, group in data.groupby("Produto", sort=True):
        full = group[metric].map(moeda if metric == "Receita" else numero)
        fig.add_trace(go.Scatter(
            x=group["Período"], y=group[metric], name=str(product), mode="lines+markers",
            line=dict(width=2, shape="linear"), customdata=full,
            hovertemplate=f"<b>{html.escape(str(product))}</b><br>%{{x|%m/%Y}}<br>{metric}: %{{customdata}}<extra></extra>",
        ))
    apply_layout(fig, f"Evolução mensal por produto · {metric.lower()}", height=360)
    periods = sorted(pd.to_datetime(data["Período"].unique())) if not data.empty else []
    fig.update_xaxes(tickmode="array", tickvals=periods, ticktext=[f"{month_names[p.month-1]} {p.year}" for p in periods])
    if log_scale and not data.empty and (data[metric] > 0).all():
        fig.update_yaxes(type="log", title=f"{metric} · escala log")
    else:
        fig.update_yaxes(title=metric)
    return fig


def _formatted_table(summary: pd.DataFrame) -> pd.DataFrame:
    display = summary.copy()
    display["Receita"] = display["Receita"].map(moeda)
    display["Quantidade"] = display["Quantidade"].map(numero)
    display["Participação na receita"] = display["Participação na receita"].map(lambda x: f"{x:.2f}%".replace(".", ","))
    display["Participação na quantidade"] = display["Participação na quantidade"].map(lambda x: f"{x:.2f}%".replace(".", ","))
    display["Receita média por unidade"] = display["Receita média por unidade"].map(lambda x: "Indefinida" if pd.isna(x) else moeda(x))
    return display


def render_products_dashboard(df: pd.DataFrame, source: str) -> None:
    summary = build_product_summary(df)
    if summary.empty:
        st.info("Não há produtos válidos no recorte selecionado.")
        return
    kpis = calculate_product_kpis(df)
    exact_revenue = exact_decimal_sum(df["Faturamento"])
    exact_average = exact_revenue / kpis.distinct_products if kpis.distinct_products else None
    growth, period_label, comparison_available = build_product_kpi_comparison(df)
    anomalies = detect_extreme_monetary_values(df)
    dates = pd.to_datetime(df["Data"], errors="coerce").dropna()
    period = "Período não identificado" if dates.empty else f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y}"
    quality = f"{len(anomalies)} valores atípicos preservados" if len(anomalies) else "Sem anomalias monetárias sinalizadas"
    st.markdown(f"""
    <div class="product-hero"><div><div class="product-eyebrow">PORTFÓLIO COMERCIAL</div>
    <div class="product-title">Inteligência de Produtos</div>
    <div class="product-subtitle">Desempenho, participação e comportamento comercial do portfólio.</div></div>
    <div class="product-meta"><span>{html.escape(source)}</span><span>{period}</span><span>{len(df):,} registros</span>
    <span>{len(summary)} produtos</span><span class="product-warning">{quality}</span></div></div>
    """, unsafe_allow_html=True)

    cards = [
        ("Receita total dos produtos", moeda_resumida(exact_revenue), moeda(exact_revenue), "revenue", "◇"),
        ("Unidades vendidas", numero(kpis.quantity), numero(kpis.quantity), "quantity", "↗"),
        ("Produtos distintos", numero(kpis.distinct_products), numero(kpis.distinct_products), "distinct_products", "▦"),
        ("Receita média por produto", moeda_resumida(exact_average or 0), "Indefinida" if exact_average is None else moeda(exact_average), "average_revenue_per_product", "◎"),
    ]
    with st.container(key="product-kpis"):
        for column, item in zip(st.columns(4), cards):
            label, value, full, key, icon = item
            badge, tone = _growth_badge(growth.get(key), comparison_available)
            with column:
                st.markdown(_kpi(label, value, full, badge, tone, icon), unsafe_allow_html=True)
    st.caption("Receita média por produto = receita total ÷ produtos distintos válidos. " + period_label)

    st.markdown('<div class="product-section"><span>Ranking inteligente</span><small>O recorte completo alimenta os cálculos</small></div>', unsafe_allow_html=True)
    control_a, control_b = st.columns([1, 1])
    with control_a:
        metric = st.segmented_control("Métrica do ranking", ("Receita", "Quantidade"), default="Receita", key="product_ranking_metric", label_visibility="collapsed") or "Receita"
    options = sorted({min(3, len(summary)), min(5, len(summary)), len(summary)})
    with control_b:
        limit = st.selectbox("Produtos exibidos", options, index=len(options) - 1, key="product_ranking_limit")
    chart_col, concentration_col = st.columns([1.55, 1])
    with chart_col:
        with st.container(border=True):
            st.plotly_chart(_ranking_figure(summary, metric, limit), width="stretch", config={"displayModeBar": False, "responsive": True})
            share_column = "Participação na receita" if metric == "Receita" else "Participação na quantidade"
            st.caption(f"{share_column} (%) calculada sobre o total do recorte ativo.")
    with concentration_col:
        with st.container(border=True):
            st.plotly_chart(_concentration_figure(summary), width="stretch", config={"displayModeBar": False, "responsive": True})
            concentration = build_product_concentration(summary)
            st.markdown(
                f'<div class="concentration-strip"><span>Líder <strong>{concentration["leader"]:.1f}%</strong></span>'
                f'<span>Top 3 <strong>{concentration["top3"]:.1f}%</strong></span>'
                f'<span>Top {min(5, len(summary))} <strong>{concentration["top5"]:.1f}%</strong></span></div>'.replace(".", ","),
                unsafe_allow_html=True,
            )

    st.markdown('<div class="product-section"><span>Evolução por produto</span><small>Sem suavização ou interpolação</small></div>', unsafe_allow_html=True)
    temporal_a, temporal_b, temporal_c = st.columns([2, 1, 1])
    product_options = summary["Produto"].tolist()
    with temporal_a:
        selected = st.multiselect("Produtos comparados", product_options, default=product_options[: min(3, len(product_options))], max_selections=4, key="product_temporal_selection")
    with temporal_b:
        temporal_metric = st.segmented_control("Métrica temporal", ("Receita", "Quantidade"), default="Receita", key="product_temporal_metric", label_visibility="collapsed") or "Receita"
    with temporal_c:
        view = st.segmented_control("Visão temporal", ("Completa", "Faixa típica"), default="Completa", key="product_temporal_view", label_visibility="collapsed") or "Completa"
    log_scale = st.toggle("Escala logarítmica", value=True, key="product_temporal_log", help="Altera apenas a escala visual quando todos os valores são positivos.")
    excluded = set(anomalies["indice"].tolist()) if view == "Faixa típica" and not anomalies.empty else None
    temporal = build_product_time_series(df, selected, temporal_metric, excluded)
    if not selected or temporal.empty:
        st.info("Selecione ao menos um produto com dados no período.")
    else:
        if excluded:
            st.caption("Faixa típica exclusivamente visual: valores sinalizados permanecem nos KPIs, rankings e visão completa.")
        with st.container(border=True, key="product-timeline"):
            st.plotly_chart(_time_figure(temporal, temporal_metric, log_scale), width="stretch", config={"displayModeBar": False, "responsive": True})

    comparison, comparison_label, comparison_ok = build_product_comparison(df)
    st.markdown('<div class="product-section"><span>Desempenho comparativo</span><small>Janelas equivalentes</small></div>', unsafe_allow_html=True)
    st.caption(comparison_label)
    if comparison_ok:
        display_comparison = comparison.copy()
        for column in ("Receita atual", "Receita anterior", "Diferença de receita"):
            display_comparison[column] = display_comparison[column].map(moeda)
        for column in ("Quantidade atual", "Quantidade anterior", "Diferença de quantidade"):
            display_comparison[column] = display_comparison[column].map(numero)
        for column in ("Variação da receita (%)", "Variação da quantidade (%)"):
            display_comparison[column] = display_comparison[column].map(lambda x: "Indefinida" if pd.isna(x) else f"{x:+.1f}%".replace(".", ","))
        st.dataframe(display_comparison, width="stretch", hide_index=True)
    else:
        st.info("Não há dois períodos equivalentes com dados suficientes.")

    concentration = build_product_concentration(summary)
    revenue_top = summary.iloc[0]
    quantity_top = summary.sort_values(["Quantidade", "Produto"], ascending=[False, True]).iloc[0]
    insight_texts = [
        ("RECEITA", "Liderança por receita", f"{revenue_top['Produto']} concentra {revenue_top['Participação na receita']:.1f}% da receita."),
        ("VOLUME", "Liderança por quantidade", f"{quantity_top['Produto']} representa {quantity_top['Participação na quantidade']:.1f}% das unidades."),
        ("CONCENTRAÇÃO", "Participação acumulada", f"Os três primeiros produtos somam {concentration['top3']:.1f}% da receita; o dado não implica risco por si só."),
        ("QUALIDADE", "Valores preservados", f"{len(anomalies)} valores monetários sinalizados permanecem em todos os cálculos." if len(anomalies) else "Não há valores monetários extremos sinalizados neste recorte."),
    ]
    st.markdown('<div class="product-section"><span>Leituras verificáveis</span><small>Sem IA externa ou causalidade inventada</small></div>', unsafe_allow_html=True)
    with st.container(key="product-insights"):
        for column, (badge, title, text) in zip(st.columns(4), insight_texts):
            with column:
                st.markdown(f'<div class="product-insight"><em>{badge}</em><strong>{html.escape(title)}</strong><p>{html.escape(text)}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="product-section"><span>Tabela analítica de produtos</span><small>Paginação apenas visual</small></div>', unsafe_allow_html=True)
    page_size = st.selectbox("Produtos por página", sorted({5, 10, 25, max(len(summary), 1)}), key="product_table_page_size")
    total_pages = max(math.ceil(len(summary) / page_size), 1)
    page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1, key="product_table_page")
    visible = paginate_products(summary, page, page_size)
    st.caption(f"Exibindo {len(visible)} de {len(summary)} produtos. Totais calculados sobre todo o recorte.")
    st.dataframe(_formatted_table(visible), width="stretch", hide_index=True)

