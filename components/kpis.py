import streamlit as st

from services.formatter import moeda, moeda_resumida, numero

KPI_DEFINITIONS = (
    ("Faturamento", "faturamento_total", "crescimento_faturamento", "currency_short"),
    ("Pedidos", "total_pedidos", "crescimento_pedidos", "number"),
    ("Quantidade", "quantidade_total", "crescimento_quantidade", "number"),
    ("Lojas ativas", "lojas_ativas", "crescimento_lojas", "number"),
    ("Ticket médio", "ticket_medio", "crescimento_ticket", "currency"),
)


def format_growth(value, available=True):
    if not available or value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    sign = "+" if numeric > 0 else ""
    numeric_text = f"{sign}{numeric:.1f}".replace(".", ",")
    return f"{numeric_text}% vs. período anterior"


def _value(value, kind):
    if kind == "currency_short":
        return moeda_resumida(value)
    if kind == "currency":
        return moeda(value)
    return numero(value)


def render_kpis(metricas):
    comparison = metricas.get("comparison", {})
    available = bool(comparison.get("available", comparison.get("disponivel", False)))
    st.subheader("Indicadores executivos")
    st.caption(comparison.get("label", "Sem período comparativo equivalente disponível."))
    first_row = st.columns(3)
    second_row = st.columns(2)
    columns = [*first_row, *second_row]
    for column, (label, key, growth_key, kind) in zip(columns, KPI_DEFINITIONS):
        with column:
            delta = format_growth(metricas.get(growth_key), available)
            st.metric(label, _value(metricas.get(key, 0), kind), delta=delta or "Sem comparação")
