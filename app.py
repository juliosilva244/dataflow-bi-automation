from __future__ import annotations

from datetime import datetime
from textwrap import dedent

import pandas as pd
import streamlit as st

from assets.styles import load_css
from components.ai_assistant import render_ai_assistant
from components.charts import render_charts
from components.insights import render_insights
from components.kpis import render_kpis
from components.sidebar import render_sidebar
from components.tables import render_table
from services.exporter import gerar_excel, gerar_pdf
from services.loader import carregar_dados
from services.metrics_engine import construir_analytics_state


st.set_page_config(
    page_title="DataFlow BI Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


def render_html(content: str) -> None:
    st.markdown(dedent(content).strip(), unsafe_allow_html=True)


def init_session_state() -> None:
    defaults = {
        "selected_primary_dimension": [],
        "selected_secondary_dimension": [],
        "selected_periodo": "Tudo",
        "active_page": "Painel",
        "ai_mode": "Executivo",
        "ai_enabled": True,
        "chat_history": [],
        "debug_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def safe_session_list(key: str, valid_options: list[str]) -> None:
    current_values = st.session_state.get(key, [])
    if not isinstance(current_values, list):
        st.session_state[key] = []
        return
    st.session_state[key] = [value for value in current_values if value in valid_options]


def get_page_title(active_page: str) -> str:
    page_titles = {
        "Painel": "Painel Executivo",
        "Performance": "Desempenho Analítico",
        "DimensaoSecundaria": "Análise por Dimensão Secundária",
        "DimensaoPrincipal": "Análise por Dimensão Principal",
        "Relatorios": "Relatórios Executivos",
        "Exportacoes": "Central de Exportações",
    }
    return page_titles.get(active_page, "Painel Executivo")


def render_active_filters_summary(primary_values, secondary_values, date_range, primary_label: str, secondary_label: str) -> None:
    active_filters = []
    if primary_values:
        active_filters.append(f"🧭 {len(primary_values)} {primary_label}")
    if secondary_values:
        active_filters.append(f"📦 {len(secondary_values)} {secondary_label}")
    if date_range and len(date_range) == 2:
        start, end = date_range
        active_filters.append(f"📅 {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}")
    summary = " | ".join(active_filters) if active_filters else "Nenhum filtro avançado ativo"
    st.info(f"Filtros ativos: {summary}")


def get_schema_from_df(df: pd.DataFrame) -> dict:
    try:
        state = construir_analytics_state(df)
        return state.get("schema", {}) or {}
    except Exception:
        return {}


def render_top_controls():
    with st.container():
        col_upload, col_periodo, col_debug = st.columns([3, 2, 1])
        with col_upload:
            arquivo_upload = st.file_uploader("📤 Carregar Excel ou CSV", type=["xlsx", "xls", "csv"], label_visibility="visible")
        with col_periodo:
            periodo = st.selectbox("🗓️ Período", ["Tudo", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Ano atual"], key="selected_periodo")
        with col_debug:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            st.toggle("Debug", key="debug_mode")
    return arquivo_upload, periodo


def render_header(origem_dados: str, schema: dict) -> None:
    domain = schema.get("domain", "universal")
    metric_column = schema.get("metric_column") or "métrica principal"
    page_title = get_page_title(st.session_state.get("active_page", "Painel"))
    render_html(
        f"""
        <div class="hero-block">
            <div class="hero-eyebrow">DataFlow BI Automation</div>
            <div class="main-title">{page_title}</div>
            <div class="main-subtitle">
                Plataforma inteligente de Business Intelligence para análise automática de planilhas,
                geração de KPIs, visualizações executivas e insights estratégicos.
                Domínio detectado: <strong>{domain}</strong>. Métrica principal:
                <strong>{metric_column}</strong>.
            </div>
            <div class="source-card">📁 Fonte de dados: <strong>{origem_dados}</strong></div>
        </div>
        """
    )


def render_filters(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    render_html(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Filtros Inteligentes</div>
                <div class="section-subtitle">Segmentação analítica adaptada automaticamente à planilha carregada.</div>
            </div>
        </div>
        """
    )

    primary_col = schema.get("primary_dimension")
    secondary_col = schema.get("secondary_dimension")
    data_col = schema.get("date_column")
    primary_label = primary_col or "Dimensão Principal"
    secondary_label = secondary_col or "Dimensão Secundária"
    df_filtrado = df.copy()

    if data_col and data_col in df_filtrado.columns:
        df_filtrado[data_col] = pd.to_datetime(df_filtrado[data_col], errors="coerce", dayfirst=True)

    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.4, 0.7])
    primary_selected = []
    secondary_selected = []
    date_range = None

    with col1:
        if primary_col and primary_col in df_filtrado.columns:
            primary_options = sorted(df_filtrado[primary_col].dropna().astype(str).unique().tolist())
            safe_session_list("selected_primary_dimension", primary_options)
            primary_selected = st.multiselect(f"🧭 {primary_label}", options=primary_options, key="selected_primary_dimension")

    with col2:
        if secondary_col and secondary_col in df_filtrado.columns and secondary_col != primary_col:
            secondary_options = sorted(df_filtrado[secondary_col].dropna().astype(str).unique().tolist())
            safe_session_list("selected_secondary_dimension", secondary_options)
            secondary_selected = st.multiselect(f"📦 {secondary_label}", options=secondary_options, key="selected_secondary_dimension")

    with col3:
        if data_col and data_col in df_filtrado.columns:
            min_date = df_filtrado[data_col].min()
            max_date = df_filtrado[data_col].max()
            if pd.notnull(min_date) and pd.notnull(max_date):
                date_range = st.date_input("📅 Intervalo de datas", value=(min_date.date(), max_date.date()), key="selected_date_range")

    with col4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Resetar", width="stretch"):
            st.session_state["selected_primary_dimension"] = []
            st.session_state["selected_secondary_dimension"] = []
            if "selected_date_range" in st.session_state:
                del st.session_state["selected_date_range"]
            st.rerun()

    if primary_selected and primary_col and primary_col in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[primary_col].astype(str).isin(primary_selected)]
    if secondary_selected and secondary_col and secondary_col in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[secondary_col].astype(str).isin(secondary_selected)]
    if date_range and len(date_range) == 2 and data_col and data_col in df_filtrado.columns:
        start_date = pd.Timestamp(date_range[0])
        end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
        df_filtrado = df_filtrado[(df_filtrado[data_col] >= start_date) & (df_filtrado[data_col] < end_date)]

    render_active_filters_summary(primary_selected, secondary_selected, date_range, primary_label, secondary_label)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Registros filtrados", f"{len(df_filtrado):,}")
    with col_info2:
        st.metric("Colunas disponíveis", len(df_filtrado.columns))
    with col_info3:
        percentual = (len(df_filtrado) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Base analisada", f"{percentual:.1f}%")
    return df_filtrado


def render_schema_warning(analytics_state: dict) -> None:
    quality = analytics_state.get("quality", {})
    warnings = quality.get("schema_warnings", []) or []
    missing = quality.get("colunas_ausentes", []) or []
    if warnings:
        st.warning(" | ".join(warnings))
    elif missing:
        st.info("Colunas opcionais não detectadas: " + ", ".join(missing) + ". O dashboard continuará funcionando com os dados disponíveis.")


def render_status_bar(df: pd.DataFrame, origem_dados: str, analytics_state: dict) -> None:
    total_linhas = len(df)
    total_colunas = len(df.columns)
    ultima_atualizacao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    quality = analytics_state.get("quality", {})
    score_schema = quality.get("score_schema", 0)
    render_html(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Status Operacional</div>
                <div class="section-subtitle">Resumo técnico da base carregada</div>
            </div>
        </div>
        """
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Registros", f"{total_linhas:,}")
    with col2:
        st.metric("Colunas", total_colunas)
    with col3:
        st.metric("Origem", origem_dados)
    with col4:
        st.metric("Schema", f"{score_schema}%")
    with col5:
        st.metric("Atualização", ultima_atualizacao)
    render_schema_warning(analytics_state)


def render_debug_panel(df_filtrado: pd.DataFrame, analytics_state: dict) -> None:
    if not st.session_state.get("debug_mode", False):
        return
    charts = analytics_state.get("charts", {})
    st.divider()
    st.subheader("🧪 DEBUG — Payload Universal")
    st.write("DEBUG — DataFrame filtrado")
    st.dataframe(df_filtrado, width="stretch")
    for key in ["primary_dimension_summary", "secondary_dimension_summary", "revenue_by_month", "revenue_by_category"]:
        st.write(f"DEBUG — {key}")
        st.dataframe(charts.get(key, pd.DataFrame()), width="stretch")
    st.write("DEBUG — Schema")
    st.json(analytics_state.get("schema", {}))


def render_report_page(df: pd.DataFrame, origem_dados: str, analytics_state: dict) -> None:
    render_html(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Relatórios Executivos</div>
                <div class="section-subtitle">Visão consolidada para apresentação, análise e tomada de decisão.</div>
            </div>
        </div>
        """
    )
    render_kpis(analytics_state)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    render_insights(analytics_state)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    render_status_bar(df, origem_dados, analytics_state)


def render_export_page(analytics_state: dict) -> None:
    render_html(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Central de Exportações</div>
                <div class="section-subtitle">Gere relatórios prontos para análise externa, envio ou arquivamento.</div>
            </div>
        </div>
        """
    )
    col_excel, col_pdf = st.columns(2)
    with col_excel:
        excel_file = gerar_excel(analytics_state)
        st.download_button("📥 Baixar Relatório Excel", data=excel_file, file_name="relatorio_dataflow.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    with col_pdf:
        pdf_file = gerar_pdf(analytics_state)
        st.download_button("📄 Baixar Relatório PDF", data=pdf_file, file_name="relatorio_dataflow.pdf", mime="application/pdf", width="stretch")


def render_ai_if_enabled(analytics_state: dict) -> None:
    if st.session_state.get("ai_enabled", True):
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_ai_assistant(analytics_state)


def main() -> None:
    init_session_state()
    arquivo_upload, periodo = render_top_controls()
    df, origem_dados, erro = carregar_dados(arquivo_upload=arquivo_upload, periodo=periodo)

    if erro:
        render_sidebar()
        st.error(erro)
        st.stop()

    base_schema = get_schema_from_df(df)
    render_sidebar(base_schema)
    render_header(origem_dados, base_schema)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    df_filtrado = render_filters(df, base_schema)
    analytics_state = construir_analytics_state(df_filtrado)
    active_page = st.session_state["active_page"]
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    if active_page == "Painel":
        render_kpis(analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_charts(metricas=analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_insights(analytics_state)
        render_ai_if_enabled(analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_status_bar(df_filtrado, origem_dados, analytics_state)
        render_table(df_filtrado)

    elif active_page == "Performance":
        render_kpis(analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_charts(metricas=analytics_state)
        render_ai_if_enabled(analytics_state)

    elif active_page == "DimensaoSecundaria":
        render_insights(analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_table(df_filtrado)
        render_ai_if_enabled(analytics_state)

    elif active_page == "DimensaoPrincipal":
        render_charts(metricas=analytics_state)
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        render_table(df_filtrado)
        render_ai_if_enabled(analytics_state)

    elif active_page == "Relatorios":
        render_report_page(df_filtrado, origem_dados, analytics_state)
        render_ai_if_enabled(analytics_state)

    elif active_page == "Exportacoes":
        render_export_page(analytics_state)

    render_debug_panel(df_filtrado, analytics_state)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
