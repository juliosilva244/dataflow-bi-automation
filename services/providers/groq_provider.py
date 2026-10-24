import os

from groq import APIConnectionError, APIStatusError, APITimeoutError

from services.ai_trace import trace_stage
from services.errors import AIPayloadError, AIProviderError, AIUsagePolicyError
from services.logging_config import get_logger
from services.settings import SecuritySettings, get_security_settings

DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
LEGACY_GROQ_MODEL = "llama-3.1-8b-instant"
AI_GENERATION_REVISION = "IA-geracao-20261023.6"
logger = get_logger(__name__)


def configured_groq_model() -> str:
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    return DEFAULT_GROQ_MODEL if model == LEGACY_GROQ_MODEL else model


def legacy_groq_model_configured() -> bool:
    return os.getenv("GROQ_MODEL", "").strip() == LEGACY_GROQ_MODEL


def _provider_failure(error, operation):
    trace_stage("provider.error", error)
    status = error.status_code if isinstance(error, APIStatusError) else None
    if isinstance(error, APITimeoutError):
        code, message = "AI_TIMEOUT", "A Groq demorou além do limite configurado. Tente novamente mais tarde."
    elif isinstance(error, APIConnectionError):
        code, message = "AI_CONNECTION", "Não foi possível conectar à Groq. Verifique a conexão e tente novamente."
    else:
        code, message = {
            401: ("AI_AUTH", "A Groq recusou a credencial desta sessão. Confira ou substitua a chave."),
            403: ("AI_PERMISSION", "A conta ou projeto Groq não tem permissão para esta operação/modelo."),
            404: ("AI_MODEL_UNAVAILABLE", "O modelo configurado não está disponível para esta conta Groq. Revise a configuração de modelo."),
            400: ("AI_REQUEST_INVALID", "A Groq recusou o formato ou os parâmetros da solicitação."),
            413: ("AI_PAYLOAD_TOO_LARGE", "O contexto enviado excede o tamanho aceito pela Groq. Reduza o contexto."),
            422: ("AI_REQUEST_INVALID", "A Groq não conseguiu processar o contexto ou os parâmetros enviados."),
            429: ("AI_REMOTE_RATE_LIMIT", "A Groq informou um limite de requisições ou tokens. Aguarde antes de tentar novamente."),
        }.get(status, ("AI_PROVIDER_UNAVAILABLE", "A Groq está indisponível para esta solicitação. Tente novamente mais tarde."))
    logger.warning("IA provedor=groq codigo=%s status=%s etapa=%s", code, status, operation)
    raise AIProviderError(message, code=code) from None


class GroqProvider:
    def __init__(self, api_key: str, settings: SecuritySettings | None = None):
        self.settings = settings or get_security_settings()
        self.model = configured_groq_model()

        if not api_key:
            raise AIUsagePolicyError("O assistente de IA não está configurado.")

        from groq import Groq

        self.client = Groq(
            api_key=api_key,
            timeout=self.settings.ai_timeout_seconds,
            max_retries=self.settings.ai_max_retries,
        )
        trace_stage("provider.initialized", model=self.model)

    def test_connection(self) -> bool:
        try:
            models = self.client.models.list()
        except (APIConnectionError, APIStatusError) as error:
            _provider_failure(error, "models")
        identifiers = {getattr(model, "id", model) for model in getattr(models, "data", models)}
        if self.model not in identifiers:
            raise AIProviderError(
                "A credencial foi aceita, mas o modelo configurado não aparece disponível nesta conta Groq.",
                code="AI_MODEL_UNAVAILABLE",
            )
        return True

    def generate(self, messages, temperature=0.2):
        options = {}
        if self.model in {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}:
            options = {"reasoning_effort": "low", "include_reasoning": False}
        try:
            trace_stage("http.send", model=self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.settings.ai_max_output_tokens,
                **options,
            )
            trace_stage("http.received", model=self.model)
        except (APIConnectionError, APIStatusError) as error:
            _provider_failure(error, "chat")
        except (TypeError, ValueError):
            raise AIPayloadError() from None
        if not response.choices or not isinstance(response.choices[0].message.content, str) or not response.choices[0].message.content.strip():
            raise AIProviderError(
                "A Groq não retornou texto de resposta dentro dos limites configurados. Nenhuma resposta foi inventada.",
                code="AI_EMPTY_RESPONSE",
            )
        trace_stage("response.ready", model=self.model)
        return response.choices[0].message.content

