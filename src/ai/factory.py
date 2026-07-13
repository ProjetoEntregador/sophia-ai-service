import os

from groq import Groq
from openai import OpenAI

from .openai_compat import OpenAICompatProvider


class AIClientFactory:
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self, env=None):
        self._env = env if env is not None else os.environ
        self._groq_clients = {}

    def groq_client(self, api_key):
        if api_key not in self._groq_clients:
            self._groq_clients[api_key] = Groq(api_key=api_key)
        return self._groq_clients[api_key]

    def gemini_client(self, api_key):
        return OpenAI(api_key=api_key, base_url=self.GEMINI_BASE_URL)

    def build_chat_providers(self):
        providers = []

        groq_key = self._env.get("GROQ_API_KEY") or self._env.get("CHAT_API_KEY")
        if groq_key:
            providers.append(
                OpenAICompatProvider(
                    name="groq",
                    client=self.groq_client(groq_key),
                    model=self._env.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
                )
            )


        gemini_key = self._env.get("GEMINI_API_KEY")
        if gemini_key:
            providers.append(
                OpenAICompatProvider(
                    name="gemini",
                    client=self.gemini_client(gemini_key),
                    model=self._env.get("GEMINI_MODEL", "gemini-2.5-flash"),
                )
            )

        return providers
