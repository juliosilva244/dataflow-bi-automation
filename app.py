import pandas as pd
import streamlit as st

from assets.styles import load_css
from components.ai_assistant import render_ai_assistant
from components.analytical_scope import render_analytical_scope
from components.charts import (
    render_revenue_chart,
    render_store_chart,
)
from components.executive_dashboard import (
    display_name,
    render_ai_panel,
    render_category_donut,
    render_insight_row,
    render_kpi_strip,
    render_products_panel,
)
from components.products_dashboard import render_products_dashboard
from components.quality_dashboard import render_quality_dashboard
from components.reports_dashboard import render_reports_dashboard
from components.sales_dashboard import render_sales_dashboard
from components.settings_dashboard import render_settings_dashboard
from components.sidebar import PAGES, render_sidebar, render_sidebar_status, sidebar_layout_css
from components.stores_dashboard import render_stores_dashboard
from services.anomalies import detect_extreme_monetary_values, financial_anomaly_notice
from services.llm_router import SlidingWindowRateLimiter, ensure_current_rate_limiter
from services.loader import carregar_dados
from services.metrics_engine import build_revenue_by_month, construir_analytics_state
from services.performance import (
    SessionScopedCache,
    TelemetryCollector,
    get_cached_analytics,
)
from services.preferences import initialize_preferences, preference_css, read_preferences
from services.security import escape_html
from services.settings import get_performance_settings, get_security_settings


def navigate_to(page):
    st.session_state.active_page = page


def clear_filter_state():
    st.session_state.selected_lojas = []
    st.session_state.selected_produtos = []
    st.session_state.pop("selected_date_range", None)


