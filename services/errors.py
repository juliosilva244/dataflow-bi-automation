class DataFlowError(Exception):
    public_message = "Não foi possível concluir a operação com segurança."
    code = "DATAFLOW_ERROR"

    def __init__(self, public_message: str | None = None, code: str | None = None):
        if public_message:
            self.public_message = public_message
        if code:
            self.code = code
        super().__init__(self.public_message)


class UploadValidationError(DataFlowError):
    code = "UPLOAD_INVALID"


class AIUsagePolicyError(DataFlowError):
    code = "AI_POLICY_BLOCKED"


class AIRateLimitError(DataFlowError):
    code = "AI_RATE_LIMIT"


class AIProviderError(DataFlowError):
    code = "AI_PROVIDER_ERROR"


class AIPayloadError(DataFlowError):
    code = "AI_PAYLOAD_INVALID"
    public_message = "Não foi possível preparar o contexto analítico para a IA. Revise os dados e tente novamente."


class AIResponseValidationError(DataFlowError):
    code = "AI_RESPONSE_UNGROUNDED"
    public_message = "A resposta da IA foi bloqueada por não apresentar referências analíticas válidas. Nenhum número não verificado foi exibido."

