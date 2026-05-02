import json
from groq import Groq

class ChatService:
    def __init__(
            self,
            api_key,
            temperature=1,
            model="llama-3.3-70b-versatile"
        ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def chat(self, request) -> dict:
        system_prompt = request.get("systemPrompt") or ""
        messages = request.get("messages") or []
        tools = request.get("tools") or []

        provider_messages = []
        if system_prompt:
            provider_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            provider_messages.append(self._to_provider_message(msg))

        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": provider_messages,
        }

        if tools:
            kwargs["tools"] = [self._to_provider_tool(t) for t in tools]
            kwargs["tool_choice"] = "auto"

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message

        response = {}
        text = getattr(message, "content", None)
        if text:
            response["text"] = text

        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            response["toolCalls"] = [
                {
                    "toolUseId": tc.id,
                    "name": tc.function.name,
                    "args": self._parse_args(tc.function.arguments),
                }
                for tc in tool_calls
            ]

        return response

    @staticmethod
    def _parse_args(raw):
        if raw is None or raw == "":
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return {}

    @staticmethod
    def _to_provider_tool(tool):
        definition = tool.get("definition", tool)
        return {
            "type": "function",
            "function": {
                "name": definition["name"],
                "description": definition.get("description", ""),
                "parameters": definition.get("inputSchema") or {"type": "object", "properties": {}},
            },
        }

    @staticmethod
    def _to_provider_message(msg):
        role = msg.get("role")

        if role == "user":
            return {"role": "user", "content": msg.get("content", "")}

        if role == "assistant":
            out = {"role": "assistant", "content": msg.get("content") or ""}
            tool_calls = msg.get("toolCalls") or []
            if tool_calls:
                out["tool_calls"] = [
                    {
                        "id": tc["toolUseId"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc.get("args") or {}),
                        },
                    }
                    for tc in tool_calls
                ]
            return out

        if role == "tool":
            return {
                "role": "tool",
                "tool_call_id": msg.get("toolUseId", ""),
                "content": msg.get("content", ""),
            }

        if role == "system":
            return {"role": "system", "content": msg.get("content", "")}

        raise ValueError(f"unsupported role: {role}")