def init_session_state():
    performance = get_performance_settings()
    security = get_security_settings()
    defaults = {
        "active_page": PAGES[0],
        "selected_lojas": [],
        "selected_produtos": [],
        "selected_periodo": "Tudo",
        "global_search": "",
        "ai_enabled": False,
        "ai_consent": False,
        "ai_anonymize": get_security_settings().ai_anonymize_default,
        "groq_api_key": "",
        "ai_connection_status": None,
        "ai_rate_limiter": SlidingWindowRateLimiter(security.ai_requests_per_minute),
        "performance_cache": SessionScopedCache(
            max_entries=performance.cache_max_entries,
            ttl_seconds=performance.cache_ttl_seconds,
        ),
        "performance_telemetry": TelemetryCollector(),
        "prepared_export_key": None,
        "prepared_export_bytes": None,
        "sidebar_menu_search": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.ai_rate_limiter = ensure_current_rate_limiter(
        st.session_state.ai_rate_limiter, security.ai_requests_per_minute,
    )
    initialize_preferences(st.session_state)


def page_header(title, subtitle, source=None):
    st.markdown('<div class="eyebrow">DATAFLOW FUSION · ANALYTICS WORKSPACE</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{escape_html(subtitle)}</div>', unsafe_allow_html=True)
    if source:
        st.markdown(
            f'<div class="source-pill">Fonte: {escape_html(source)}</div>',
            unsafe_allow_html=True,
        )


def render_data_controls():
    st.markdown('<div class="fusion-topbar"><div class="fusion-eyebrow">CENTRAL ANALÍTICA</div></div>', unsafe_allow_html=True)
    with st.container(border=True, key="topbar-controls"):
        search_col, period_col, data_col, report_col = st.columns([3.2, 1.35, 0.8, 1.15])
        with search_col:
            st.text_input(
                "Busca",
                key="global_search",
                placeholder="Buscar produto ou loja...",
                label_visibility="collapsed",
            )
        with period_col:
            period = st.selectbox(
                "Período rápido",
                ["Tudo", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Ano atual"],
                key="selected_periodo",
                label_visibility="collapsed",
            )
        with data_col:
            with st.popover("Dados", width="stretch"):
                upload = st.file_uploader(
                    "Arquivo CSV ou XLSX",
                    type=["xlsx", "csv"],
                    help="Arquivo sujeito aos limites de segurança e às validações configuradas.",
                )
        with report_col:
            st.button(
                "Gerar relatório",
                type="primary",
                width="stretch",
                on_click=navigate_to,
                args=("Relatórios",),
            )
    return upload, period


def render_filters(df):
    filtered = df.copy()
    with st.sidebar:
        with st.popover("Filtros do recorte", width="stretch"):
            stores = sorted(filtered["Loja"].dropna().astype(str).unique())
            products = sorted(filtered["Produto"].dropna().astype(str).unique())
            selected_stores = st.multiselect("Lojas", stores, key="selected_lojas")
            selected_products = st.multiselect("Produtos", products, key="selected_produtos")
            minimum, maximum = filtered["Data"].min().date(), filtered["Data"].max().date()
            date_range = st.date_input(
                "Intervalo personalizado",
                value=(minimum, maximum),
                min_value=minimum,
                max_value=maximum,
                key="selected_date_range",
            )
            st.button(
                "Limpar filtros",
                width="stretch",
                on_click=clear_filter_state,
            )

    if selected_stores:
        filtered = filtered[filtered["Loja"].astype(str).isin(selected_stores)]
    if selected_products:
        filtered = filtered[filtered["Produto"].astype(str).isin(selected_products)]
    query = st.session_state.get("global_search", "").strip()
    if query:
        matches_store = filtered["Loja"].astype(str).str.contains(query, case=False, na=False)
        matches_product = filtered["Produto"].astype(str).str.contains(query, case=False, na=False)
        filtered = filtered[matches_store | matches_product]
    if len(date_range) == 2:
        start = pd.Timestamp(date_range[0])
        end = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
        filtered = filtered[(filtered["Data"] >= start) & (filtered["Data"] < end)]
    filtered.attrs = df.attrs.copy()
    return filtered


def render_anomaly_notice(df):
    anomalies = detect_extreme_monetary_values(df)
    if anomalies.empty:
        return anomalies
    st.warning(
        financial_anomaly_notice(len(anomalies))
    )
    return anomalies


def render_overview(df, analytics, source):
    anomalies = detect_extreme_monetary_values(df)
    anomaly_html = ""
    if not anomalies.empty:
        detail = financial_anomaly_notice(len(anomalies))
        anomaly_html = (
            f'<div class="fusion-anomaly" title="{escape_html(detail)}">'
            f'{len(anomalies)} possíveis anomalias · mantidas nos cálculos</div>'
        )
    st.markdown(
        f"""
        <div class="fusion-hero"><div><div class="fusion-greeting">Olá, {escape_html(display_name())}!</div>
        <div class="fusion-subtitle">Aqui está o panorama completo do seu negócio</div></div>
        <div class="fusion-hero-meta"><div class="source-chip">{escape_html(source)} · {len(df):,} registros</div>
        {anomaly_html}</div></div>
        """,
        unsafe_allow_html=True,
    )
    render_kpi_strip(analytics)
    st.caption(analytics["comparison"].get("label", "Sem comparação temporal disponível"))
    render_analytical_scope(analytics)
    charts = analytics["charts"]
    with st.container(key="overview-chart-grid"):
        left, right = st.columns([2.05, 1])
        with left:
            with st.container(border=True):
                scale_col, view_col = st.columns([1.35, 1])
                with scale_col:
                    log_scale = st.toggle(
                        "Escala logarítmica",
                        value=True,
                        key="overview_log_scale",
                        help="Mantém todos os valores e apenas altera a escala visual.",
                    )
                with view_col:
                    revenue_view = st.segmented_control(
                        "Visualização do faturamento",
                        ("Completa", "Faixa típica"),
                        default="Completa",
                        key="overview_revenue_view",
                        label_visibility="collapsed",
                    )
                revenue_data = charts["revenue_by_month"]
                if revenue_view == "Faixa típica" and not anomalies.empty:
                    typical_df = df.drop(index=anomalies["indice"], errors="ignore").copy()
                    revenue_data = build_revenue_by_month(typical_df, "Data", "Faturamento")
                    st.caption(
                        "Visão complementar: as anomalias permanecem nos KPIs e na visão completa, "
                        "mas são separadas somente neste gráfico para revelar a faixa típica."
                    )
                render_revenue_chart(revenue_data, log_scale=log_scale)
        with right:
            with st.container(border=True):
                render_category_donut(df)

    with st.container(key="overview-lower-grid"):
        stores_col, products_col, ai_col = st.columns([1.25, 1.35, 1])
        with stores_col:
            with st.container(border=True):
                render_store_chart(charts["revenue_by_store"], compact=True)
        with products_col:
            with st.container(border=True):
                render_products_panel(analytics)
        with ai_col:
            with st.container(border=True):
                render_ai_panel()

    render_insight_row(analytics)


def render_sales(df, analytics, source):
    render_sales_dashboard(df, analytics, source)


def render_products(df, analytics, source):
    render_products_dashboard(df, source)


def render_stores(df, analytics, source):
    render_stores_dashboard(df, source)


def render_quality(df, source, active_records):
    render_quality_dashboard(df, source, active_records=active_records)


def main():
    st.set_page_config(
        page_title="DataFlow Fusion Ultimate 2.0",
        page_icon="DF",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    init_session_state()
    st.html(preference_css(read_preferences(st.session_state)))
    st.html(sidebar_layout_css())
    page = render_sidebar()
    upload, period = render_data_controls()
    with st.spinner("Validando e preparando dados..."):
        df, source, error = carregar_dados(
            arquivo_upload=upload,
            periodo=period,
            cache=st.session_state.performance_cache,
            telemetry=st.session_state.performance_telemetry,
        )
    if error:
        st.error(error)
        st.stop()
    if df is None or df.empty:
        st.info("Nenhum registro disponível para o período selecionado.")
        st.stop()

    filtered = render_filters(df)
    if filtered.empty:
        st.info("Nenhum registro corresponde aos filtros atuais.")
        st.stop()
    analytics, _analytics_key, _ = get_cached_analytics(
        filtered,
        st.session_state.performance_cache,
        st.session_state.performance_telemetry,
        construir_analytics_state,
    )
    render_sidebar_status(len(filtered))

    routes = {
        "Visão Geral": lambda: render_overview(filtered, analytics, source),
        "Análise de Vendas": lambda: render_sales(filtered, analytics, source),
        "Produtos": lambda: render_products(filtered, analytics, source),
        "Lojas": lambda: render_stores(filtered, analytics, source),
        "Inteligência Artificial": lambda: (
            page_header("Inteligência Artificial", "Assistente governado, opcional e sem respostas simuladas.", source),
            render_ai_assistant(analytics),
        ),
        "Qualidade dos Dados": lambda: render_quality(df, source, len(filtered)),
        "Relatórios": lambda: render_reports_dashboard(df, filtered, source),
        "Configurações": lambda: render_settings_dashboard(df, source),
    }
    routes[page]()


if __name__ == "__main__":
    main()
