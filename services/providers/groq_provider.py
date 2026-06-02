import os

from groq import Groq


class GroqProvider:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY não encontrada nas variáveis de ambiente.")

        self.client = Groq(api_key=self.api_key)

    def generate(self, messages, temperature=0.2, max_tokens=700):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content