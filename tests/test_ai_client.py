from unittest.mock import patch

import httpx
import pytest

from app.ai.client import LocalAIClient, LocalAIError


def test_ollama_timeout_has_actionable_message():
    client = LocalAIClient(model="qwen2.5:7b")
    with patch("app.ai.client.httpx.Client.post", side_effect=httpx.ReadTimeout("slow")):
        with pytest.raises(LocalAIError, match="timed out after"):
            client._request({"model": "qwen2.5:7b", "stream": False})


def test_ollama_timeout_mentions_warmup():
    client = LocalAIClient(model="qwen2.5:7b")
    with patch("app.ai.client.httpx.Client.post", side_effect=httpx.ReadTimeout("slow")):
        with pytest.raises(LocalAIError, match="ollama run qwen2.5:7b"):
            client._request({"model": "qwen2.5:7b", "stream": False})
