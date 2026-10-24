import re

import streamlit as st

from services.formatter import moeda
from services.insight_engine import gerar_insights_executivos


def _plain_text(value):
    return re.sub(r"<[^>]+>", "", str(value))


def render_summary_cards(metricas):
    columns = st.columns(3)
    summaries = (
        (
            "Melhor loja",
            str(metricas.get("melhor_loja", "Não informado")),
            moeda(metricas.get("valor_melhor_loja", 0)),
        ),
        (
            "Produto líder",
            str(metricas.get("produto_top", "Não informado")),
            moeda(metricas.get("valor_produto_top", 0)),
        ),
        (
            "Maior dia",
            metricas.get("dia_top").strftime("%d/%m/%Y")
            if hasattr(metricas.get("dia_top"), "strftime")
            else "Não informado",
            moeda(metricas.get("valor_dia_top", 0)),
        ),
    )
    for column, (title, primary, secondary) in zip(columns, summaries):
        with column:
            with st.container(border=True):
                st.caption(title.upper())
                st.markdown(f"#### {primary}")
                st.write(secondary)


def render_insights(metricas):
    st.subheader("Destaques do recorte")
    render_summary_cards(metricas)
    st.subheader("Sinais analíticos")
    st.caption("Observações determinísticas; não são respostas geradas pelo assistente externo.")
    for insight in gerar_insights_executivos(metricas):
        with st.container(border=True):
            st.caption(str(insight.get("badge", "Sinal")).upper())
            st.markdown(f"**{insight.get('title', 'Insight')}**")
            st.write(_plain_text(insight.get("text", "")))
