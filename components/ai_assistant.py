import streamlit as st

from components.ai_state import (
    commit_ai_widget,
    prepare_ai_widget,
    render_ai_state_diagnostics,
)
from components.analytical_scope import render_analytical_scope
from components.chat_message import render_chat_history, sanitize_content
from services.ai_presentation import GroundedAnswer
from services.ai_trace import generation_trace, trace_stage
from services.errors import DataFlowError
from services.llm_router import get_llm_router, new_anonymization_context
from services.logging_config import get_logger
from services.providers.groq_provider import (
    AI_GENERATION_REVISION,
    configured_groq_model,
    legacy_groq_model_configured,
)

logger = get_logger(__name__)


def initialize_ai_state():
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    if "groq_api_key" not in st.session_state:
        st.session_state.groq_api_key = ""
    if "ai_connection_status" not in st.session_state:
        st.session_state.ai_connection_status = None


def _session_router():
    if "ai_anonymization_context" not in st.session_state:
        st.session_state.ai_anonymization_context = new_anonymization_context()
    return get_llm_router(
        api_key=st.session_state.get("groq_api_key", ""),
        rate_limiter=st.session_state.get("ai_rate_limiter"),
        anonymization_context=st.session_state.ai_anonymization_context,
    )


def invalidate_session_key_state():
    """Invalidate trust derived from a previously entered session credential."""
    st.session_state.ai_connection_status = None
    st.session_state.ai_consent = False


def update_session_key():
    commit_ai_widget("groq_api_key", "_assistant_groq_api_key")
    invalidate_session_key_state()


def remove_session_key():
    st.session_state.groq_api_key = ""
    st.session_state._assistant_groq_api_key = ""
    invalidate_session_key_state()


def test_session_connection():
    router = _session_router()
    try:
        router.test_connection()
        st.session_state.ai_connection_status = (
            "success",
            "Credencial aceita e modelo listado. A geração de respostas ainda não foi testada.",
        )
    except DataFlowError as error:
        logger.warning("Teste de conexão Groq bloqueado codigo=%s", error.code)
        st.session_state.ai_connection_status = ("error", error.public_message)
    except Exception as error:
        logger.warning("Teste de conexão Groq falhou tipo=%s", type(error).__name__)
        st.session_state.ai_connection_status = (
            "error",
            "Não foi possível validar a chave. Confira a credencial e tente novamente.",
        )


def add_message(role, content):
    message = {"role": role, "content": sanitize_content(content)}
    presentation = getattr(content, "presentation", None)
    if role == "assistant" and isinstance(presentation, dict):
        message["presentation"] = presentation
    st.session_state.ai_messages.append(message)
    if role == "assistant":
        trace_stage("ui.history_added", trace=st.session_state.get("ai_last_trace"))


def clear_ai_history():
    st.session_state.ai_messages = []


def ask_ai(question, analytics_state):
    with generation_trace(configured_groq_model()) as trace:
        st.session_state.ai_last_trace = trace
        trace_stage("ui.request")
        try:
            router = _session_router()
            history = st.session_state.ai_messages
            response = router.generate_response(
                question=question,
                analytics_state=analytics_state,
                history=history,
                enabled=bool(st.session_state.get("ai_enabled", False)),
                consent=bool(st.session_state.get("ai_consent", False)),
                anonymize=bool(st.session_state.get("ai_anonymize", True)),
            )
            result = sanitize_content(response)
            trace_stage("ui.sanitized")
            presentation = getattr(response, "presentation", None)
            return GroundedAnswer(result, presentation) if isinstance(presentation, dict) else result
        except DataFlowError as error:
            trace_stage("ui.blocked", error)
            return f"{error.public_message} (referência: {trace.correlation})"
        except Exception as error:
            trace_stage("ui.error", error)
            return (
                "Não foi possível consultar o assistente agora. "
                f"Nenhuma chave ou detalhe técnico foi exibido. (referência: {trace.correlation})"
            )


def render_quick_actions():
    col1, col2, col3, col4, col5 = st.columns(
        [1, 1.2, 1, 1.25, 0.65]
    )

    selected = None

    with col1:
        if st.button(
            "Gere um resumo.",
            width="stretch",
            key="ai_btn_summary",
        ):
            selected = "gere um resumo executivo"

    with col2:
        if st.button(
            "Maior risco?",
            width="stretch",
            key="ai_btn_risk",
        ):
            selected = "qual o maior risco da operação?"

    with col3:
        if st.button(
            "Loja Norte",
            width="stretch",
            key="ai_btn_store",
        ):
            selected = "como está a loja norte?"

    with col4:
        if st.button(
            "Produto líder",
            width="stretch",
            key="ai_btn_product",
        ):
            selected = "qual produto liderou o faturamento?"

    with col5:
        if st.button(
            "Limpar",
            width="stretch",
            key="ai_btn_clear",
        ):
            clear_ai_history()
            st.rerun()

    return selected


