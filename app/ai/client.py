from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from ..config import settings


class GrokError(RuntimeError):
    pass


class GrokClient:
    """Small Responses API client for xAI/Grok with strict JSON and read-only tools."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.xai_api_key
        self.model = model or settings.xai_model

    @property
    def enabled(self) -> bool:
        return bool(settings.ai_enabled and self.api_key)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise GrokError("XAI_API_KEY is not configured")
        try:
            with httpx.Client(base_url="https://api.x.ai/v1", timeout=settings.ai_timeout_seconds) as client:
                response = client.post(
                    "/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise GrokError(f"Grok request failed: {exc}") from exc
        if response.status_code >= 400:
            raise GrokError(f"Grok API returned {response.status_code}: {response.text[:1000]}")
        try:
            return response.json()
        except ValueError as exc:
            raise GrokError("Grok returned invalid JSON") from exc

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
            return payload["output_text"]
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    return content["text"]
        raise GrokError("Grok response did not contain output text")

    def structured(self, *, system: str, user: str, name: str, schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = self._request({
            "model": self.model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": name,
                    "schema": schema,
                    "strict": True,
                },
            },
            "prompt_cache_key": "the-trader-ai",
        })
        raw = self._extract_text(payload)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GrokError("Grok returned non-JSON structured output") from exc
        if not isinstance(value, dict):
            raise GrokError("Grok structured output was not an object")
        return value, payload.get("usage") or {}

    def run_readonly_agent(
        self,
        *,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
        max_turns: int | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Run a bounded Responses tool loop. Only explicitly registered read-only handlers execute."""
        turns = max_turns or settings.ai_max_turns
        if turns < 1 or turns > 12:
            raise GrokError("AI_MAX_TURNS must be between 1 and 12")
        payload = self._request({
            "model": self.model,
            "input": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "tools": tools,
        })
        usage: dict[str, Any] = dict(payload.get("usage") or {})
        for _ in range(turns):
            calls = [item for item in payload.get("output", []) if item.get("type") == "function_call"]
            if not calls:
                return self._extract_text(payload), usage
            outputs = []
            for call in calls:
                name = call.get("name")
                handler = handlers.get(name)
                if handler is None:
                    raise GrokError(f"AI attempted unavailable tool: {name}")
                try:
                    arguments = json.loads(call.get("arguments") or "{}")
                except json.JSONDecodeError as exc:
                    raise GrokError(f"Invalid arguments for AI tool {name}") from exc
                result = handler(arguments if isinstance(arguments, dict) else {})
                outputs.append({"type": "function_call_output", "call_id": call["call_id"], "output": json.dumps(result, default=str)})
            payload = self._request({
                "model": self.model,
                "input": outputs,
                "tools": tools,
                "previous_response_id": payload.get("id"),
            })
            for key, value in (payload.get("usage") or {}).items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
        raise GrokError("Grok tool loop exceeded AI_MAX_TURNS")
