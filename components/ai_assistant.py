import streamlit as st

from components.chat_message import render_chat_history, sanitize_content
from services.llm_router import get_llm_router


def initialize_ai_state():
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []


def add_message(role, content):
    st.session_state.ai_messages.append(
        {
            "role": role,
            "content": sanitize_content(content),
        }
    )


def clear_ai_history():
    st.session_state.ai_messages = []


def ask_ai(question, analytics_state):
    router = get_llm_router()
    history = st.session_state.ai_messages

    try:
        response = router.generate_response(
            question=question,
            analytics_state=analytics_state,
            history=history,
        )
        return sanitize_content(response)

    except Exception as error:
        return f"Erro ao gerar resposta: {str(error)}"


def render_quick_actions():
    col1, col2, col3, col4, col5 = st.columns(
        [1, 1.2, 1, 1.25, 0.65]
    )

    selected = None

    with col1:
        if st.button(
            "Gere um resumo.",
            use_container_width=True,
            key="ai_btn_summary",
        ):
            selected = "gere um resumo executivo"

    with col2:
        if st.button(
            "Maior risco?",
            use_container_width=True,
            key="ai_btn_risk",
        ):
            selected = "qual o maior risco da operação?"

    with col3:
        if st.button(
            "Loja Norte",
            use_container_width=True,
            key="ai_btn_store",
        ):
            selected = "como está a loja norte?"

    with col4:
        if st.button(
            "Produto líder",
            use_container_width=True,
            key="ai_btn_product",
        ):
            selected = "qual produto liderou o faturamento?"

    with col5:
        if st.button(
            "Limpar",
            use_container_width=True,
            key="ai_btn_clear",
        ):
            clear_ai_history()
            st.rerun()

    return selected


def render_ai_assistant(analytics_state):
    initialize_ai_state()

    with st.expander(
        "🧠 Assistente Executivo de IA",
        expanded=True,
    ):
        st.markdown(
            """
<div class="main-title">
Assistente de IA para BI
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div class="section-subtitle">
Copiloto executivo com Groq + LLM Router + contexto analítico
</div>
""",
            unsafe_allow_html=True,
        )

        quick_question = render_quick_actions()

        st.markdown(
            "<div style='height:12px'></div>",
            unsafe_allow_html=True,
        )

        render_chat_history(
            st.session_state.ai_messages
        )

        manual_question = st.text_input(
            "Pergunte algo sobre os dados...",
            placeholder="Digite sua pergunta aqui...",
            key="ai_manual_question_input",
        )

        send_manual_question = st.button(
            "Enviar",
            key="ai_send_manual_question",
            use_container_width=True,
        )

        question = None

        if quick_question:
            question = quick_question
        elif send_manual_question and manual_question.strip():
            question = manual_question.strip()

        if question:
            add_message(
                "user",
                question,
            )

            with st.spinner(
                "Analisando indicadores..."
            ):
                response = ask_ai(
                    question,
                    analytics_state,
                )

            add_message(
                "assistant",
                response,
            )

            st.rerun()