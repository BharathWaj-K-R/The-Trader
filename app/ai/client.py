from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx

from ..config import settings

T = TypeVar("T")


class GrokError(RuntimeError):
    pass


class GrokClient:
    """Small Responses API client for xAI/Grok with strict structured JSON output."""

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
            detail = response.text[:1000]
            raise GrokError(f"Grok API returned {response.status_code}: {detail}")
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
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return content["text"]
        raise GrokError("Grok response did not contain output text")

    def structured(self, *, system: str, user: str, name: str, schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = self._request({
            "model": self.model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": name,
                    "schema": schema,
                    "strict": True,
                }
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
        usage = payload.get("usage") or {}
        return value, usage
