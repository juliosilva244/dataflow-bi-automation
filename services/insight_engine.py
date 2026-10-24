from __future__ import annotations

from typing import Any

from domain.periods import split_equivalent_periods
from services.ai_evidence import describe_change
from services.metrics_engine import exact_decimal_sum
from services.security import escape_html
from services.settings import get_insight_settings


def gerar_insights_executivos(metricas: dict[str, Any]) -> list[dict[str, str]]:
    settings = get_insight_settings()
    insights: list[dict[str, str]] = []

    participacao_produto_top = float(metricas.get("participacao_produto_top", 0))
    desempenho_pior_loja = float(metricas.get("desempenho_pior_loja", 100))
    crescimento_faturamento = float(metricas.get("crescimento_faturamento", 0))
    crescimento_ticket = float(metricas.get("crescimento_ticket", 0))
    ticket_medio = float(metricas.get("ticket_medio", 0))

    produto_top = escape_html(metricas.get("produto_top", "Não informado"))
    pior_loja = escape_html(metricas.get("pior_loja", "Não informado"))

    if participacao_produto_top >= settings.product_share_critical:
        insights.append(
            {
                "icon": "🚨",
                "title": "Alta concentração de receita",
                "text": (
                    f"O produto <b>{produto_top}</b> concentra "
                    f"<b>{participacao_produto_top:.1f}%</b> do faturamento. "
                    "Fato: concentração de receita. Hipótese: exposição à queda desse item; "
                    "não comprova causa, falha operacional ou perda futura."
                ),
                "badge": "Risco",
            }
        )
    elif participacao_produto_top >= settings.product_share_warning:
        insights.append(
            {
                "icon": "⚠️",
                "title": "Concentração moderada",
                "text": (
                    f"O produto <b>{produto_top}</b> representa "
                    f"<b>{participacao_produto_top:.1f}%</b> da receita. "
                    "Esse percentual não comprova saúde operacional nem a causa da concentração."
                ),
                "badge": "Atenção",
            }
        )
    else:
        insights.append(
            {
                "icon": "✅",
                "title": "Participação do produto líder",
                "text": (
                    f"O principal produto representa "
                    f"<b>{participacao_produto_top:.1f}%</b> do faturamento. "
                    "A participação isolada não comprova equilíbrio ou saúde operacional."
                ),
                "badge": "Observação",
            }
        )

    if desempenho_pior_loja < settings.store_performance_critical:
        insights.append(
            {
                "icon": "🚨",
                "title": "Menor receita relativa por loja",
                "text": (
                    f"A receita da loja <b>{pior_loja}</b> corresponde a "
                    f"<b>{desempenho_pior_loja:.1f}%</b> da média de receita por loja. "
                    "A base disponível não demonstra a causa; é necessária análise adicional."
                ),
                "badge": "Alerta de receita",
            }
        )
    elif desempenho_pior_loja < settings.store_performance_warning:
        insights.append(
            {
                "icon": "⚠️",
                "title": "Loja abaixo da média",
                "text": (
                    f"A receita da loja <b>{pior_loja}</b> corresponde a "
                    f"<b>{desempenho_pior_loja:.1f}%</b> da média de receita por loja. "
                    "A base disponível não demonstra a causa da diferença."
                ),
                "badge": "Risco",
            }
        )
    else:
        insights.append(
            {
                "icon": "🏬",
                "title": "Receita relativa das lojas",
                "text": (
                    f"A menor receita por loja corresponde a {desempenho_pior_loja:.1f}% "
                    "da média de receita por loja. Não comprova estabilidade operacional."
                ),
                "badge": "Observação",
            }
        )

    if not metricas.get("base_comparativa_disponivel", False):
        insights.append({"icon": "➖", "title": "Comparação indisponível", "text": "Não há dois períodos equivalentes comprovados; não concluir receita estável ou crescimento de 0%.", "badge": "Sem base"})
    elif crescimento_faturamento > settings.revenue_growth_positive:
        insights.append(
            {
                "icon": "📈",
                "title": "Aceleração de receita",
                "text": (
                    f"O faturamento avançou <b>{crescimento_faturamento:.1f}%</b> "
                    "na comparação entre períodos equivalentes. A base não demonstra a causa."
                ),
                "badge": "Crescimento",
            }
        )
    elif crescimento_faturamento < settings.revenue_growth_negative:
        description = f"O faturamento caiu {abs(crescimento_faturamento):.1f}% (arredondado)."
        frame = metricas.get("prepared_df")
        if frame is not None and "Data" in frame and "Faturamento" in frame:
            current, previous, period = split_equivalent_periods(frame, "Data")
            description = period.label + ". " + describe_change(exact_decimal_sum(current["Faturamento"]), exact_decimal_sum(previous["Faturamento"]), period.available)
        elif crescimento_faturamento <= -99.995:
            description = "Queda arredondada próxima de 100%; conferir valores e períodos antes de concluir receita zerada."
        insights.append(
            {
                "icon": "📉",
                "title": "Queda relevante de receita",
                "text": (
                    f"{description} "
                    "A base não contém evidência suficiente para atribuir uma causa."
                ),
                "badge": "Queda",
            }
        )
    else:
        insights.append(
            {
                "icon": "➖",
                "title": "Variação dentro da faixa configurada",
                "text": (
                    f"A variação de faturamento foi de <b>{crescimento_faturamento:.1f}%</b>. "
                    "Isso não comprova estabilidade operacional."
                ),
                "badge": "Estável",
            }
        )

    if ticket_medio < settings.ticket_reference_minimum:
        insights.append(
            {
                "icon": "💎",
                "title": "Ticket médio baixo",
                "text": (
                    f"O ticket médio está abaixo da referência configurada de "
                    f"R$ {settings.ticket_reference_minimum:,.2f}. "
                    "A base não permite concluir a causa dessa diferença."
                ),
                "badge": "Oportunidade",
            }
        )
    elif metricas.get("base_comparativa_disponivel", False) and crescimento_ticket > settings.ticket_growth_positive:
        insights.append(
            {
                "icon": "💎",
                "title": "Ticket médio em expansão",
                "text": (
                    f"O ticket médio cresceu <b>{crescimento_ticket:.1f}%</b>. "
                    "A variação é observável, mas sua causa não está demonstrada na base."
                ),
                "badge": "Eficiência",
            }
        )
    else:
        insights.append(
            {
                "icon": "💎",
                "title": "Ticket médio do recorte",
                "text": (
                    "Não há evidência suficiente para recomendar ofertas ou concluir eficiência operacional. "
                    "Conferir receita e denominador de pedidos do mesmo recorte."
                ),
                "badge": "Observação",
            }
        )

    return insights
