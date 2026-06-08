from __future__ import annotations

import os
from typing import Any


class GroqProvider:
    """Provider Groq para o AI BI Assistant.

    Observação técnica:
    Algumas combinações de versões entre `groq` e `httpx` geram o erro:
    `Client.__init__() got an unexpected keyword argument 'proxies'`.

    Por isso o projeto fixa `httpx==0.27.2` no requirements.txt.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente.")

        try:
            from groq import Groq
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Pacote 'groq' não instalado. Rode: pip install -r requirements.txt"
            ) from exc

        try:
            self.client = Groq(api_key=self.api_key)
        except TypeError as exc:
            if "proxies" in str(exc):
                raise RuntimeError(
                    "Incompatibilidade entre groq e httpx detectada. "
                    "Rode no terminal: pip install --upgrade --force-reinstall -r requirements.txt"
                ) from exc
            raise

    def generate(self, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 700) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content
        return content or "Não recebi resposta textual do provedor de IA."
