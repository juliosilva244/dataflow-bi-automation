import streamlit as st


def render_sidebar(schema: dict | None = None):
    schema = schema or {}

    primary_dimension = schema.get("primary_dimension") or "Dimensão Principal"
    secondary_dimension = schema.get("secondary_dimension") or "Dimensão Secundária"

    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Painel"

    if "ai_enabled" not in st.session_state:
        st.session_state["ai_enabled"] = True

    if "ai_mode" not in st.session_state:
        st.session_state["ai_mode"] = "Executivo"

    with st.sidebar:
        st.markdown(
            "<div style='display:flex;align-items:center;gap:12px;margin-bottom:22px;padding:10px 0 4px 0;'>"
            "<div style='width:44px;height:44px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(14,165,233,0.25),rgba(56,189,248,0.08));border:1px solid rgba(56,189,248,0.35);font-size:1.75rem;box-shadow:0 0 24px rgba(14,165,233,0.16);'>📊</div>"
            "<div>"
            "<div style='font-size:1.05rem;line-height:1.15;font-weight:900;color:#ffffff;letter-spacing:-0.02em;'>DataFlow BI<br>Automation</div>"
            "<div style='margin-top:6px;font-size:0.62rem;line-height:1.35;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;font-weight:700;'>Business Intelligence<br>Analytics Platform</div>"
            "</div>"
            "</div>"
            "<div style='height:1px;width:100%;background:linear-gradient(90deg,rgba(14,165,233,0.55),rgba(255,255,255,0.06));margin:10px 0 22px 0;'></div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Navegação")

        pages = {
            "Painel": "🏠 Painel Executivo",
            "Performance": "📈 Desempenho",
            "DimensaoSecundaria": f"📦 {secondary_dimension}",
            "DimensaoPrincipal": f"🏬 {primary_dimension}",
            "Relatorios": "📄 Relatórios",
            "Exportacoes": "📤 Exportações",
        }

        for page_id, page_name in pages.items():
            is_active = st.session_state.get("active_page") == page_id

            if st.button(
                page_name,
                key=f"nav_{page_id}",
                width="stretch",
                type="primary" if is_active else "secondary",
            ):
                st.session_state["active_page"] = page_id
                st.rerun()

        st.markdown(
            "<div style='height:1px;width:100%;background:rgba(255,255,255,0.08);margin:22px 0;'></div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Assistente de IA")

        st.selectbox(
            "Modo Analítico",
            ["Executivo", "Operacional", "Previsão", "Anomalias"],
            key="ai_mode",
        )

        st.toggle("Ativar Assistente de IA", key="ai_enabled")

        if st.session_state.get("ai_enabled"):
            st.markdown(
                "<div style='background:linear-gradient(135deg,rgba(14,165,233,0.16),rgba(15,23,42,0.55));border:1px solid rgba(14,165,233,0.35);border-radius:14px;padding:14px;margin-top:12px;box-shadow:0 0 22px rgba(14,165,233,0.10);'>"
                "<div style='font-size:0.78rem;font-weight:900;color:#38bdf8;margin-bottom:6px;'>🟢 DataFlow AI Analyst</div>"
                "<div style='font-size:0.68rem;color:#94a3b8;line-height:1.45;'>Assistente analítico conectado para apoiar leitura de dados, identificação de padrões e geração de insights executivos.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:rgba(248,113,113,0.10);border:1px solid rgba(248,113,113,0.25);border-radius:14px;padding:14px;margin-top:12px;'>"
                "<div style='font-size:0.78rem;font-weight:900;color:#f87171;margin-bottom:6px;'>🔴 DataFlow AI Offline</div>"
                "<div style='font-size:0.68rem;color:#94a3b8;line-height:1.45;'>O assistente de IA está desativado.</div>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='height:1px;width:100%;background:rgba(255,255,255,0.08);margin:22px 0;'></div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Tempo de execução")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Latência", "0.3s")

        with col2:
            st.metric("Status", "Online")

        st.markdown(
            "<div style='margin-top:22px;padding:12px 10px;border-radius:14px;background:rgba(15,23,42,0.45);border:1px solid rgba(148,163,184,0.14);text-align:center;'>"
            "<div style='font-size:0.68rem;color:#94a3b8;font-weight:700;margin-bottom:3px;'>DataFlow BI Automation</div>"
            "<div style='font-size:0.62rem;color:#64748b;line-height:1.35;'>Universal Analytics Runtime v3.1<br>Portfolio BI Platform</div>"
            "</div>",
            unsafe_allow_html=True,
        )