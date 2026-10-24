from __future__ import annotations

import html
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import _log_currency_ticks, apply_layout, render_revenue_chart
from components.tables import table_raw_data
from domain.periods import split_equivalent_periods
from services.anomalies import detect_extreme_monetary_values
from services.formatter import moeda, moeda_resumida, numero


@dataclass(frozen=True)
class ComparisonMetric:
    label: str
    current: float
    previous: float
    difference: float
    percentage: float | None
    kind: str


def safe_percentage_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def build_sales_breakdowns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    total_revenue = float(df["Faturamento"].sum()) if "Faturamento" in df else 0.0
    total_quantity = float(df["Quantidade"].sum()) if "Quantidade" in df else 0.0
    product = (
        df.groupby("Produto", dropna=False, as_index=False)
        .agg(Receita=("Faturamento", "sum"), Quantidade=("Quantidade", "sum"))
        .sort_values(["Receita", "Produto"], ascending=[False, True])
        .reset_index(drop=True)
    )
    product["Produto"] = product["Produto"].fillna("Não informado").astype(str)
    product.insert(0, "Posição", product.index + 1)
    product["Participação na receita"] = (
        product["Receita"].div(total_revenue).mul(100) if total_revenue else 0.0
    )
    product["Participação na quantidade"] = (
        product["Quantidade"].div(total_quantity).mul(100) if total_quantity else 0.0
    )

    store = (
        df.groupby("Loja", dropna=False, as_index=False)
        .agg(Receita=("Faturamento", "sum"), Quantidade=("Quantidade", "sum"))
        .sort_values(["Receita", "Loja"], ascending=[False, True])
        .reset_index(drop=True)
    )
    store["Loja"] = store["Loja"].fillna("Não informado").astype(str)
    store.insert(0, "Posição", store.index + 1)
    store["Participação na receita"] = (
        store["Receita"].div(total_revenue).mul(100) if total_revenue else 0.0
    )
    store["Participação na quantidade"] = (
        store["Quantidade"].div(total_quantity).mul(100) if total_quantity else 0.0
    )
    return product, store


def build_anomaly_comparison_note(df: pd.DataFrame, anomalies: pd.DataFrame) -> str | None:
    """Describe material anomaly concentration without changing or explaining the data."""
    if anomalies.empty or "indice" not in anomalies:
        return None
    current, previous, period = split_equivalent_periods(df, "Data")
    if not period.available:
        return None

    anomaly_indices = set(anomalies["indice"].tolist())
    shares: list[tuple[str, float]] = []
    for label, frame in (("período atual", current), ("período anterior", previous)):
        total = float(frame["Faturamento"].sum())
        flagged = float(frame.loc[frame.index.isin(anomaly_indices), "Faturamento"].sum())
        share = (flagged / total * 100) if total else 0.0
        if share >= 25.0:
            shares.append((label, share))
    if not shares:
        return None

    detail = " e ".join(
        f"{share:.1f}% da receita do {label}".replace(".", ",") for label, share in shares
    )
    return (
        f"Leitura cautelosa: valores sinalizados concentram {detail}. "
        "Eles permanecem nos cálculos e podem ampliar a variação, sem demonstrar sua causa."
    )


def build_comparison_metrics(df: pd.DataFrame) -> tuple[list[ComparisonMetric], str, bool]:
    current, previous, period = split_equivalent_periods(df, "Data")
    if not period.available:
        return [], period.label, False

    def values(frame: pd.DataFrame) -> tuple[float, float, float, float]:
        revenue = float(frame["Faturamento"].sum())
        quantity = float(frame["Quantidade"].sum())
        records = float(len(frame))
        ticket = revenue / records if records else 0.0
        return revenue, quantity, records, ticket

    current_values = values(current)
    previous_values = values(previous)
    definitions = (
        ("Faturamento", "currency"),
        ("Quantidade", "number"),
        ("Registros de venda", "number"),
        ("Ticket médio", "currency"),
    )
    metrics = [
        ComparisonMetric(
            label=label,
            current=current_value,
            previous=previous_value,
            difference=current_value - previous_value,
            percentage=safe_percentage_change(current_value, previous_value),
            kind=kind,
        )
        for (label, kind), current_value, previous_value in zip(
            definitions, current_values, previous_values
        )
    ]
    return metrics, period.label, True


