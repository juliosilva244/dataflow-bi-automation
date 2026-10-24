"""Explicit consolidated versus comparison scopes, without changing any KPI."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.sensitivity_panel import render_sensitivity_analysis
from services.ai_evidence import scope_summary
from services.formatter import moeda, moeda_integral


def full_decimal_currency(value):
    return moeda_integral(value)


def render_analytical_scope(state):
    summary = scope_summary(state)
    if summary is None:
        return
    with st.expander("Escopo e reconciliação dos KPIs", expanded=False):
        st.write(
            "Faturamento, pedidos e ticket consolidados usam os mesmos registros após os filtros. "
            "Os percentuais comparam somente os dois períodos equivalentes abaixo; "
            "não representam uma divisão do faturamento consolidado."
        )
        st.caption(summary["label"])
        rows = []
        for label, key in (("Consolidado após filtros", "global"), ("Período atual", "current"), ("Período anterior", "previous"), ("Fora dos períodos comparativos", "outside")):
            values = summary[key]
            rows.append({
                "Escopo": label, "Registros": values["records"],
                "Receita integral": full_decimal_currency(values["revenue"]),
                "Pedidos/denominador": values["orders"],
                "Ticket calculado": full_decimal_currency(values["ticket"]) if values["orders"] else "Indisponível",
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        total = summary["global"]
        st.write("Denominador:", summary["order_method"])
        st.write(
            "Fração do ticket consolidado:",
            f"{full_decimal_currency(total['revenue'])} / {total['orders']}"
            if total["orders"] else "Indisponível: sem denominador.",
        )
        st.caption(
            "Ticket nos cards: arredondado para centavos. A divisão pode ser periódica; "
            "a fração acima é a referência, não a multiplicação do ticket arredondado. "
            "Pedidos únicos não são necessariamente aditivos entre lojas, produtos ou períodos."
        )
        if total["orders"]:
            st.caption("Apresentação nos cards: " + moeda(total["ticket"]))
    render_sensitivity_analysis(state)
