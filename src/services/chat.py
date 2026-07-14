import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, providers):
        providers = [p for p in providers if p is not None]
        if not providers:
            raise ValueError("ChatService requer ao menos um provider configurado")
        self.providers = providers

    def chat(self, request) -> dict:
        errors = []
        for provider in self.providers:
            try:
                result = provider.chat(request)
                if errors:
                    logger.warning(
                        "Chat respondido pelo fallback '%s' apos falha(s): %s",
                        provider.name, " | ".join(errors),
                    )
                return result
            except Exception as e:
                logger.warning("Provider de chat '%s' falhou: %s", provider.name, e)
                errors.append(f"{provider.name}: {e}")

        raise RuntimeError(
            "todos os providers de chat falharam -> " + " | ".join(errors)
        )
