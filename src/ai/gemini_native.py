import json
from typing import Any

from google import genai

from .base import ChatProvider


class GeminiNativeProvider(ChatProvider):
    def __init__(self, name, api_key, model, temperature=1):
        self.name = name
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.supports_tools = True
        self._interaction_cache: dict[str, str] = {}
        self._cache_order: list[str] = []

    def chat(self, request) -> dict:
        system_prompt = request.get("systemPrompt") or ""
        messages = request.get("messages") or []
        tools = request.get("tools") or []

        previous_key, previous_interaction_id, prefix_len = self._resolve_previous_state(
            system_prompt,
            tools,
            messages,
        )
        delta_messages = messages[prefix_len:]
        input_steps = self._to_interaction_steps(messages, delta_messages)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": input_steps,
            "temperature": self.temperature,
        }

        if tools:
            kwargs["tools"] = [self._to_tool(tool) for tool in tools]

        if system_prompt and previous_interaction_id is None:
            kwargs["system_instruction"] = system_prompt

        if previous_interaction_id is not None:
            kwargs["previous_interaction_id"] = previous_interaction_id

        try:
            interaction = self.client.interactions.create(**kwargs)
        except TypeError as exc:
            message = str(exc)
            fallback_kwargs = dict(kwargs)
            removed = False

            for key in ("system_instruction", "temperature"):
                if key in message and key in fallback_kwargs:
                    fallback_kwargs.pop(key, None)
                    removed = True

            if not removed:
                raise

            interaction = self.client.interactions.create(**fallback_kwargs)

        response: dict[str, Any] = {}
        text = getattr(interaction, "output_text", None)
        if text:
            response["text"] = text

        tool_calls = self._extract_tool_calls(interaction)
        if tool_calls:
            response["toolCalls"] = tool_calls

        self._remember_state(previous_key, system_prompt, tools, messages, interaction.id)
        return response

    def _resolve_previous_state(self, system_prompt, tools, messages):
        if not messages:
            return None, None, 0

        for end in range(len(messages), -1, -1):
            candidate_messages = messages[:end]
            candidate_key = self._cache_key(system_prompt, tools, candidate_messages)
            previous_interaction_id = self._interaction_cache.get(candidate_key)
            if previous_interaction_id:
                return candidate_key, previous_interaction_id, end

        return None, None, 0

    def _remember_state(self, previous_key, system_prompt, tools, messages, interaction_id):
        key = self._cache_key(system_prompt, tools, messages)
        self._interaction_cache[key] = interaction_id
        self._cache_order.append(key)

        if previous_key and previous_key not in self._interaction_cache:
            self._interaction_cache[previous_key] = interaction_id

        while len(self._cache_order) > 100:
            old_key = self._cache_order.pop(0)
            self._interaction_cache.pop(old_key, None)

    def _to_interaction_steps(self, full_messages, delta_messages):
        steps = []
        for msg in delta_messages:
            role = msg.get("role")

            if role == "user":
                steps.append(self._to_user_input(msg))
                continue

            if role == "assistant":
                text = msg.get("content")
                if text:
                    steps.append({"type": "text", "text": text})
                for call in msg.get("toolCalls") or []:
                    steps.append(self._to_function_call(call))
                continue

            if role == "tool":
                steps.append(self._to_function_result(full_messages, msg))
                continue

            if role == "system":
                continue

            raise ValueError(f"unsupported role: {role}")

        return steps

    @staticmethod
    def _to_user_input(msg):
        return {
            "type": "user_input",
            "content": [{"type": "text", "text": msg.get("content", "")}],
        }

    @staticmethod
    def _to_function_call(call):
        return {
            "type": "function_call",
            "id": call["toolUseId"],
            "name": call["name"],
            "arguments": call.get("args") or {},
        }

    def _to_function_result(self, messages, msg):
        tool_name = self._tool_name_for_call(messages, msg.get("toolUseId", ""))
        if not tool_name:
            tool_name = "unknown_tool"
        return {
            "type": "function_result",
            "name": tool_name,
            "call_id": msg.get("toolUseId", ""),
            "result": [{"type": "text", "text": msg.get("content", "")}],
        }

    @staticmethod
    def _tool_name_for_call(messages, tool_use_id):
        for message in reversed(messages):
            if message.get("role") != "assistant":
                continue
            for call in message.get("toolCalls") or []:
                if call.get("toolUseId") == tool_use_id:
                    return call.get("name")
        return None

    @staticmethod
    def _to_tool(tool):
        definition = tool.get("definition", tool)
        return {
            "type": "function",
            "name": definition["name"],
            "description": definition.get("description", ""),
            "parameters": definition.get("inputSchema")
            or {"type": "object", "properties": {}},
        }

    @staticmethod
    def _extract_tool_calls(interaction):
        tool_calls = []
        for step in getattr(interaction, "steps", []) or []:
            if getattr(step, "type", None) != "function_call":
                continue
            tool_calls.append(
                {
                    "toolUseId": getattr(step, "id", ""),
                    "name": getattr(step, "name", ""),
                    "args": getattr(step, "arguments", {}) or {},
                }
            )
        return tool_calls

    @staticmethod
    def _cache_key(system_prompt, tools, messages):
        normalized = {
            "systemPrompt": system_prompt or "",
            "tools": tools or [],
            "messages": messages or [],
        }
        return json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
