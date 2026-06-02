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


def get_growth_label(value: float) -> tuple[str, str]:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    if value > 5:
        return "crescimento forte", "positive"

    if value > 0:
        return "crescimento moderado", "positive"

    if value < -5:
        return "queda relevante", "negative"

    if value < 0:
        return "leve retração", "negative"

    return "estabilidade", "neutral"


def render_insight_card(icon: str, badge: str, title: str, text: str):
    st.markdown(
        f"""
        <div class="smart-insight-card">
            <div class="smart-insight-icon">{icon}</div>
            <div>
                <div class="smart-insight-badge">{badge}</div>
                <div class="smart-insight-title">{title}</div>
                <div class="insight-text">{text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_domain_name(domain: str) -> str:
    labels = {
        "vendas": "Vendas",
        "financeiro": "Financeiro",
        "rh": "Recursos Humanos",
        "estoque": "Estoque",
        "crm": "CRM",
        "projetos": "Projetos",
        "generico": "Análise Geral",
        "vazio": "Base Vazia",
    }

    return labels.get(domain, "Análise Geral")


def get_domain_context(domain: str) -> dict:
    contexts = {
        "vendas": {
            "main_badge": "Vendas",
            "main_title": "Receita consolidada",
            "main_text": "O painel identificou uma base com comportamento comercial ou de vendas.",
            "top_primary_title": "Dimensão principal em destaque",
            "top_secondary_title": "Dimensão secundária em destaque",
            "opportunity": "A principal oportunidade é cruzar os itens de maior valor com as dimensões de melhor desempenho para ampliar escala.",
        },
        "financeiro": {
            "main_badge": "Financeiro",
            "main_title": "Valor financeiro consolidado",
            "main_text": "O painel identificou uma base com características financeiras, custos, receitas ou valores transacionais.",
            "top_primary_title": "Centro de impacto principal",
            "top_secondary_title": "Conta ou grupo dominante",
            "opportunity": "A principal oportunidade é investigar concentração de valores e identificar centros de custo ou contas que exigem maior controle.",
        },
        "rh": {
            "main_badge": "RH",
            "main_title": "Métrica consolidada de pessoas",
            "main_text": "O painel identificou uma base relacionada a pessoas, cargos, departamentos ou folha.",
            "top_primary_title": "Grupo de maior impacto",
            "top_secondary_title": "Subgrupo de maior relevância",
            "opportunity": "A principal oportunidade é comparar grupos para localizar concentração de custo, volume ou desempenho.",
        },
        "estoque": {
            "main_badge": "Estoque",
            "main_title": "Volume consolidado de estoque",
            "main_text": "O painel identificou uma base relacionada a produtos, quantidades, entradas, saídas ou armazenagem.",
            "top_primary_title": "Grupo de maior volume",
            "top_secondary_title": "Item mais relevante",
            "opportunity": "A principal oportunidade é priorizar os itens de maior concentração e investigar possíveis excessos, rupturas ou sazonalidades.",
        },
        "crm": {
            "main_badge": "CRM",
            "main_title": "Base comercial consolidada",
            "main_text": "O painel identificou uma base relacionada a clientes, leads, oportunidades ou pipeline.",
            "top_primary_title": "Segmento de maior impacto",
            "top_secondary_title": "Conta ou oportunidade relevante",
            "opportunity": "A principal oportunidade é cruzar os segmentos mais relevantes com oportunidades de maior valor para priorizar ações comerciais.",
        },
        "projetos": {
            "main_badge": "Projetos",
            "main_title": "Métrica consolidada de projetos",
            "main_text": "O painel identificou uma base relacionada a projetos, tarefas, responsáveis, status ou prazos.",
            "top_primary_title": "Grupo de maior esforço",
            "top_secondary_title": "Projeto ou status relevante",
            "opportunity": "A principal oportunidade é priorizar os grupos com maior esforço, custo ou volume e investigar gargalos operacionais.",
        },
        "generico": {
            "main_badge": "Universal",
            "main_title": "Métrica principal consolidada",
            "main_text": "O painel analisou automaticamente a estrutura da planilha e detectou uma métrica principal para consolidação.",
            "top_primary_title": "Dimensão principal",
            "top_secondary_title": "Dimensão secundária",
            "opportunity": "A principal oportunidade é explorar as dimensões mais representativas para entender concentração, tendência e outliers.",
        },
    }

    return contexts.get(domain, contexts["generico"])


def render_schema_insight(analytics_state: dict):
    schema = get_schema(analytics_state)

    domain = schema.get("domain", "generico")
    confidence = schema.get("confidence", 0)
    metric_column = schema.get("metric_column") or "não identificada"
    date_column = schema.get("date_column") or "não identificada"
    primary_dimension = schema.get("primary_dimension") or "não identificada"
    secondary_dimension = schema.get("secondary_dimension") or "não identificada"

    render_insight_card(
        icon="🧠",
        badge="Schema",
        title="Leitura automática da planilha",
        text=(
            f"O DataFlow detectou o domínio "
            f"<span class='insight-highlight'>{format_domain_name(domain)}</span> "
            f"com confiança de "
            f"<span class='insight-highlight'>{format_percent(confidence * 100)}</span>. "
            f"Métrica principal: <span class='insight-highlight'>{metric_column}</span>. "
            f"Dimensão principal: <span class='insight-highlight'>{primary_dimension}</span>. "
            f"Dimensão secundária: <span class='insight-highlight'>{secondary_dimension}</span>. "
            f"Coluna temporal: <span class='insight-highlight'>{date_column}</span>."
        ),
    )


def render_insights(analytics_state: dict):
    schema = get_schema(analytics_state)

    domain = schema.get("domain", "generico")
    context = get_domain_context(domain)

    metric_column = schema.get("metric_column") or "métrica principal"
    primary_dimension = schema.get("primary_dimension") or "dimensão principal"
    secondary_dimension = schema.get("secondary_dimension") or "dimensão secundária"

    total_metric = get_metric_value(analytics_state, "faturamento_total", 0)
    average_metric = get_metric_value(analytics_state, "ticket_medio", 0)
    total_records = get_metric_value(analytics_state, "total_pedidos", 0)
    quantity_total = get_metric_value(analytics_state, "quantidade_total", 0)

    growth_metric = get_metric_value(analytics_state, "crescimento_faturamento", 0)
    growth_average = get_metric_value(analytics_state, "crescimento_ticket", 0)

    top_primary = get_metric_value(analytics_state, "top_primary_dimension", "Não informado")
    top_primary_value = get_metric_value(analytics_state, "top_primary_dimension_value", 0)

    top_secondary = get_metric_value(analytics_state, "top_secondary_dimension", "Não informado")
    top_secondary_value = get_metric_value(analytics_state, "top_secondary_dimension_value", 0)
    top_secondary_share = get_metric_value(
        analytics_state,
        "top_secondary_dimension_share",
        0,
    )

    bottom_dimension = get_metric_value(
        analytics_state,
        "bottom_primary_dimension",
        "Não informado",
    )
    bottom_performance = get_metric_value(
        analytics_state,
        "bottom_primary_dimension_performance",
        0,
    )

    growth_label, _ = get_growth_label(growth_metric)

    st.markdown(
        """
        <div class="section-header">
            <div>
                <div class="section-title">Insights Inteligentes</div>
                <div class="section-subtitle">Análise automática adaptada ao domínio da planilha</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        render_insight_card(
            icon="📊",
            badge=context["main_badge"],
            title=context["main_title"],
            text=(
                f"{context['main_text']} "
                f"O total consolidado de "
                f"<span class='insight-highlight'>{metric_column}</span> é "
                f"<span class='insight-highlight'>{format_currency(total_metric)}</span>. "
                f"A média por registro está em "
                f"<span class='insight-highlight'>{format_currency(average_metric)}</span>, "
                f"considerando <span class='insight-highlight'>{format_number(total_records)}</span> "
                f"registro(s) analisado(s)."
            ),
        )

        render_insight_card(
            icon="🥇",
            badge="Ranking",
            title=context["top_primary_title"],
            text=(
                f"A principal dimensão detectada foi "
                f"<span class='insight-highlight'>{primary_dimension}</span>. "
                f"O maior destaque é "
                f"<span class='insight-highlight'>{top_primary}</span>, "
                f"com valor consolidado de "
                f"<span class='insight-highlight'>{format_currency(top_primary_value)}</span>."
            ),
        )

    with col2:
        render_insight_card(
            icon="🏆",
            badge="Destaque",
            title=context["top_secondary_title"],
            text=(
                f"A dimensão secundária detectada foi "
                f"<span class='insight-highlight'>{secondary_dimension}</span>. "
                f"O item de maior impacto é "
                f"<span class='insight-highlight'>{top_secondary}</span>, "
                f"representando "
                f"<span class='insight-highlight'>{format_currency(top_secondary_value)}</span>. "
                f"Participação estimada no total: "
                f"<span class='insight-highlight'>{format_percent(top_secondary_share)}</span>."
            ),
        )

        render_insight_card(
            icon="📈",
            badge="Tendência",
            title="Movimento do período",
            text=(
                f"A comparação entre períodos indica "
                f"<span class='insight-highlight'>{growth_label}</span> "
                f"na métrica principal, com variação de "
                f"<span class='insight-highlight'>{format_percent(growth_metric)}</span>. "
                f"A média por registro variou "
                f"<span class='insight-highlight'>{format_percent(growth_average)}</span>."
            ),
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if bottom_dimension != "Não informado" and bottom_performance < 80:
        render_insight_card(
            icon="⚠️",
            badge="Alerta",
            title="Dimensão abaixo da média",
            text=(
                f"O grupo <span class='insight-highlight'>{bottom_dimension}</span> "
                f"está performando em aproximadamente "
                f"<span class='insight-highlight'>{format_percent(bottom_performance)}</span> "
                f"da média das dimensões analisadas. Vale investigar concentração, volume, sazonalidade "
                f"ou inconsistência de dados."
            ),
        )
    else:
        render_insight_card(
            icon="🚀",
            badge="Oportunidade",
            title="Próxima alavanca de análise",
            text=(
                f"Com <span class='insight-highlight'>{format_number(quantity_total)}</span> "
                f"unidade(s)/registro(s) de volume, {context['opportunity']}"
            ),
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    render_schema_insight(analytics_state)