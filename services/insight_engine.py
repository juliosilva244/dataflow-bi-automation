from __future__ import annotations

from typing import Any


def gerar_insights_executivos(metricas: dict[str, Any]) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []

    participacao_produto_top = float(metricas.get("participacao_produto_top", 0))
    desempenho_pior_loja = float(metricas.get("desempenho_pior_loja", 100))
    crescimento_faturamento = float(metricas.get("crescimento_faturamento", 0))
    crescimento_ticket = float(metricas.get("crescimento_ticket", 0))
    ticket_medio = float(metricas.get("ticket_medio", 0))

    produto_top = metricas.get("produto_top", "Não informado")
    pior_loja = metricas.get("pior_loja", "Não informado")

    if participacao_produto_top >= 45:
        insights.append(
            {
                "icon": "🚨",
                "title": "Alta concentração de receita",
                "text": (
                    f"O produto <b>{produto_top}</b> concentra "
                    f"<b>{participacao_produto_top:.1f}%</b> do faturamento. "
                    "Isso cria risco comercial caso a demanda desse item caia."
                ),
                "badge": "Risco",
            }
        )
    elif participacao_produto_top >= 30:
        insights.append(
            {
                "icon": "⚠️",
                "title": "Concentração moderada",
                "text": (
                    f"O produto <b>{produto_top}</b> representa "
                    f"<b>{participacao_produto_top:.1f}%</b> da receita. "
                    "A operação ainda é saudável, mas merece acompanhamento."
                ),
                "badge": "Atenção",
            }
        )
    else:
        insights.append(
            {
                "icon": "✅",
                "title": "Receita bem distribuída",
                "text": (
                    f"O principal produto representa apenas "
                    f"<b>{participacao_produto_top:.1f}%</b> do faturamento. "
                    "Isso reduz dependência de um único item."
                ),
                "badge": "Saudável",
            }
        )

    if desempenho_pior_loja < 60:
        insights.append(
            {
                "icon": "🚨",
                "title": "Loja em zona crítica",
                "text": (
                    f"A loja <b>{pior_loja}</b> está muito abaixo da média operacional. "
                    "Priorize diagnóstico de mix, tráfego, equipe e ruptura de estoque."
                ),
                "badge": "Crítico",
            }
        )
    elif desempenho_pior_loja < 80:
        insights.append(
            {
                "icon": "⚠️",
                "title": "Loja abaixo da média",
                "text": (
                    f"A loja <b>{pior_loja}</b> apresenta desempenho inferior ao padrão. "
                    "Há oportunidade clara de correção operacional."
                ),
                "badge": "Risco",
            }
        )
    else:
        insights.append(
            {
                "icon": "🏬",
                "title": "Operação equilibrada",
                "text": (
                    "As lojas apresentam distribuição operacional relativamente estável "
                    "no período analisado."
                ),
                "badge": "Estável",
            }
        )

    if crescimento_faturamento > 15:
        insights.append(
            {
                "icon": "📈",
                "title": "Aceleração de receita",
                "text": (
                    f"O faturamento avançou <b>{crescimento_faturamento:.1f}%</b> "
                    "na leitura comparativa interna do período. Bom sinal de tração."
                ),
                "badge": "Crescimento",
            }
        )
    elif crescimento_faturamento < -10:
        insights.append(
            {
                "icon": "📉",
                "title": "Queda relevante de receita",
                "text": (
                    f"O faturamento caiu <b>{abs(crescimento_faturamento):.1f}%</b>. "
                    "Investigue sazonalidade, campanhas, ruptura e queda de conversão."
                ),
                "badge": "Queda",
            }
        )
    else:
        insights.append(
            {
                "icon": "➖",
                "title": "Receita estável",
                "text": (
                    f"A variação de faturamento foi de <b>{crescimento_faturamento:.1f}%</b>. "
                    "O negócio está sem grande aceleração no recorte atual."
                ),
                "badge": "Estável",
            }
        )

    if ticket_medio < 100:
        insights.append(
            {
                "icon": "💎",
                "title": "Ticket médio baixo",
                "text": (
                    "O ticket médio está abaixo de R$ 100. "
                    "Teste bundles, upsell, combos e política de frete mínimo."
                ),
                "badge": "Oportunidade",
            }
        )
    elif crescimento_ticket > 8:
        insights.append(
            {
                "icon": "💎",
                "title": "Ticket médio em expansão",
                "text": (
                    f"O ticket médio cresceu <b>{crescimento_ticket:.1f}%</b>. "
                    "Isso sugere melhora de monetização por pedido."
                ),
                "badge": "Eficiência",
            }
        )
    else:
        insights.append(
            {
                "icon": "💎",
                "title": "Monetização controlada",
                "text": (
                    "O ticket médio está em patamar funcional. "
                    "Ainda há espaço para elevar valor por pedido com ofertas inteligentes."
                ),
                "badge": "Eficiência",
            }
        )

    return insights