def render_ai_assistant(analytics_state):
    initialize_ai_state()
    render_ai_state_diagnostics()
    st.caption(f"{AI_GENERATION_REVISION} · Modelo de geração Groq: {configured_groq_model()}")
    if legacy_groq_model_configured():
        st.info(
            "A configuração antiga llama-3.1-8b-instant foi substituída por openai/gpt-oss-20b, "
            "conforme a migração recomendada pela Groq. Nenhuma chamada é feita automaticamente."
        )

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

        st.text_input(
            "Chave Groq desta sessão",
            key=prepare_ai_widget("groq_api_key", "_assistant_groq_api_key"),
            type="password",
            placeholder="gsk_...",
            help=(
                "A chave permanece apenas na memória desta sessão Streamlit. "
                "Ela não é gravada em arquivo, banco, log ou relatório."
            ),
            on_change=update_session_key,
        )
        key_present = bool(str(st.session_state.get("groq_api_key", "")).strip())
        test_col, remove_col = st.columns(2)
        with test_col:
            st.button(
                "Testar conexão",
                key="ai_test_connection",
                disabled=not key_present,
                on_click=test_session_connection,
                width="stretch",
            )
        with remove_col:
            st.button(
                "Remover chave",
                key="ai_remove_session_key",
                disabled=not key_present,
                on_click=remove_session_key,
                width="stretch",
            )
        st.caption(
            "BYOK temporário: a chave não sobrevive ao encerramento da sessão. "
            "Em implantação remota, use somente HTTPS."
        )

        status = st.session_state.get("ai_connection_status")
        if status:
            level, message = status
            if level == "success":
                st.success(message)
            else:
                st.error(message)

        router = _session_router()
        if not router.is_configured():
            st.info(
                "O dashboard está operacional sem IA. Informe uma chave Groq temporária "
                "acima para habilitar o assistente nesta sessão."
            )
            return

        if not st.session_state.get("ai_enabled", False):
            st.info("O assistente de IA está desativado. Nenhuma chamada externa será feita.")
            return

        st.markdown(
            """
<div class="section-subtitle">
Copiloto executivo com Groq + LLM Router + contexto analítico
</div>
""",
            unsafe_allow_html=True,
        )

        st.checkbox(
            "Autorizo o envio dos KPIs exibidos e da minha pergunta ao provedor externo de IA.",
            key=prepare_ai_widget("ai_consent", "_assistant_ai_consent"),
            on_change=commit_ai_widget,
            args=("ai_consent", "_assistant_ai_consent"),
        )
        st.toggle(
            "Anonimizar lojas, produtos e identificadores antes do envio",
            key=prepare_ai_widget("ai_anonymize", "_assistant_ai_anonymize"),
            on_change=commit_ai_widget,
            args=("ai_anonymize", "_assistant_ai_anonymize"),
            help=(
                "Substitui nomes conhecidos por pseudônimos e mascara e-mails e documentos. "
                "Somente KPIs agregados são enviados."
            ),
        )

        if not st.session_state.get("ai_consent", False):
            st.warning(
                "Aguardando consentimento. Nenhum dado será enviado enquanto esta opção "
                "não for marcada."
            )
            return

        render_analytical_scope(analytics_state)
        quick_question = render_quick_actions()
        st.caption(
            "Respostas ancoradas: a IA seleciona evidências; números, critérios e períodos "
            "são validados e apresentados localmente. Histórico anterior não foi revalidado."
        )

        st.markdown(
            "<div style='height:12px'></div>",
            unsafe_allow_html=True,
        )

        try:
            render_chat_history(st.session_state.ai_messages)
        except Exception as error:
            trace_stage("ui.render_error", error, trace=st.session_state.get("ai_last_trace"))
            raise
        trace_stage("ui.rendered", trace=st.session_state.get("ai_last_trace"))

        question = st.chat_input(
            "Pergunte algo sobre os dados...",
            key="ai_chat_input",
        )

        if quick_question:
            question = quick_question

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
