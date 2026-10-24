import html
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.formatter import moeda, moeda_resumida, numero
from services.insight_engine import gerar_insights_executivos
from services.llm_router import get_llm_router


def _growth(value, available):
    if not available:
        return "Sem base comparativa", "neutral"
    numeric = float(value or 0)
    text = f"{numeric:+.1f}%".replace(".", ",")
    if numeric > 0:
        return f"↑ {text}", "positive"
    if numeric < 0:
        return f"↓ {text}", "negative"
    return f"→ {text}", "neutral"


def _metric_card(label, value, full_value, growth, tone, accent, icon):
    return f"""
    <div class="fusion-kpi fusion-kpi-{accent}">
      <div class="fusion-kpi-head"><span class="fusion-kpi-label"><span class="fusion-kpi-icon" aria-hidden="true">{icon}</span>{html.escape(label)}</span>
      <span class="fusion-delta fusion-delta-{tone}">{html.escape(growth)}</span></div>
      <div class="fusion-kpi-value" title="{html.escape(full_value)}" aria-label="Valor integral: {html.escape(full_value)}">{html.escape(value)}</div>
      <div class="fusion-kpi-detail">Passe o cursor para ver o valor completo</div>
    </div>
    """


def render_kpi_strip(analytics):
    available = bool(analytics.get("comparison", {}).get("available"))
    definitions = (
        (
            "Faturamento total",
            moeda_resumida(analytics.get("faturamento_total_exato", analytics.get("faturamento_total", 0))),
            moeda(analytics.get("faturamento_total_exato", analytics.get("faturamento_total", 0))),
            analytics.get("crescimento_faturamento"),
            "cyan",
            "◇",
        ),
        (
            "Pedidos",
            numero(analytics.get("total_pedidos", 0)),
            numero(analytics.get("total_pedidos", 0)),
            analytics.get("crescimento_pedidos"),
            "blue",
            "▦",
        ),
        (
            "Quantidade vendida",
            numero(analytics.get("quantidade_total", 0)),
            numero(analytics.get("quantidade_total", 0)),
            analytics.get("crescimento_quantidade"),
            "green",
            "↗",
        ),
        (
            "Ticket médio",
            moeda_resumida(analytics.get("ticket_medio_exato", analytics.get("ticket_medio", 0))),
            moeda(analytics.get("ticket_medio_exato", analytics.get("ticket_medio", 0))),
            analytics.get("crescimento_ticket"),
            "violet",
            "◎",
        ),
    )
    with st.container(key="overview-kpis"):
        columns = st.columns(4)
        for column, (label, value, full_value, growth_value, accent, icon) in zip(columns, definitions):
            growth, tone = _growth(growth_value, available)
            with column:
                st.markdown(
                    _metric_card(label, value, full_value, growth, tone, accent, icon),
                    unsafe_allow_html=True,
                )


