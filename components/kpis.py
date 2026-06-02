import streamlit as st

from services.formatter import format_currency, format_number, format_percent


def get_metric_value(analytics_state: dict, key: str, default=0):
    if not key:
        return default

    metricas = analytics_state.get("metricas", {})

    if key in analytics_state:
        return analytics_state.get(key, default)

    if key in metricas:
        return metricas.get(key, default)

    return default


def get_schema(analytics_state: dict) -> dict:
    return analytics_state.get("schema", {}) or {}


def normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def is_text_metric(title: str, value) -> bool:
    if isinstance(value, str):
        return True

    text_keywords = [
        "produto",
        "loja",
        "categoria",
        "dimensão",
        "dimensao",
        "domínio",
        "dominio",
        "top",
        "melhor",
        "principal",
        "departamento",
        "cliente",
        "projeto",
        "status",
        "segmento",
        "grupo",
        "canal",
        "responsável",
        "responsavel",
    ]

    normalized_title = normalize_text(title)
    return any(keyword in normalized_title for keyword in text_keywords)


def is_percent_metric(title: str) -> bool:
    percent_keywords = [
        "margem",
        "crescimento",
        "participação",
        "participacao",
        "percentual",
        "%",
    ]

    normalized_title = normalize_text(title)
    return any(keyword in normalized_title for keyword in percent_keywords)


def is_money_metric(title: str, schema: dict | None = None) -> bool:
    normalized_title = normalize_text(title)

    force_not_money = [
        "pedido",
        "pedidos",
        "quantidade",
        "qtd",
        "volume",
        "registro",
        "registros",
        "ativos",
        "ativo",
        "itens",
        "unidades",
        "unidade",
        "count",
        "contagem",
    ]

    if any(keyword in normalized_title for keyword in force_not_money):
        return False

    monetary_keywords = [
        "faturamento",
        "ticket",
        "receita",
        "valor",
        "total de",
        "custo",
        "despesa",
        "lucro",
        "saldo",
        "salário",
        "salario",
        "preço",
        "preco",
        "média por registro",
        "media por registro",
    ]

    return any(keyword in normalized_title for keyword in monetary_keywords)


def format_kpi_value(title: str, value, schema: dict | None = None):
    schema = schema or {}

    if is_text_metric(title, value):
        return str(value) if value not in [None, ""] else "Não informado"

    if is_percent_metric(title):
        return format_percent(value)

    if is_money_metric(title, schema):
        return format_currency(value)

    return format_number(value)


def format_growth(delta):
    try:
        delta = float(delta)
    except (TypeError, ValueError):
        delta = 0.0

    prefix = "+" if delta > 0 else ""
    return f"{prefix}{format_percent(delta)}"


def get_delta_color(delta):
    try:
        delta = float(delta)
    except (TypeError, ValueError):
        return "neutral"

    if delta > 0:
        return "positive"

    if delta < 0:
        return "negative"

    return "neutral"


def render_kpi_card(
    title: str,
    value,
    icon: str,
    badge: str = "",
    delta=None,
    featured: bool = False,
    schema: dict | None = None,
):
    card_class = "kpi-card kpi-card-featured" if featured else "kpi-card"

    badge_html = ""
    if badge:
        badge_html = f'<div class="kpi-badge">{badge}</div>'

    delta_html = ""
    if delta is not None:
        color_class = f"kpi-growth-{get_delta_color(delta)}"
        delta_html = (
            f'<div class="{color_class}">'
            f"{format_growth(delta)} em relação ao período anterior"
            f"</div>"
        )

    st.markdown(
        f"""
        <div class="{card_class}">
            <div>
                <div class="kpi-icon">{icon}</div>
                {badge_html}
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{format_kpi_value(title, value, schema)}</div>
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_domain_kpi_cards(analytics_state: dict):
    schema = get_schema(analytics_state)

    domain = schema.get("domain", "generico")
    metric_column = schema.get("metric_column") or "Métrica Principal"
    primary_dimension = schema.get("primary_dimension") or "Dimensão Principal"
    secondary_dimension = schema.get("secondary_dimension") or "Dimensão Secundária"

    domain_badges = {
        "vendas": "Receita",
        "financeiro": "Financeiro",
        "rh": "RH",
        "estoque": "Estoque",
        "crm": "CRM",
        "projetos": "Projetos",
        "generico": "Universal",
    }

    return [
        {
            "icon": "💰" if domain in ["vendas", "financeiro"] else "📊",
            "title": f"Total de {metric_column}",
            "metric_key": "faturamento_total",
            "growth_key": "crescimento_faturamento",
            "badge": domain_badges.get(domain, "Métrica"),
            "featured": True,
        },
        {
            "icon": "🎯",
            "title": "Média por Registro",
            "metric_key": "ticket_medio",
            "growth_key": "crescimento_ticket",
            "badge": "Eficiência",
            "featured": True,
        },
        {
            "icon": "📄",
            "title": "Registros Analisados",
            "metric_key": "total_pedidos",
            "growth_key": "crescimento_pedidos",
            "badge": "Base",
            "featured": True,
        },
        {
            "icon": "🧮",
            "title": "Quantidade Total",
            "metric_key": "quantidade_total",
            "growth_key": "crescimento_quantidade",
            "badge": "Volume",
            "featured": False,
        },
        {
            "icon": "🧭",
            "title": f"Qtd. {primary_dimension}",
            "metric_key": "primary_dimension_count",
            "growth_key": "crescimento_primary_dimension",
            "badge": "Dimensão",
            "featured": False,
        },
        {
            "icon": "🏆",
            "title": f"Top {secondary_dimension}",
            "metric_key": "top_secondary_dimension",
            "growth_key": None,
            "badge": "Ranking",
            "featured": False,
        },
        {
            "icon": "🥇",
            "title": f"Top {primary_dimension}",
            "metric_key": "top_primary_dimension",
            "growth_key": None,
            "badge": "Destaque",
            "featured": False,
        },
        {
            "icon": "🧠",
            "title": "Domínio Detectado",
            "metric_key": "domain",
            "growth_key": None,
            "badge": "Schema",
            "featured": False,
        },
    ]


def render_kpis(analytics_state: dict):
    schema = get_schema(analytics_state)
    cards = analytics_state.get("kpi_cards") or get_domain_kpi_cards(analytics_state)

    st.markdown(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Indicadores Inteligentes</div>
                <div class="section-subtitle">KPIs adaptados automaticamente ao tipo de planilha carregada</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    first_row = cards[:4]
    second_row = cards[4:8]

    cols = st.columns(4)

    for col, card in zip(cols, first_row):
        with col:
            value = get_metric_value(analytics_state, card.get("metric_key"))
            delta = (
                get_metric_value(analytics_state, card.get("growth_key"))
                if card.get("growth_key")
                else None
            )

            render_kpi_card(
                title=card.get("title", "Indicador"),
                value=value,
                icon=card.get("icon", "📊"),
                badge=card.get("badge", ""),
                delta=delta,
                featured=card.get("featured", False),
                schema=schema,
            )

    if second_row:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        cols = st.columns(4)

        for col, card in zip(cols, second_row):
            with col:
                value = get_metric_value(analytics_state, card.get("metric_key"))
                delta = (
                    get_metric_value(analytics_state, card.get("growth_key"))
                    if card.get("growth_key")
                    else None
                )

                render_kpi_card(
                    title=card.get("title", "Indicador"),
                    value=value,
                    icon=card.get("icon", "📊"),
                    badge=card.get("badge", ""),
                    delta=delta,
                    featured=card.get("featured", False),
                    schema=schema,
                )