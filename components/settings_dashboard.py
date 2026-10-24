from __future__ import annotations

import platform
from importlib.metadata import version

import streamlit as st

from components.ai_state import (
    commit_ai_widget,
    prepare_ai_widget,
    render_ai_state_diagnostics,
)
from services.llm_router import get_llm_router
from services.preferences import (
    ALLOWED_DENSITIES,
    ALLOWED_METRICS,
    ALLOWED_MOTION,
    ALLOWED_RANKING_SIZES,
    preference_key,
    restore_preference_defaults,
    revoke_ai_consent,
)
from services.security import escape_html
from services.settings import get_performance_settings, get_security_settings


def _yes_no(value: bool) -> str:
    return "Ativo" if value else "Inativo"


def _provider_state() -> tuple[str, str]:
    router = get_llm_router(
        api_key=st.session_state.get("groq_api_key", ""),
        rate_limiter=st.session_state.get("ai_rate_limiter"),
    )
    provider = router.provider.upper() if router.provider else "Não configurado"
    availability = "Configurado, não testado" if router.is_configured() else "Não configurado"
    return provider, availability


def _restore_preferences() -> None:
    restore_preference_defaults(st.session_state)


def _revoke_consent() -> None:
    revoke_ai_consent(st.session_state)


def _clear_session_cache() -> None:
    cache = st.session_state.get("performance_cache")
    if cache is not None:
        cache.clear()
    for key in (
        "prepared_export_key",
        "prepared_export_bytes",
        "report_download_signature",
        "report_download_content",
        "report_download_name",
        "report_download_mime",
    ):
        st.session_state[key] = None
    st.session_state.settings_confirm_cache_clear = False
    st.session_state.settings_cache_cleared = True


