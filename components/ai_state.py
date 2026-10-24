"""Bind temporary UI widgets to AI business values owned by the current session."""

import secrets

import streamlit as st

from services.runtime_revision import runtime_diagnostics

AI_STATE_REVISION = "IA-estado-20261023.2"


def prepare_ai_widget(state_key: str, widget_key: str) -> str:
    """Hydrate before rendering; widget cleanup may only discard the UI copy."""
    st.session_state[widget_key] = st.session_state[state_key]
    return widget_key


def commit_ai_widget(state_key: str, widget_key: str) -> None:
    """Commit in on_change, before the next script run reads business values."""
    st.session_state[state_key] = st.session_state[widget_key]


def render_ai_state_diagnostics() -> None:
    """Reveal flags and an ephemeral label, never the credential or its digest."""
    if "ai_diagnostic_session" not in st.session_state:
        st.session_state.ai_diagnostic_session = secrets.token_hex(4)
    with st.expander("Diagnóstico do estado da IA", expanded=True):
        runtime = runtime_diagnostics()
        st.caption(f"Geração carregada: {runtime['generation_loaded']} · Em disco: {runtime['generation_disk']}")
        st.caption(f"{runtime['audit']} · Processo {runtime['pid']} · Fonte {runtime['source_at_import'][:12]}")
        if not runtime["current"]:
            st.warning("Código carregado divergente. Chamadas à IA bloqueadas até atualização controlada do servidor.")
        st.caption(f"{AI_STATE_REVISION} · Sessão temporária {st.session_state.ai_diagnostic_session}")
        st.write("Ativação:", "Ligada" if st.session_state.get("ai_enabled") else "Desligada")
        st.write("Credencial:", "Presente" if st.session_state.get("groq_api_key") else "Ausente")
        st.write("Consentimento:", "Concedido" if st.session_state.get("ai_consent") else "Não concedido")
        status = st.session_state.get("ai_connection_status")
        st.write("Último teste de conexão:", "Sucesso" if status and status[0] == "success" else "Não validado")
        st.caption("A sessão é temporária. Recarregar a aba pode iniciar outra sessão. Nenhum segredo é mostrado aqui.")
