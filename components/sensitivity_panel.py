"""On-demand, session-isolated local simulation, clearly separate from official KPIs."""
from decimal import Decimal

import pandas as pd
import streamlit as st

from services.formatter import moeda_integral
from services.metrics_engine import exact_decimal_sum
from services.performance import SessionScopedCache, dataframe_fingerprint
from services.sensitivity import build_sensitivity_analysis


def _money(value):
    return moeda_integral(value) if value is not None else "Indisponível (sem denominador)"


def _difference(first, second):
    if first is None or second is None:
        return "Indisponível"
    return _money(exact_decimal_sum(pd.Series([second, first.copy_negate()], dtype=object)))


def _share(value):
    if value is None:
        return "Indisponível (receita zero)"
    if value and value.copy_abs() < Decimal("0.0001"):
        return "Magnitude inferior a 0,0001% (não zero)"
    return f"{value:.4f}% (arredondada)".replace(".", ",")


def _ranking_table(ranking):
    if ranking is None:
        st.caption("Dimensão não disponível no schema deste recorte.")
        return
    if not ranking:
        st.caption("Sem registros para classificar neste cenário.")
        return
    st.dataframe(pd.DataFrame([{
        "Posição": str(row.rank) + (" (empate)" if row.tied else ""),
        "Identificador": row.name, "Receita integral": _money(row.revenue),
        "Participação no próprio cenário": _share(row.share),
        "Denominador do ticket": row.orders, "Ticket": _money(row.ticket),
    } for row in ranking[:20]]), hide_index=True, width="stretch", height="auto")
    if len(ranking) > 20:
        st.caption(f"Primeiras 20 de {len(ranking)} entidades. Os totais e participações usam o cenário completo.")


def render_sensitivity_analysis(state):
    frame, columns = state.get("prepared_df"), state.get("columns")
    if not isinstance(frame, pd.DataFrame) or not getattr(columns, "faturamento", None):
        return
    with st.expander("Análise de sensibilidade — simulação, não correção dos dados", expanded=False):
        st.caption(
            "A: dados integrais — referência oficial. B: simulação local sem os registros "
            "sinalizados no recorte atual. Nenhum KPI oficial, arquivo ou exportação é substituído. "
            "Nenhuma informação desta análise é enviada à IA."
        )
        key = "sensitivity:v1:" + dataframe_fingerprint(frame)
        if "sensitivity_cache" not in st.session_state:
            st.session_state.sensitivity_cache = SessionScopedCache(max_entries=2)
        cache = st.session_state.sensitivity_cache
        if st.button("Calcular análise de sensibilidade", key="calculate_sensitivity"):
            try:
                with st.spinner("Recalculando e reconciliando os dois cenários..."):
                    analysis = build_sensitivity_analysis(frame, columns)
                cache.set(key, analysis)
                st.session_state.sensitivity_view_key = key
            except (ValueError, ArithmeticError, KeyError):
                st.error("Não foi possível reconciliar a simulação com os dados disponíveis. Os indicadores oficiais não foram alterados.")
                return
        analysis = cache.get(key) if st.session_state.get("sensitivity_view_key") == key else None
        if analysis is None:
            st.caption("Calcule para o recorte atual. Ao alterar dados ou filtros, o resultado anterior não será reutilizado indevidamente.")
            return
        st.write(f"Registros sinalizados: {analysis.flagged_records}. Critério: {analysis.criterion}.")
        st.caption("Limite estatístico no cenário A: " + (_money(analysis.threshold) if analysis.threshold is not None else "Indisponível"))
        st.caption(analysis.period.label + ". Limites inclusivos; as mesmas janelas de A são mantidas em B.")
        if not analysis.flagged_records:
            st.info("Nenhum registro foi sinalizado neste recorte. Os cenários são iguais; isso não certifica ausência de outros problemas.")
        first, second = analysis.integral, analysis.simulated
        denominator = "Pedidos únicos" if analysis.uses_order_id else "Registros (proxy, sem identificador de pedido)"
        rows = [
            ("Receita consolidada", _money(first.total.revenue), _money(second.total.revenue), _money(analysis.revenue_difference)),
            ("Registros", str(first.total.records), str(second.total.records), str(second.total.records - first.total.records)),
            (denominator, str(first.total.orders), str(second.total.orders), str(second.total.orders - first.total.orders)),
            ("Ticket = receita / denominador do próprio cenário", _money(first.total.ticket), _money(second.total.ticket), _difference(first.total.ticket, second.total.ticket)),
            ("Datas efetivamente presentes", first.date_label, second.date_label, "Não se aplica"),
        ]
        for label, field in (("Receita atual", "current"), ("Receita anterior", "previous"), ("Receita fora das janelas", "outside")):
            a, b = getattr(first, field), getattr(second, field)
            available = field == "outside" or analysis.period.previous_start is not None
            rows.append((label, _money(a.revenue) if available else "Indisponível (sem janela)", _money(b.revenue) if available else "Indisponível (sem janela)", _difference(a.revenue, b.revenue) if available else "Indisponível"))
        st.dataframe(pd.DataFrame(rows, columns=["Indicador / escopo", "A — integral oficial", "B — simulação", "Diferença B − A"]), hide_index=True, width="stretch")
        st.write("Diferença B − A na receita:", _money(analysis.revenue_difference))
        st.caption("Receita sinalizada em A: " + _money(analysis.flagged_revenue) + ". O cenário B não é uma estimativa da receita correta nem evidência de erro nos registros.")
        with st.expander("Rankings e participações — denominadores próprios", expanded=False):
            for label, scenario in (("A — integral oficial", first), ("B — simulação", second)):
                st.markdown("**" + label + "**")
                st.write("Lojas — ranking por receita consolidada")
                _ranking_table(scenario.stores)
                st.write("Produtos — ranking por receita consolidada")
                _ranking_table(scenario.products)
        with st.expander("Reconciliação dos cenários e limitações", expanded=False):
            st.write("Receitas por loja/produto reconciliadas separadamente com o próprio cenário; receitas atual + anterior + fora das janelas também reconciliadas.")
            st.write("Pedidos únicos por dimensão/período não são necessariamente aditivos. Ticket e participação são recalculados sobre o denominador de cada cenário; ticket exibido arredondado para centavos.")
            st.write("O detector usa valores positivos e interpolação linear dos quartis em Decimal. O filtro é aplicado antes da sinalização; filtros distintos podem alterar o limite e os registros sinalizados.")
            st.write("Valores Decimal são calculados a partir da representação canônica disponível. Não se recuperam dígitos já perdidos na origem ou ingestão legada em float.")