def render_settings_dashboard(df, source: str) -> None:
    security = get_security_settings()
    performance = get_performance_settings()
    provider, provider_state = _provider_state()
    ai_enabled = bool(st.session_state.get("ai_enabled", False))
    ai_consent = bool(st.session_state.get("ai_consent", False))
    privacy_state = "Consentimento externo ativo" if ai_consent else "Processamento local por padrão"

    st.title("Configurações", anchor=False)
    st.html(
        f"""
        <div class="settings-hero">
          <div><div class="settings-eyebrow">CONTROLE E GOVERNANÇA</div>
          <div class="settings-title">Central de Configurações</div>
          <div class="settings-subtitle">Personalize sua experiência, controle a privacidade e acompanhe o estado do sistema.</div></div>
          <div class="settings-meta"><span>Ultimate 2.0</span><span>{escape_html(source)}</span>
          <span>{len(df):,} registros</span><span class="settings-safe">{privacy_state}</span></div>
        </div>
        """
    )

    with st.container(key="settings-status"):
        cols = st.columns(4)
        statuses = (
            ("Sessão", "Ativa", "Estado atual em memória"),
            ("Processamento", "Local", "IA externa é opcional"),
            ("Inteligência artificial", _yes_no(ai_enabled), provider_state),
            ("Privacidade", "Protegida" if not ai_consent else "Consentida", privacy_state),
        )
        for column, (label, value, detail) in zip(cols, statuses, strict=True):
            with column:
                st.html(
                    f'<div class="settings-status-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>'
                )

    appearance, analytics, artificial, privacy, performance_tab, system = st.tabs(
        ["Aparência", "Análises", "Inteligência Artificial", "Privacidade", "Desempenho", "Sistema"]
    )

    with appearance:
        st.html('<div class="settings-section"><span>Aparência e experiência</span><small>Preferências válidas durante esta sessão</small></div>')
        left, right = st.columns(2)
        with left:
            st.selectbox("Densidade visual", ALLOWED_DENSITIES, key=preference_key("visual_density"))
            st.selectbox("Movimento e animações", ALLOWED_MOTION, key=preference_key("motion"))
        with right:
            st.toggle("Exibir dicas explicativas", key=preference_key("show_help"))
            st.toggle("Preferir números compactos", key=preference_key("compact_numbers"))
        if st.session_state[preference_key("show_help")]:
            st.info("As preferências são isoladas nesta sessão e sobrevivem aos reruns, mas não ao encerramento da sessão.")
        number = "R$ 1,23 milhão" if st.session_state[preference_key("compact_numbers")] else "R$ 1.234.567,89"
        st.html(f'<div class="settings-preview"><span>Prévia numérica · exemplo fictício</span><strong>{number}</strong><small>Apenas a apresentação muda; os cálculos permanecem intactos.</small></div>')

    with analytics:
        st.html('<div class="settings-section"><span>Preferências analíticas</span><small>Não alteram as métricas oficiais</small></div>')
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Itens preferidos em rankings", ALLOWED_RANKING_SIZES, key=preference_key("ranking_size"))
            st.selectbox("Métrica inicial preferida", ALLOWED_METRICS, key=preference_key("default_metric"))
        with col2:
            st.toggle("Exibir detalhes adicionais de anomalias", key=preference_key("show_anomaly_details"))
            st.warning("Alertas relevantes continuam presentes em análises e exportações, independentemente desta preferência.")
        st.caption("Estas preferências ficam disponíveis para componentes compatíveis; páginas já concluídas mantêm seus controles e cálculos atuais.")

    with artificial:
        render_ai_state_diagnostics()
        st.html('<div class="settings-section"><span>Governança de Inteligência Artificial</span><small>Chave individual mantida somente nesta sessão</small></div>')
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(
                "Ativar recursos opcionais de IA",
                key=prepare_ai_widget("ai_enabled", "_settings_ai_enabled"),
                on_change=commit_ai_widget,
                args=("ai_enabled", "_settings_ai_enabled"),
            )
            st.toggle(
                "Anonimizar identificadores antes do envio",
                key=prepare_ai_widget("ai_anonymize", "_settings_ai_anonymize"),
                on_change=commit_ai_widget,
                args=("ai_anonymize", "_settings_ai_anonymize"),
            )
        with col2:
            st.metric("Provedor selecionado", provider)
            st.metric("Disponibilidade", provider_state)
        consent_now = bool(st.session_state.get("ai_consent", False))
        if consent_now:
            st.warning("Existe consentimento para envio externo nesta sessão. Ele ainda depende da IA estar ativada.")
            st.button("Revogar consentimento externo", type="primary", on_click=_revoke_consent, key="settings_revoke_ai")
        else:
            st.success("Nenhum consentimento externo ativo. Novas chamadas permanecem bloqueadas.")
        st.caption("O consentimento só pode ser concedido na área de Inteligência Artificial, no contexto da utilização do assistente.")
        st.caption("A chave individual é informada e removida na página Inteligência Artificial; ela não é persistida em arquivos ou banco de dados.")

    with privacy:
        st.html('<div class="settings-section"><span>Privacidade e segurança</span><small>Controles e limites efetivamente aplicados</small></div>')
        cards = st.columns(3)
        values = (
            ("Envio externo", "Permitido somente com IA e consentimento"),
            ("Anonimização", _yes_no(bool(st.session_state.get("ai_anonymize", True)))),
            ("Segredos", "Não exibidos nem exportados"),
        )
        for col, (label, value) in zip(cards, values, strict=True):
            with col:
                st.html(f'<div class="settings-info-card"><span>{label}</span><strong>{value}</strong></div>')
        st.info("O carregamento, a normalização, os cálculos e as exportações são locais. O assistente de IA é opcional e pode enviar apenas o contexto autorizado a um provedor externo.")
        st.caption(f"Limites: upload {security.max_upload_bytes // 1024 // 1024} MB · {security.max_rows:,} linhas · {security.max_columns} colunas · {security.ai_max_output_tokens} tokens por resposta.")

    with performance_tab:
        st.html('<div class="settings-section"><span>Desempenho e sessão</span><small>Limpeza delimitada ao estado temporário desta sessão</small></div>')
        cache = st.session_state.get("performance_cache")
        cache_entries = len(cache) if cache is not None else 0
        cols = st.columns(3)
        cols[0].metric("Registros disponíveis", f"{len(df):,}")
        cols[1].metric("Itens no cache da sessão", cache_entries)
        cols[2].metric("Expiração configurada", f"{performance.cache_ttl_seconds}s")
        st.checkbox(
            "Confirmo que desejo limpar apenas cache e exportações temporárias desta sessão",
            key="settings_confirm_cache_clear",
        )
        st.button(
            "Limpar temporários da sessão",
            disabled=not st.session_state.get("settings_confirm_cache_clear", False),
            on_click=_clear_session_cache,
            key="settings_clear_cache",
        )
        if st.session_state.pop("settings_cache_cleared", False):
            st.success("Cache e exportações temporárias desta sessão foram limpos. Arquivos e dados originais não foram alterados.")

    with system:
        st.html('<div class="settings-section"><span>Informações do sistema</span><small>Sem caminhos privados, tokens ou variáveis sensíveis</small></div>')
        information = (
            ("Produto", "DataFlow Fusion Ultimate 2.0"),
            ("Python", platform.python_version()),
            ("Streamlit", version("streamlit")),
            ("Pandas", version("pandas")),
            ("Estado da aplicação", "Carregada"),
            ("Fonte ativa", source),
        )
        for col, (label, value) in zip(st.columns(3) * 2, information, strict=True):
            with col:
                st.html(f'<div class="settings-info-card"><span>{escape_html(label)}</span><strong>{escape_html(value)}</strong></div>')
        st.caption("A disponibilidade do provedor de IA indica somente presença de configuração; nenhuma conexão foi testada.")

    st.divider()
    restore_col, note_col = st.columns([1, 2.4])
    with restore_col:
        st.button("Restaurar preferências padrão", on_click=_restore_preferences, key="settings_restore_defaults", width="stretch")
    with note_col:
        st.caption("Restaura apenas aparência e preferências analíticas. IA, consentimento, dados, arquivos e configurações de segurança não são tornados mais permissivos.")