def render_category_donut(df):
    dimension = "Categoria" if "Categoria" in df.columns else "Produto"
    title = "Receita por categoria" if dimension == "Categoria" else "Mix de receita por produto"
    grouped = (
        df.groupby(dimension, as_index=False)["Faturamento"]
        .sum()
        .sort_values("Faturamento", ascending=False)
    )
    if len(grouped) > 6:
        leading = grouped.head(5).copy()
        other = pd.DataFrame({dimension: ["Outros"], "Faturamento": [grouped.iloc[5:]["Faturamento"].sum()]})
        grouped = pd.concat([leading, other], ignore_index=True)
    total = float(grouped["Faturamento"].sum())
    grouped["Participação"] = grouped["Faturamento"].div(total).mul(100) if total else 0.0
    grouped["Legenda"] = grouped.apply(
        lambda row: f"{row[dimension]} · {row['Participação']:.1f}%".replace(".", ","), axis=1
    )
    fig = go.Figure(
        go.Pie(
            labels=grouped["Legenda"],
            values=grouped["Faturamento"],
            customdata=list(zip(grouped[dimension], grouped["Faturamento"].map(moeda))),
            hole=0.63,
            sort=False,
            textinfo="none",
            domain=dict(x=[0, 0.62]),
            marker=dict(
                colors=["#22D3EE", "#3B82F6", "#8B5CF6", "#D946EF", "#34D399", "#FB923C"],
                line=dict(color="#081128", width=2),
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>Receita: %{customdata[1]}<br>Participação: %{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16), x=0.04),
        height=285,
        margin=dict(l=12, r=12, t=55, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E8EEFF", family="Inter"),
        legend=dict(
            orientation="v",
            y=0.5,
            x=0.68,
            xanchor="left",
            yanchor="middle",
            font=dict(size=11, color="#DCE8FF"),
            itemwidth=30,
        ),
        annotations=[
            dict(
                text=f"<b>{moeda_resumida(grouped['Faturamento'].sum())}</b><br><span style='font-size:10px'>Total</span>",
                x=0.31,
                y=0.5,
                showarrow=False,
                font=dict(color="#F8FAFC", size=12),
            )
        ],
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})


def prepare_product_ranking(analytics, limit=6):
    products = analytics["charts"].get("top_products", pd.DataFrame()).copy()
    products.attrs = {}
    if products.empty:
        return products
    total = float(analytics.get("faturamento_total", products["faturamento"].sum()) or 0)
    products = products.sort_values("faturamento", ascending=False).head(limit).reset_index(drop=True)
    products.insert(0, "#", products.index + 1)
    products["Receita"] = products["faturamento"].map(moeda_resumida)
    products["Participação"] = products["faturamento"].div(total).mul(100) if total else 0.0
    products["Participação"] = products["Participação"].map(lambda value: f"{value:.1f}%".replace(".", ","))
    return products.rename(columns={"produto": "Produto"})


def render_products_panel(analytics):
    products = prepare_product_ranking(analytics)
    st.markdown('<div class="panel-title">Principais produtos</div>', unsafe_allow_html=True)
    if products.empty:
        st.info("Produtos indisponíveis para este recorte.")
        return
    st.dataframe(
        products[["#", "Produto", "Receita", "Participação"]],
        width="stretch",
        hide_index=True,
        height=276,
        column_config={
            "#": st.column_config.NumberColumn("#", width="small"),
            "Produto": st.column_config.TextColumn("Produto", width="medium"),
            "Receita": st.column_config.TextColumn("Receita", width="medium"),
            "Participação": st.column_config.TextColumn("Part.", width="small"),
        },
    )
    with st.popover("Valores integrais", width="stretch"):
        details = products[["Produto", "faturamento", "Participação"]].rename(
            columns={"faturamento": "Receita integral"}
        )
        st.dataframe(
            details,
            width="stretch",
            hide_index=True,
            column_config={
                "Receita integral": st.column_config.NumberColumn("Receita integral", format="R$ %.2f"),
            },
        )


def render_ai_panel():
    router = get_llm_router(
        api_key=st.session_state.get("groq_api_key", ""),
        rate_limiter=st.session_state.get("ai_rate_limiter"),
    )
    enabled = bool(st.session_state.get("ai_enabled", False))
    configured = router.is_configured()
    if not configured:
        status, status_class = "Provedor não configurado", "offline"
    elif not enabled:
        status, status_class = "Desativada pelo usuário", "offline"
    else:
        status, status_class = "Disponível com consentimento", "online"
    st.markdown(
        f"""
        <div class="ai-panel-head"><div class="ai-orb">✦</div><div>
        <div class="panel-title">Assistente de IA</div>
        <div class="ai-status ai-status-{status_class}">{html.escape(status)}</div></div></div>
        <p class="panel-copy">Analise os KPIs com governança, anonimização e limites de uso.</p>
        <div class="ai-guardrails"><span>Consentimento explícito</span><span>Anonimização configurável</span></div>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Abrir assistente",
        key="overview_open_ai",
        width="stretch",
        on_click=lambda: st.session_state.update(active_page="Inteligência Artificial"),
    )


def render_insight_row(analytics):
    insights = gerar_insights_executivos(analytics)[:3]
    columns = st.columns(3)
    for column, insight in zip(columns, insights):
        clean_text = html.unescape(str(insight.get("text", "")))
        clean_text = clean_text.replace("<b>", "").replace("</b>", "")
        with column:
            st.markdown(
                f"""
                <div class="fusion-insight">
                  <div class="fusion-insight-tag">{html.escape(str(insight.get('badge', 'Sinal')).upper())}</div>
                  <div class="fusion-insight-title">{html.escape(str(insight.get('title', 'Insight')))}</div>
                  <div class="fusion-insight-copy">{html.escape(clean_text)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def display_name():
    return os.getenv("DATAFLOW_DISPLAY_NAME", "Visitante").strip() or "Visitante"