def build_sales_insights(
    analytics: dict, product: pd.DataFrame, store: pd.DataFrame, anomaly_count: int
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    if not product.empty:
        top = product.iloc[0]
        insights.append(
            {
                "badge": "PRODUTO",
                "title": "Maior participação na receita",
                "text": (
                    f"{top['Produto']} representa {top['Participação na receita']:.1f}% do faturamento "
                    "do recorte selecionado."
                ),
            }
        )
    if not store.empty:
        top = store.iloc[0]
        insights.append(
            {
                "badge": "LOJA",
                "title": "Maior contribuição no período",
                "text": (
                    f"{top['Loja']} responde por {top['Participação na receita']:.1f}% da receita "
                    "observada."
                ),
            }
        )
    comparison = analytics.get("comparison", {})
    if comparison.get("available"):
        growth = float(analytics.get("crescimento_faturamento", 0))
        direction = "aumentou" if growth > 0 else "diminuiu" if growth < 0 else "permaneceu estável"
        value = f" {abs(growth):.1f}%".replace(".", ",") if growth else ""
        insights.append(
            {
                "badge": "PERÍODOS",
                "title": "Variação entre janelas equivalentes",
                "text": f"O faturamento {direction}{value}. A base não demonstra a causa da variação.",
            }
        )
    else:
        insights.append(
            {
                "badge": "PERÍODOS",
                "title": "Comparação indisponível",
                "text": "Não há duas janelas equivalentes com dados suficientes para calcular variação.",
            }
        )
    if anomaly_count:
        insights.append(
            {
                "badge": "QUALIDADE",
                "title": "Valores atípicos preservados",
                "text": (
                    f"{anomaly_count} valores monetários foram sinalizados para revisão e continuam "
                    "presentes nos indicadores consolidados."
                ),
            }
        )
    return insights[:4]


def _growth(value: float, available: bool) -> tuple[str, str]:
    if not available:
        return "Comparação indisponível", "neutral"
    tone = "positive" if value > 0 else "negative" if value < 0 else "neutral"
    arrow = "↑" if value > 0 else "↓" if value < 0 else "→"
    return f"{arrow} {abs(value):.1f}%".replace(".", ","), tone


def _kpi_card(label: str, value: str, full: str, growth: str, tone: str, icon: str) -> str:
    return f"""
    <div class="sales-kpi">
      <div class="sales-kpi-head"><span class="sales-kpi-icon">{icon}</span>
      <span>{html.escape(label)}</span><span class="fusion-delta fusion-delta-{tone}">{html.escape(growth)}</span></div>
      <div class="sales-kpi-value" title="{html.escape(full)}">{html.escape(value)}</div>
      <div class="sales-kpi-foot">Valor integral disponível ao passar o cursor</div>
    </div>
    """


def render_sales_header(df: pd.DataFrame, analytics: dict, source: str, anomaly_count: int) -> None:
    dates = pd.to_datetime(df["Data"], errors="coerce").dropna()
    period = "Período não identificado"
    if not dates.empty:
        period = f"{dates.min():%d/%m/%Y}–{dates.max():%d/%m/%Y}"
    quality = analytics.get("quality", {})
    discarded = int(quality.get("registros_descartados", 0))
    warning = (
        f"{anomaly_count} possíveis anomalias preservadas"
        if anomaly_count
        else "Sem anomalias monetárias sinalizadas"
    )
    st.markdown(
        f"""
        <div class="sales-hero">
          <div><div class="sales-eyebrow">DESEMPENHO COMERCIAL</div>
          <div class="sales-title">Análise de Vendas</div>
          <div class="sales-subtitle">Receita, volume e concentração do recorte selecionado</div></div>
          <div class="sales-meta">
            <span>{html.escape(source)}</span><span>{html.escape(period)}</span>
            <span>{len(df):,} registros</span><span>{discarded} descartados</span>
            <span class="sales-meta-warning">{html.escape(warning)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sales_kpis(analytics: dict) -> None:
    available = bool(analytics.get("comparison", {}).get("available"))
    methodology = analytics.get("metodologia_ticket", "receita por registro de venda")
    order_label = "Pedidos" if methodology == "receita por pedido único" else "Registros de venda"
    items = (
        ("Faturamento", moeda_resumida(analytics.get("faturamento_total_exato", analytics["faturamento_total"])), moeda(analytics.get("faturamento_total_exato", analytics["faturamento_total"])), analytics["crescimento_faturamento"], "◇"),
        ("Quantidade vendida", numero(analytics["quantidade_total"]), numero(analytics["quantidade_total"]), analytics["crescimento_quantidade"], "↗"),
        (order_label, numero(analytics["total_pedidos"]), numero(analytics["total_pedidos"]), analytics["crescimento_pedidos"], "▦"),
        ("Ticket médio", moeda_resumida(analytics.get("ticket_medio_exato", analytics["ticket_medio"])), moeda(analytics.get("ticket_medio_exato", analytics["ticket_medio"])), analytics["crescimento_ticket"], "◎"),
    )
    with st.container(key="sales-kpis"):
        columns = st.columns(4)
        for column, (label, value, full, growth_value, icon) in zip(columns, items):
            growth, tone = _growth(float(growth_value or 0), available)
            with column:
                st.markdown(_kpi_card(label, value, full, growth, tone, icon), unsafe_allow_html=True)
    st.markdown(
        f'<div class="sales-method">Ticket médio: {html.escape(methodology)}.</div>',
        unsafe_allow_html=True,
    )


def _ranking_figure(data: pd.DataFrame, dimension: str, metric: str, title: str) -> go.Figure:
    ordered = data.sort_values(metric, ascending=True).copy()
    is_currency = metric == "Receita"
    custom = ordered[metric].map(moeda if is_currency else numero)
    visible_text = ordered[metric].map(moeda_resumida if is_currency else numero)
    colors = ["#22D3EE", "#38BDF8", "#3B82F6", "#6366F1", "#8B5CF6", "#A855F7"]
    fig = go.Figure(
        go.Bar(
            x=ordered[metric],
            y=ordered[dimension],
            orientation="h",
            marker=dict(color=colors[: len(ordered)], line=dict(width=0)),
            customdata=custom,
            text=visible_text,
            textposition="auto",
            textfont=dict(size=12, color="#F4F8FF"),
            cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>{metric}: %{{customdata}}<extra></extra>",
        )
    )
    apply_layout(fig, title, height=330)
    fig.update_layout(margin=dict(l=18, r=32, t=58, b=42), font=dict(size=12))
    fig.update_yaxes(title=None, automargin=True, tickfont=dict(size=12, color="#D9E5FA"))
    if is_currency:
        ticks, labels = _log_currency_ticks(ordered[metric])
        fig.update_xaxes(
            type="log",
            title="Receita (R$ · escala log)",
            tickvals=ticks,
            ticktext=labels,
            automargin=True,
            tickfont=dict(size=11, color="#B8C9E7"),
        )
    else:
        fig.update_xaxes(
            title="Quantidade", tickformat=",.0f", automargin=True,
            tickfont=dict(size=11, color="#B8C9E7"),
        )
    return fig


def _compact_ranking_table(data: pd.DataFrame, dimension: str, metric: str) -> str:
    ordered = data.sort_values([metric, dimension], ascending=[False, True]).reset_index(drop=True)
    share_column = (
        "Participação na receita" if metric == "Receita" else "Participação na quantidade"
    )
    share_label = (
        "Participação na receita (%)" if metric == "Receita" else "Participação na quantidade (%)"
    )
    rows = []
    for position, row in ordered.iterrows():
        value = moeda_resumida(row[metric]) if metric == "Receita" else numero(row[metric])
        share = f"{row[share_column]:.1f}%".replace(".", ",")
        rows.append(
            "<tr>"
            f"<td>{position + 1}</td><td title=\"{html.escape(str(row[dimension]))}\">{html.escape(str(row[dimension]))}</td>"
            f"<td title=\"{html.escape(moeda(row[metric]) if metric == 'Receita' else numero(row[metric]))}\">{html.escape(value)}</td>"
            f"<td>{html.escape(share)}</td></tr>"
        )
    return (
        f'<div class="sales-ranking-basis">{html.escape(share_label)}</div>'
        '<div class="sales-ranking-wrap"><table class="sales-ranking-table">'
        f"<thead><tr><th>#</th><th>{html.escape(dimension)}</th><th>{html.escape(metric)}</th>"
        f'<th title="{html.escape(share_label)}">Participação</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def render_rankings(product: pd.DataFrame, store: pd.DataFrame) -> None:
    with st.container(key="sales-rankings"):
        product_col, store_col = st.columns(2)
        with product_col:
            with st.container(border=True):
                metric = st.segmented_control(
                    "Métrica de produtos",
                    ("Receita", "Quantidade"),
                    default="Receita",
                    key="sales_product_metric",
                    label_visibility="collapsed",
                )
                st.plotly_chart(
                    _ranking_figure(product, "Produto", metric, f"Produtos por {metric.lower()}"),
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )
                st.markdown(
                    _compact_ranking_table(product, "Produto", metric),
                    unsafe_allow_html=True,
                )
                with st.popover("Valores integrais dos produtos", width="stretch"):
                    st.dataframe(product, width="stretch", hide_index=True)
        with store_col:
            with st.container(border=True):
                metric = st.segmented_control(
                    "Métrica de lojas",
                    ("Receita", "Quantidade"),
                    default="Receita",
                    key="sales_store_metric",
                    label_visibility="collapsed",
                )
                st.plotly_chart(
                    _ranking_figure(store, "Loja", metric, f"Lojas por {metric.lower()}"),
                    width="stretch",
                    config={"displayModeBar": False, "responsive": True},
                )
                st.markdown(
                    _compact_ranking_table(store, "Loja", metric),
                    unsafe_allow_html=True,
                )
                with st.popover("Valores integrais das lojas", width="stretch"):
                    st.dataframe(store, width="stretch", hide_index=True)


def _comparison_value(value: float, kind: str) -> str:
    return moeda_resumida(value) if kind == "currency" else numero(value)


def render_comparison(df: pd.DataFrame, anomalies: pd.DataFrame) -> None:
    metrics, label, available = build_comparison_metrics(df)
    st.markdown(
        '<div class="sales-section-head"><span>Comparação temporal</span><small>Janelas equivalentes e identificadas</small></div>',
        unsafe_allow_html=True,
    )
    st.caption(label)
    if not available:
        st.info("Não há dados suficientes para comparar dois períodos equivalentes.")
        return
    anomaly_note = build_anomaly_comparison_note(df, anomalies)
    if anomaly_note:
        st.markdown(
            f'<div class="sales-comparison-note">{html.escape(anomaly_note)}</div>',
            unsafe_allow_html=True,
        )
    with st.container(key="sales-comparison"):
        columns = st.columns(4)
        for column, metric in zip(columns, metrics):
            percent = "Indefinida: base anterior igual a zero" if metric.percentage is None else f"{metric.percentage:+.1f}%".replace(".", ",")
            with column:
                st.markdown(
                    f"""
                    <div class="comparison-card"><div class="comparison-label">{html.escape(metric.label)}</div>
                    <div class="comparison-current">{html.escape(_comparison_value(metric.current, metric.kind))}</div>
                    <div class="comparison-row"><span>Anterior</span><strong>{html.escape(_comparison_value(metric.previous, metric.kind))}</strong></div>
                    <div class="comparison-row"><span>Diferença</span><strong>{html.escape(_comparison_value(metric.difference, metric.kind))}</strong></div>
                    <div class="comparison-rate">{html.escape(percent)}</div></div>
                    """,
                    unsafe_allow_html=True,
                )


def render_sales_insights(insights: list[dict[str, str]]) -> None:
    st.markdown(
        '<div class="sales-section-head"><span>Leituras verificáveis</span><small>Sem causalidade ou previsão inventada</small></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="sales-insights"):
        columns = st.columns(len(insights))
        for column, insight in zip(columns, insights):
            with column:
                st.markdown(
                    f"""
                    <div class="sales-insight"><div class="sales-insight-badge">{html.escape(insight['badge'])}</div>
                    <div class="sales-insight-title">{html.escape(insight['title'])}</div>
                    <div class="sales-insight-copy">{html.escape(insight['text'])}</div></div>
                    """,
                    unsafe_allow_html=True,
                )


def render_sales_dashboard(df: pd.DataFrame, analytics: dict, source: str) -> None:
    anomalies = detect_extreme_monetary_values(df)
    product, store = build_sales_breakdowns(df)
    render_sales_header(df, analytics, source, len(anomalies))
    render_sales_kpis(analytics)

    st.markdown(
        '<div class="sales-section-head"><span>Evolução das vendas</span><small>Valores consolidados preservados</small></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="sales-timeline"):
        scale_col, view_col = st.columns([1.3, 1])
        with scale_col:
            log_scale = st.toggle(
                "Escala logarítmica",
                value=True,
                key="sales_log_scale",
                help="Altera apenas a escala visual; todos os valores permanecem nos cálculos.",
            )
        with view_col:
            view = st.segmented_control(
                "Visualização temporal",
                ("Completa", "Faixa típica"),
                default="Completa",
                key="sales_revenue_view",
                label_visibility="collapsed",
            )
        revenue_data = analytics["charts"]["revenue_by_month"]
        if view == "Faixa típica" and not anomalies.empty:
            typical = df.drop(index=anomalies["indice"], errors="ignore")
            revenue_data = (
                typical.assign(periodo=typical["Data"].dt.to_period("M").dt.to_timestamp("M"))
                .groupby("periodo", as_index=False)["Faturamento"]
                .sum()
                .rename(columns={"Faturamento": "faturamento"})
            )
            st.caption(
                "Faixa típica: separação exclusivamente visual. Os valores sinalizados continuam nos KPIs, comparações e visão completa."
            )
        render_revenue_chart(revenue_data, log_scale=log_scale)

    st.markdown(
        '<div class="sales-section-head"><span>Produtos e lojas</span><small>Receita, volume e participação</small></div>',
        unsafe_allow_html=True,
    )
    render_rankings(product, store)
    render_comparison(df, anomalies)
    insights = build_sales_insights(analytics, product, store, len(anomalies))
    render_sales_insights(insights)

    st.markdown(
        '<div class="sales-section-head"><span>Tabela analítica</span><small>O recorte ativo alimenta cálculos e exportações</small></div>',
        unsafe_allow_html=True,
    )
    table_raw_data(df)
