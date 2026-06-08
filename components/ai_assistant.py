from __future__ import annotations

import streamlit as st

from components.chat_message import render_chat_history, sanitize_content
from services.llm_router import get_llm_router


def initialize_ai_state() -> None:
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []


def add_message(role: str, content: str) -> None:
    st.session_state.ai_messages.append({"role": role, "content": sanitize_content(content)})


def clear_ai_history() -> None:
    st.session_state.ai_messages = []


def ask_ai(question: str, analytics_state: dict) -> str:
    router = get_llm_router()
    history = st.session_state.get("ai_messages", [])
    response = router.generate_response(question=question, analytics_state=analytics_state, history=history)
    return sanitize_content(response)


def render_quick_actions(schema: dict) -> str | None:
    primary_label = schema.get("primary_dimension") or "dimensão principal"
    secondary_label = schema.get("secondary_dimension") or "dimensão secundária"

    col1, col2, col3, col4, col5 = st.columns([1, 1.1, 1.2, 1.2, 0.75])
    selected = None

    with col1:
        if st.button("Resumo", width="stretch", key="ai_btn_summary"):
            selected = "gere um resumo executivo objetivo desta base"
    with col2:
        if st.button("Risco", width="stretch", key="ai_btn_risk"):
            selected = "qual é o maior risco detectável pelos dados?"
    with col3:
        if st.button(f"Top {primary_label}", width="stretch", key="ai_btn_primary"):
            selected = f"analise a performance da dimensão {primary_label}"
    with col4:
        if st.button(f"Top {secondary_label}", width="stretch", key="ai_btn_secondary"):
            selected = f"analise a performance da dimensão {secondary_label}"
    with col5:
        if st.button("Limpar", width="stretch", key="ai_btn_clear"):
            clear_ai_history()
            st.rerun()

    return selected


def render_ai_assistant(analytics_state: dict) -> None:
    initialize_ai_state()
    schema = analytics_state.get("schema", {}) or {}

    with st.expander("🧠 Assistente Executivo de IA", expanded=False):
        st.markdown(
            """
<div class="section-header">
  <div>
    <div class="section-title">AI BI Assistant</div>
    <div class="section-subtitle">Copiloto executivo conectado ao contexto analítico da base carregada.</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        quick_question = render_quick_actions(schema)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        render_chat_history(st.session_state.ai_messages)

        manual_question = st.text_input(
            "Pergunte algo sobre os dados",
            placeholder="Ex.: quais são os riscos e próximas ações?",
            key="ai_manual_question_input",
        )
        send_manual_question = st.button("Enviar pergunta para IA", key="ai_send_manual_question", width="stretch")

        question = quick_question or (manual_question.strip() if send_manual_question and manual_question.strip() else None)

        if question:
            add_message("user", question)
            with st.spinner("Analisando indicadores..."):
                response = ask_ai(question, analytics_state)
            add_message("assistant", response)
            st.rerun()
