import os

from dotenv import load_dotenv

from services.providers.groq_provider import GroqProvider


load_dotenv()


class LLMRouter:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.provider = "groq" if self.groq_api_key else None

    def build_system_prompt(self):
        return """
Você é o AI BI Assistant do DataFlow BI Automation.

Você atua como:
- analista executivo de BI;
- copiloto corporativo;
- consultor analítico empresarial.

OBJETIVO:
Realizar análises executivas usando SOMENTE os KPIs fornecidos.

REGRAS CRÍTICAS:

1. Nunca invente:
- concorrência;
- comportamento de clientes;
- marketing;
- logística;
- economia;
- mercado;
- causas externas.

2. Nunca afirme causalidade sem evidência.

3. Toda análise deve seguir:

OBSERVAÇÃO →
IMPACTO →
LIMITAÇÃO DA EVIDÊNCIA

4. Quando existir risco:
explique APENAS impactos possíveis.

5. Sempre diferencie:
- fatos observáveis;
- inferências;
- hipóteses.

6. Se não houver evidência:
diga explicitamente:
"não há dados suficientes para afirmar isso."

7. Respostas devem ser:
- objetivas;
- analíticas;
- estratégicas;
- executivas.

8. Evite linguagem genérica de chatbot.

9. Nunca use frases motivacionais.

10. Nunca invente dados não presentes.

11. Priorize:
- faturamento;
- ticket médio;
- tendências;
- lojas;
- produtos;
- performance operacional.

12. Sempre baseie respostas nos KPIs.
"""

    def build_executive_briefing(
        self,
        analytics_state,
    ):
        faturamento_total = analytics_state.get(
            "faturamento_total",
            0,
        )

        ticket_medio = analytics_state.get(
            "ticket_medio",
            0,
        )

        total_pedidos = analytics_state.get(
            "total_pedidos",
            0,
        )

        lojas_ativas = analytics_state.get(
            "lojas_ativas",
            0,
        )

        crescimento_faturamento = analytics_state.get(
            "crescimento_faturamento",
            0,
        )

        crescimento_ticket = analytics_state.get(
            "crescimento_ticket",
            0,
        )

        melhor_loja = analytics_state.get(
            "melhor_loja",
            "Não informado",
        )

        pior_loja = analytics_state.get(
            "pior_loja",
            "Não informado",
        )

        produto_top = analytics_state.get(
            "produto_top",
            "Não informado",
        )

        participacao_produto_top = analytics_state.get(
            "participacao_produto_top",
            0,
        )

        risks = []

        if crescimento_faturamento < 0:
            risks.append(
                f"queda de faturamento de {crescimento_faturamento:.1f}%"
            )

        if crescimento_ticket < 0:
            risks.append(
                f"queda de ticket médio de {crescimento_ticket:.1f}%"
            )

        if participacao_produto_top > 40:
            risks.append(
                "alta concentração de receita"
            )

        if not risks:
            risks.append(
                "nenhum risco operacional crítico detectado"
            )

        briefing = f"""
RELATÓRIO EXECUTIVO DATAFLOW BI

INDICADORES:
- faturamento total: R$ {faturamento_total:,.2f}
- ticket médio: R$ {ticket_medio:,.2f}
- pedidos totais: {total_pedidos}
- lojas ativas: {lojas_ativas}

TENDÊNCIAS:
- crescimento faturamento: {crescimento_faturamento:.2f}%
- crescimento ticket médio: {crescimento_ticket:.2f}%

PERFORMANCE:
- melhor loja: {melhor_loja}
- pior loja relativa: {pior_loja}

PRODUTO:
- produto líder: {produto_top}
- concentração produto líder: {participacao_produto_top:.1f}%

RISCOS:
- {"; ".join(risks)}

IMPORTANTE:
Use apenas os dados acima.
"""

        return briefing

    def clean_history(self, history):
        if not history:
            return []

        cleaned = []

        for message in history[-6:]:
            cleaned.append(
                {
                    "role": message.get(
                        "role",
                        "user",
                    ),
                    "content": str(
                        message.get(
                            "content",
                            "",
                        )
                    ),
                }
            )

        return cleaned

    def build_messages(
        self,
        question,
        analytics_state,
        history=None,
    ):
        briefing = self.build_executive_briefing(
            analytics_state
        )

        messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(),
            },
            {
                "role": "user",
                "content": briefing,
            },
        ]

        messages.extend(
            self.clean_history(history)
        )

        messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        return messages

    def generate_response(
        self,
        question,
        analytics_state,
        history=None,
    ):
        if not self.groq_api_key:
            return "Assistente de IA não configurado. Por favor, forneça a GROQ_API_KEY no arquivo .env para ativar."
        provider = GroqProvider()

        messages = self.build_messages(
            question,
            analytics_state,
            history,
        )

        return provider.generate(
            messages
        )


def get_llm_router():
    return LLMRouter()