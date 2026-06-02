import streamlit as st


def render_sidebar(schema: dict | None = None):
    schema = schema or {}

    primary_dimension = schema.get("primary_dimension") or "Dimensão Principal"
    secondary_dimension = schema.get("secondary_dimension") or "Dimensão Secundária"

    with st.sidebar:
        st.markdown(
            """
            <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
                <div style='font-size: 2.5rem;'>📊</div>
                <div>
                    <div style='font-size: 1.2rem; font-weight: 800; color: #ffffff;'>DataFlow BI</div>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;'>Universal Analytics Platform</div>
                </div>
            </div>
            <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Navegação")

        pages = {
            "Painel": "🏠 Painel Executivo",
            "Performance": "📈 Performance",
            "DimensaoSecundaria": f"📦 {secondary_dimension}",
            "DimensaoPrincipal": f"🏬 {primary_dimension}",
            "Relatorios": "📄 Relatórios",
            "Exportacoes": "📤 Exportações",
        }

        for page_id, page_name in pages.items():
            if st.button(
                page_name,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if st.session_state["active_page"] == page_id else "secondary",
            ):
                st.session_state["active_page"] = page_id
                st.rerun()

        st.markdown(
            "<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;'>",
            unsafe_allow_html=True,
        )

        st.markdown("### Assistente de IA")

        st.selectbox(
            "Modo Analítico",
            ["Executivo", "Operacional", "Previsão", "Anomalias"],
            key="ai_mode",
        )

        st.toggle("Ativar Assistente de IA", key="ai_enabled")

        if st.session_state["ai_enabled"]:
            st.markdown(
                """
                <div style='background: rgba(14,165,233,0.1); border: 1px solid rgba(14,165,233,0.2); border-radius: 12px; padding: 12px; margin-top: 10px;'>
                    <div style='font-size: 0.8rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;'>🟢 Assistente de IA Online</div>
                    <div style='font-size: 0.7rem; color: #94a3b8;'>Runtime analítico conectado ao mecanismo inteligente do DataFlow BI.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style='background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.2); border-radius: 12px; padding: 12px; margin-top: 10px;'>
                    <div style='font-size: 0.8rem; font-weight: 700; color: #f87171; margin-bottom: 4px;'>🔴 Assistente de IA Offline</div>
                    <div style='font-size: 0.7rem; color: #94a3b8;'>O assistente de IA está desativado.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;'>",
            unsafe_allow_html=True,
        )

        st.markdown("### Runtime")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Latência", "0.3s")

        with col2:
            st.metric("Status", "Online")

        st.markdown(
            """
            <div style='margin-top: 20px; font-size: 0.7rem; color: #64748b; text-align: center;'>
                DataFlow BI Automation<br>
                Universal Analytics Runtime v3.1
            </div>
            """,
            unsafe_allow_html=True,
        )