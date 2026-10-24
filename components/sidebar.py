from __future__ import annotations

import unicodedata
from dataclasses import dataclass

import streamlit as st

from services.llm_router import get_llm_router

PRODUCT_VERSION = "2.0"


@dataclass(frozen=True)
class NavigationItem:
    page: str
    description: str
    icon: str
    key: str
    terms: tuple[str, ...] = ()


NAVIGATION_GROUPS: tuple[tuple[str, str, tuple[NavigationItem, ...]], ...] = (
    ("PAINEL PRINCIPAL", "cyan", (
        NavigationItem("Visão Geral", "Panorama completo do negócio", ":material/dashboard:", "overview", ("dashboard", "kpi", "indicadores")),
        NavigationItem("Análise de Vendas", "Desempenho e tendências", ":material/monitoring:", "sales", ("vendas", "receita", "faturamento", "tendencias")),
        NavigationItem("Produtos", "Portfólio e performance", ":material/deployed_code:", "products", ("produto", "portfolio", "ranking")),
        NavigationItem("Lojas", "Desempenho das unidades", ":material/storefront:", "stores", ("loja", "unidade", "rede")),
    )),
    ("INTELIGÊNCIA", "violet", (
        NavigationItem("Inteligência Artificial", "Análises e insights avançados", ":material/psychology:", "ai", ("ia", "assistente", "insights")),
        NavigationItem("Qualidade dos Dados", "Diagnóstico e confiabilidade", ":material/verified_user:", "quality", ("auditoria", "qualidade", "governanca", "confiabilidade")),
    )),
    ("RELATÓRIOS", "cyan", (
        NavigationItem("Relatórios", "Exportações e relatórios analíticos", ":material/analytics:", "reports", ("pdf", "excel", "csv", "exportacao")),
    )),
    ("SISTEMA", "ice", (
        NavigationItem("Configurações", "Preferências e administração", ":material/settings:", "settings", ("configuracao", "preferencias", "administracao")),
    )),
)

PAGES = tuple(item.page for _, _, items in NAVIGATION_GROUPS for item in items)
PAGE_ITEMS = {item.page: item for _, _, items in NAVIGATION_GROUPS for item in items}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return " ".join(normalized.casefold().split())


def search_navigation(query: str) -> tuple[str, ...]:
    needle = _normalize(query)
    if not needle:
        return PAGES
    matches = []
    for page in PAGES:
        item = PAGE_ITEMS[page]
        haystack = _normalize(" ".join((item.page, item.description, *item.terms)))
        if needle in haystack:
            matches.append(page)
    return tuple(matches)


def set_active_page(page: str) -> None:
    if page not in PAGES:
        raise ValueError("Página de navegação inválida.")
    st.session_state.active_page = page


def sidebar_layout_css() -> str:
    """Size the open native sidebar without creating a second collapse state."""
    return """<style>
    [data-testid="stSidebar"][aria-expanded="true"] {
      width:318px!important;
      min-width:318px!important;
      max-width:318px!important;
    }
    [data-testid="stSidebar"]>div:first-child {
      width:100%!important;
      min-width:0!important;
      max-width:100%!important;
    }
    [data-testid="stSidebarCollapseButton"] {
      visibility:visible!important;
    }
    </style>"""


def _navigation_label(item: NavigationItem) -> str:
    return f"{item.page}\n{item.description}"


def _render_brand() -> None:
    st.html("""
    <div class="sidebar-space-brand">
      <div class="sidebar-stars" aria-hidden="true"></div><div class="sidebar-planet" aria-hidden="true"></div>
      <div class="sidebar-brand-row"><div class="sidebar-df" aria-label="Logotipo DataFlow">DF</div>
      <div class="sidebar-brand-copy"><strong>Fusão de<br>Fluxo de Dados</strong><span>ULTIMATE 2.0</span></div></div>
    </div>""")


def render_sidebar():
    with st.sidebar:
        st.radio("Navegação principal", PAGES, key="active_page", label_visibility="collapsed")
        _render_brand()
        st.html('<div class="sidebar-search-wrap"><span>Busca de navegação</span></div>')
        query = st.text_input("Buscar no menu", key="sidebar_menu_search", placeholder="Buscar no menu...", label_visibility="collapsed", icon=":material/search:")
        matches = set(search_navigation(query))
        rendered = 0
        for group, color, items in NAVIGATION_GROUPS:
            visible = [item for item in items if item.page in matches]
            if not visible:
                continue
            st.html(f'<div class="sidebar-group {color}"><span>{group}</span><i></i></div>')
            for item in visible:
                active = st.session_state.get("active_page") == item.page
                st.button(_navigation_label(item), icon=item.icon, key=f"nav_{item.key}", help=f"{item.page}: {item.description}", on_click=set_active_page, args=(item.page,), width="stretch", type="primary" if active else "secondary")
                rendered += 1
        if not rendered:
            st.html('<div class="sidebar-empty"><strong>Nenhuma página encontrada</strong><span>Tente vendas, produto, auditoria, PDF ou IA.</span></div>')
    return st.session_state.active_page


def _timing(measurement):
    cache = " · cache" if measurement.get("cache_hit") else ""
    return f"{measurement.get('duration_ms', 0):.1f} ms{cache}"


def render_sidebar_status(rows):
    with st.sidebar:
        telemetry = st.session_state.get("performance_telemetry")
        latest = getattr(telemetry, "latest", {})
        st.html('<div class="sidebar-status-rule"></div>')
        st.caption("ESTADO VERIFICADO")
        st.markdown(f'<div class="verified-data"><span>Base ativa</span><strong>{rows:,} registros</strong></div>', unsafe_allow_html=True)
        for label, measurement in (("Carga", latest.get("carregamento")), ("Análise", latest.get("agregacao")), ("Exportação", latest.get("exportacao"))):
            if measurement:
                st.markdown(f'<div class="verified-row"><span>{label}</span><strong>{_timing(measurement)}</strong></div>', unsafe_allow_html=True)
        router = get_llm_router(
            api_key=st.session_state.get("groq_api_key", ""),
            rate_limiter=st.session_state.get("ai_rate_limiter"),
        )
        ai_enabled = bool(st.session_state.get("ai_enabled", False))
        ai_state = "IA opcional não configurada" if not router.is_configured() else ("IA desativada" if not ai_enabled else "IA sujeita a consentimento")
        st.html(f"""<div class="sidebar-system-card"><b aria-hidden="true"></b>
        <div class="sidebar-status-copy"><strong>Aplicação ativa</strong><span>DataFlow Fusion Ultimate 2.0</span><small>{ai_state}</small></div><em>{PRODUCT_VERSION}</em></div>""")
        if not router.is_configured():
            st.info("Dashboard operacional sem IA; provedor não configurado.")
