from abc import ABC, abstractmethod


class ChatProvider(ABC):
    name: str = "provider"

    @abstractmethod
    def chat(self, request: dict) -> dict:
        raise NotImplementedError
