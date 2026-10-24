import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from assets.styles import DESIGN_TOKENS
from services.formatter import moeda
from services.metrics_engine import construir_analytics_state


def _compact_currency(value, include_symbol=True):
    scales = (
        (1e21, "sx"),
        (1e18, "qi"),
        (1e15, "qua"),
        (1e12, "tri"),
        (1e9, "bi"),
        (1e6, "mi"),
        (1e3, "mil"),
    )
    for divisor, suffix in scales:
        if abs(value) >= divisor:
            amount = value / divisor
            compact = f"{amount:.0f} {suffix}" if amount >= 10 else f"{amount:.1f} {suffix}".replace(".", ",")
            return f"R$ {compact}" if include_symbol else compact
    compact = f"{value:.0f}"
    return f"R$ {compact}" if include_symbol else compact


def _log_currency_ticks(series, count=6):
    positive = pd.to_numeric(series, errors="coerce")
    positive = positive[positive > 0]
    if positive.empty:
        return None, None
    low, high = math.floor(math.log10(positive.min())), math.floor(math.log10(positive.max()))
    step = max(1, math.ceil((high - low) / max(1, count - 1)))
    ticks = [10**exponent for exponent in range(low, high + 1, step)]
    return ticks, [_compact_currency(value, include_symbol=False) for value in ticks]


def chart_container_start():
    st.markdown(
        """
<div class="chart-card">
""",
        unsafe_allow_html=True,
    )


def chart_container_end():
    st.markdown("</div>", unsafe_allow_html=True)


def apply_layout(fig, title, height=380):
    fig.update_layout(
        title=dict(
            text=title,
            x=0.03,
            xanchor="left",
            font=dict(size=20, color="white"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="Inter"),
        margin=dict(l=18, r=18, t=58, b=22),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#22D3EE",
            font_size=13,
            font_color="#F8FAFC",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color="#CBD5E1",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.08)",
            zeroline=False,
            color="#CBD5E1",
            tickfont=dict(size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        height=height,
    )

    return fig


def render_revenue_chart(chart_df: pd.DataFrame, log_scale=False):
    if chart_df is None or chart_df.empty:
        st.warning("Não há dados válidos para montar o gráfico de faturamento.")
        return

    chart_df = chart_df.copy()
    chart_df["periodo"] = pd.to_datetime(chart_df["periodo"], errors="coerce")
    chart_df["faturamento"] = pd.to_numeric(chart_df["faturamento"], errors="coerce")
    chart_df = chart_df.dropna(subset=["periodo"])
    chart_df["faturamento"] = chart_df["faturamento"].where(chart_df["faturamento"].map(math.isfinite))
    if chart_df.empty or chart_df["faturamento"].notna().sum() == 0:
        st.info("Não há datas e valores finitos para mostrar neste recorte.")
        return
    if log_scale and chart_df["faturamento"].le(0).any():
        st.info("Escala linear aplicada: este recorte contém zero ou valores negativos, incompatíveis com logaritmos.")
        log_scale = False

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["periodo"],
            y=chart_df["faturamento"],
            customdata=chart_df["faturamento"].map(moeda),
            mode="lines+markers",
            connectgaps=False,
            line=dict(
                color=DESIGN_TOKENS["cyan"],
                width=3,
                shape="linear",
            ),
            marker=dict(
                size=8,
                color="#7DD3FC",
                line=dict(width=2, color="#E0F2FE"),
            ),
            hovertemplate=(
                "<b>%{x|%b %Y}</b><br>"
                "Faturamento: %{customdata}"
                "<extra></extra>"
            ),
            name="Faturamento",
        )
    )

    apply_layout(fig, "Evolução mensal do faturamento", height=285)

    periods = pd.to_datetime(chart_df["periodo"])
    month_names = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
    tick_labels = [f"{month_names[value.month - 1]} {value.year}" for value in periods]
    fig.update_xaxes(
        tickmode="array",
        tickvals=periods,
        ticktext=tick_labels,
        showgrid=False,
        zeroline=False,
        color="#CBD5E1",
        tickfont=dict(size=11),
    )
    if log_scale:
        tick_values, tick_labels = _log_currency_ticks(chart_df["faturamento"])
        fig.update_yaxes(
            type="log",
            tickvals=tick_values,
            ticktext=tick_labels,
            title=dict(text="Receita (R$ · escala log)", font=dict(size=10, color="#9FB4D8")),
        )
    else:
        fig.update_yaxes(tickformat="~s", title=dict(text="Receita (R$)", font=dict(size=10, color="#9FB4D8")))

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


def render_store_chart(chart_df: pd.DataFrame, compact=False):
    if chart_df is None or chart_df.empty:
        st.warning("Não há dados válidos para montar o gráfico por loja.")
        return

    fig = px.bar(
        chart_df,
        x="faturamento",
        y="loja",
        orientation="h",
        text="faturamento",
    )

    fig.update_traces(
        marker_color="#7DD3FC",
        marker_line_width=0,
        opacity=0.96,
        texttemplate=(chart_df["faturamento"].map(_compact_currency).tolist() if compact else "R$ %{text:,.0f}"),
        textposition="auto" if compact else "outside",
        textfont=dict(size=10, color="#F4F8FF"),
        cliponaxis=False,
        customdata=chart_df["faturamento"].map(moeda),
        hovertemplate="<b>%{y}</b><br>Faturamento: %{customdata}<extra></extra>",
    )

    title = "Faturamento por loja · escala log" if compact else "Faturamento por loja"
    apply_layout(fig, title, height=285 if compact else 390)
    if compact:
        ticks, labels = _log_currency_ticks(chart_df["faturamento"])
        fig.update_xaxes(
            type="log",
            tickvals=ticks,
            ticktext=labels,
            title=dict(text="Receita (R$ · escala log)", font=dict(size=10, color="#9FB4D8")),
        )
    else:
        fig.update_xaxes(tickprefix="R$ ", tickformat="~s", title=None)
    fig.update_yaxes(title=None)

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


def render_products_chart(chart_df: pd.DataFrame):
    if chart_df is None or chart_df.empty:
        st.warning("Não há dados válidos para montar o gráfico de produtos.")
        return

    fig = px.bar(
        chart_df,
        x="produto",
        y="faturamento",
        text="faturamento",
    )

    fig.update_traces(
        marker_color="#60A5FA",
        marker_line_width=0,
        opacity=0.96,
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Faturamento: R$ %{y:,.0f}<extra></extra>",
    )

    fig.update_xaxes(tickangle=-8)

    apply_layout(fig, "Top Produtos por Faturamento", height=370)

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


def get_charts_payload(df=None, metricas=None):
    if metricas and "charts" in metricas:
        return metricas["charts"]

    if df is not None:
        return construir_analytics_state(df)["charts"]

    return {
        "revenue_by_month": pd.DataFrame(),
        "revenue_by_store": pd.DataFrame(),
        "top_products": pd.DataFrame(),
    }


def render_charts(df=None, metricas=None):
    charts = get_charts_payload(df=df, metricas=metricas)

    st.markdown(
        """
<div class="section-header charts-section-header">
    <div>
        <div class="section-title">Análise Visual</div>
        <div class="section-subtitle">Monitoramento analítico operacional em tempo real</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        chart_container_start()
        render_revenue_chart(charts.get("revenue_by_month"))
        chart_container_end()

    with col2:
        chart_container_start()
        render_store_chart(charts.get("revenue_by_store"))
        chart_container_end()

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    chart_container_start()
    render_products_chart(charts.get("top_products"))
    chart_container_end()


render_chart = render_charts
show_charts = render_charts
display_charts = render_charts
