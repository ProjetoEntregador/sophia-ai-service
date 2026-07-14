import os

from groq import Groq

from .gemini_native import GeminiNativeProvider
from .openai_compat import OpenAICompatProvider


class AIClientFactory:
    def __init__(self, env=None):
        self._env = env if env is not None else os.environ
        self._groq_clients = {}

    def groq_client(self, api_key):
        if api_key not in self._groq_clients:
            self._groq_clients[api_key] = Groq(api_key=api_key)
        return self._groq_clients[api_key]

    def build_chat_providers(self):
        providers = []

        gemini_key = self._env.get("GEMINI_API_KEY")
        if gemini_key:
            providers.append(
                GeminiNativeProvider(
                    name="gemini",
                    api_key=gemini_key,
                    model=self._env.get("GEMINI_MODEL", "gemini-3.5-flash"),
                )
            )

        groq_key = self._env.get("GROQ_API_KEY") or self._env.get("CHAT_API_KEY")
        if groq_key:
            providers.append(
                OpenAICompatProvider(
                    name="groq",
                    client=self.groq_client(groq_key),
                    model=self._env.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
                )
            )

        return providers
