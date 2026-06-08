from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class LLMRouter:
    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.provider = "groq" if self.groq_api_key else None

    def build_system_prompt(self) -> str:
        return """
Você é o AI BI Assistant do DataFlow BI Automation.

Atue como analista executivo de BI. Use SOMENTE os dados fornecidos no briefing analítico.

Regras obrigatórias:
1. Não invente causas, mercado, concorrência, logística, marketing ou comportamento de cliente.
2. Separe fatos observáveis, inferências e hipóteses.
3. Quando não houver evidência, diga: "não há dados suficientes para afirmar isso".
4. Responda em formato executivo: Observação → Impacto → Próxima ação.
5. Seja direto, estratégico e sem frases motivacionais.
6. Adapte os nomes das métricas e dimensões ao schema detectado.
""".strip()

    def build_executive_briefing(self, analytics_state: dict[str, Any]) -> str:
        schema = analytics_state.get("schema", {}) or {}
        quality = analytics_state.get("quality", {}) or {}

        metric_label = schema.get("metric_column") or "Métrica principal"
        primary_label = schema.get("primary_dimension") or "Dimensão principal"
        secondary_label = schema.get("secondary_dimension") or "Dimensão secundária"
        domain = schema.get("domain", "generico")

        charts = analytics_state.get("charts", {}) or {}
        primary_summary = charts.get("primary_dimension_summary")
        secondary_summary = charts.get("secondary_dimension_summary")

        def safe_records(df, limit=8):
            try:
                if df is None or df.empty:
                    return []
                return df.head(limit).to_dict(orient="records")
            except Exception:
                return []

        risks = []
        if analytics_state.get("crescimento_faturamento", 0) < 0:
            risks.append(f"queda de {metric_label}: {analytics_state.get('crescimento_faturamento', 0):.1f}%")
        if analytics_state.get("crescimento_ticket", 0) < 0:
            risks.append(f"queda da média por registro: {analytics_state.get('crescimento_ticket', 0):.1f}%")
        if analytics_state.get("top_secondary_dimension_share", 0) > 40:
            risks.append(f"alta concentração em {secondary_label}: {analytics_state.get('top_secondary_dimension_share', 0):.1f}%")
        if not risks:
            risks.append("nenhum risco crítico detectado pelas regras atuais")

        return f"""
BRIEFING ANALÍTICO DATAFLOW BI

SCHEMA:
- domínio detectado: {domain}
- métrica principal: {metric_label}
- dimensão principal: {primary_label}
- dimensão secundária: {secondary_label}
- confiança do schema: {schema.get('confidence', 0)}
- avisos: {quality.get('schema_warnings', [])}

KPIS:
- total da métrica principal: {analytics_state.get('faturamento_total', 0):,.2f}
- média por registro: {analytics_state.get('ticket_medio', 0):,.2f}
- registros analisados: {analytics_state.get('total_pedidos', 0)}
- quantidade total: {analytics_state.get('quantidade_total', 0):,.2f}
- crescimento da métrica principal: {analytics_state.get('crescimento_faturamento', 0):.2f}%
- crescimento da média por registro: {analytics_state.get('crescimento_ticket', 0):.2f}%

DESTAQUES:
- top {primary_label}: {analytics_state.get('top_primary_dimension', 'Não informado')} ({analytics_state.get('top_primary_dimension_value', 0):,.2f})
- top {secondary_label}: {analytics_state.get('top_secondary_dimension', 'Não informado')} ({analytics_state.get('top_secondary_dimension_value', 0):,.2f})
- participação do top {secondary_label}: {analytics_state.get('top_secondary_dimension_share', 0):.2f}%
- pior {primary_label} relativo: {analytics_state.get('bottom_primary_dimension', 'Não informado')} ({analytics_state.get('bottom_primary_dimension_performance', 0):.2f}% da média)

RANKING {primary_label}:
{safe_records(primary_summary)}

RANKING {secondary_label}:
{safe_records(secondary_summary)}

RISCOS DETECTADOS:
- {'; '.join(risks)}
""".strip()

    def clean_history(self, history):
        if not history:
            return []
        return [{"role": item.get("role", "user"), "content": str(item.get("content", ""))} for item in history[-6:]]

    def build_messages(self, question: str, analytics_state: dict[str, Any], history=None):
        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_executive_briefing(analytics_state)},
        ]
        messages.extend(self.clean_history(history))
        messages.append({"role": "user", "content": question})
        return messages

    def generate_response(self, question: str, analytics_state: dict[str, Any], history=None) -> str:
        if not self.groq_api_key:
            return (
                "Assistente de IA ainda não configurado. Crie um arquivo .env na raiz do projeto com:\n\n"
                "GROQ_API_KEY=sua_chave_aqui\n"
                "GROQ_MODEL=llama-3.1-8b-instant\n\n"
                "Enquanto isso, os insights automáticos do dashboard continuam funcionando sem IA externa."
            )

        try:
            from services.providers.groq_provider import GroqProvider

            provider = GroqProvider()
            messages = self.build_messages(question, analytics_state, history)
            return provider.generate(messages)
        except ModuleNotFoundError:
            return "Dependência ausente: instale o pacote groq com `pip install groq` ou rode `pip install -r requirements.txt`."
        except Exception as error:
            return f"Erro ao consultar o provedor de IA: {error}"


def get_llm_router() -> LLMRouter:
    return LLMRouter()
