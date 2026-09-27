from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from ..config import settings


class LocalAIError(RuntimeError):
    pass


class LocalAIClient:
    """Bounded Ollama client. The model is local and has no execution tools."""

    def __init__(self, model: str | None = None):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = model or settings.ollama_model

    @property
    def enabled(self) -> bool:
        return bool(settings.ai_enabled)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Model generation can legitimately take longer than a normal HTTP request,
        # especially for 7B models running on CPU. Keep connection/setup failures
        # short, but give Ollama a bounded read window for generation.
        timeout = httpx.Timeout(
            connect=5.0,
            read=max(1.0, settings.ai_timeout_seconds),
            write=10.0,
            pool=5.0,
        )
        try:
            with httpx.Client(base_url=self.base_url, timeout=timeout) as client:
                response = client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise LocalAIError(
                f"Ollama request timed out after {settings.ai_timeout_seconds:.0f}s "
                f"(model={self.model}). If this is the first run or CPU inference is slow, "
                f"warm the model with 'ollama run {self.model}' or increase AI_TIMEOUT_SECONDS."
            ) from exc
        except httpx.HTTPError as exc:
            raise LocalAIError(f"Ollama request failed: {exc}") from exc
        if response.status_code >= 400:
            raise LocalAIError(f"Ollama returned {response.status_code}: {response.text[:1000]}")
        try:
            return response.json()
        except ValueError as exc:
            raise LocalAIError("Ollama returned invalid JSON") from exc

    @staticmethod
    def _text(payload: dict[str, Any]) -> str:
        text = payload.get("message", {}).get("content")
        if isinstance(text, str) and text.strip():
            return text
        raise LocalAIError("Ollama response did not contain message content")

    def structured(self, *, system: str, user: str, name: str, schema: dict[str, Any]):
        payload = self._request({
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema,
            "options": {"temperature": 0},
        })
        raw = self._text(payload)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LocalAIError("Ollama returned non-JSON structured output") from exc
        if not isinstance(value, dict):
            raise LocalAIError("Ollama structured output was not an object")
        return value, payload.get("prompt_eval_count", 0) or 0

    def run_readonly_agent(
        self,
        *,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
        max_turns: int | None = None,
    ):
        turns = max_turns or settings.ai_max_turns
        if turns < 1 or turns > 12:
            raise LocalAIError("AI_MAX_TURNS must be between 1 and 12")
        payload = self._request({
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "tools": tools,
            "options": {"temperature": 0},
        })
        usage = {"prompt_eval_count": payload.get("prompt_eval_count", 0), "eval_count": payload.get("eval_count", 0)}
        for _ in range(turns):
            calls = payload.get("message", {}).get("tool_calls", [])
            if not calls:
                return self._text(payload), usage
            tool_messages = []
            for call in calls:
                name = call.get("function", {}).get("name")
                handler = handlers.get(name)
                if handler is None:
                    raise LocalAIError(f"AI attempted unavailable tool: {name}")
                arguments = call.get("function", {}).get("arguments", {})
                if not isinstance(arguments, dict):
                    arguments = {}
                result = handler(arguments)
                tool_messages.append({"role": "tool", "content": json.dumps(result, default=str)})
            payload = self._request({
                "model": self.model,
                "stream": False,
                "messages": [{"role": "user", "content": user}, payload.get("message", {}), *tool_messages],
                "tools": tools,
                "options": {"temperature": 0},
            })
            usage["prompt_eval_count"] += payload.get("prompt_eval_count", 0) or 0
            usage["eval_count"] += payload.get("eval_count", 0) or 0
        raise LocalAIError("Ollama tool loop exceeded AI_MAX_TURNS")


# Compatibility names keep the existing AI service import surface stable.
GrokClient = LocalAIClient
GrokError = LocalAIError
