from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

import httpx

from ..config import settings


OLLAMA_WEB_BASE = "https://ollama.com/api"
SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "The-Trader/4.0 research bot"


def _clean(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def _ollama_headers() -> dict[str, str]:
    if not settings.ollama_api_key:
        raise RuntimeError(
            "OLLAMA_API_KEY is required for Ollama web search/fetch. "
            "Create an Ollama account/API key and set it in .env."
        )
    return {
        "Authorization": f"Bearer {settings.ollama_api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


def web_search(query: str, max_results: int | None = None) -> dict[str, Any]:
    """Read-only internet search requested by the Ollama agent."""
    query = str(query or "").strip()
    if not query:
        return {"ok": False, "error": "query is required", "results": []}
    limit = max(1, min(settings.ollama_web_max_results, int(max_results or settings.ollama_web_max_results)))

    if settings.ollama_web_search_enabled and settings.ollama_api_key:
        try:
            with httpx.Client(timeout=20, follow_redirects=True, headers=_ollama_headers()) as client:
                response = client.post(f"{OLLAMA_WEB_BASE}/web_search", json={"query": query, "max_results": limit})
                response.raise_for_status()
                data = response.json()
            results = data.get("results", []) if isinstance(data, dict) else []
            return {
                "ok": True,
                "provider": "ollama_web_search",
                "query": query,
                "results": [
                    {
                        "title": str(item.get("title", "")),
                        "url": str(item.get("url", "")),
                        "content": _clean(str(item.get("content", "")))[:settings.ollama_web_max_chars],
                    }
                    for item in results[:limit]
                    if isinstance(item, dict)
                ],
            }
        except (httpx.HTTPError, ValueError) as exc:
            return {"ok": False, "provider": "ollama_web_search", "query": query, "results": [], "error": f"web search failed: {exc}"}

    # Keyless fallback keeps the local research lab usable. The model still
    # explicitly requests this tool; the browser call is not performed by the model.
    try:
        with httpx.Client(timeout=12, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            response = client.get(SEARCH_URL, params={"q": query})
            response.raise_for_status()
            html = response.text
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.I | re.S,
        )
        results = []
        for match in pattern.findall(html)[:limit]:
            url, title, snippet = match
            results.append({"title": _clean(title), "url": unescape(url), "content": _clean(snippet)})
        return {"ok": True, "provider": "duckduckgo_html_fallback", "query": query, "results": results}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "provider": "duckduckgo_html_fallback", "query": query, "results": [], "error": f"web search failed: {exc}"}


def web_fetch(url: str) -> dict[str, Any]:
    """Read-only page fetch requested by the Ollama agent."""
    url = str(url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"ok": False, "error": "Only absolute http/https URLs are allowed."}

    if not settings.ollama_api_key:
        return {
            "ok": False,
            "url": url,
            "error": "OLLAMA_API_KEY is required for page fetching. Search can use the keyless fallback.",
        }

    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers=_ollama_headers()) as client:
            response = client.post(f"{OLLAMA_WEB_BASE}/web_fetch", json={"url": url})
            response.raise_for_status()
            data = response.json()
        content = _clean(str(data.get("content", "")))[:settings.ollama_web_max_chars]
        return {
            "ok": True,
            "provider": "ollama_web_fetch",
            "url": url,
            "title": str(data.get("title", "")),
            "content": content,
            "links": [str(x) for x in data.get("links", [])[:30]],
        }
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "provider": "ollama_web_fetch", "url": url, "error": f"web fetch failed: {exc}"}


def research_web(symbol: str, timeframe: str, bars: list[Any]) -> dict[str, Any]:
    """Compatibility helper for callers that want deterministic pre-search context."""
    queries = [f"{symbol} market news latest", f"{symbol} ETF official holdings methodology"]
    results = [web_search(query) for query in queries]
    sources = []
    for result in results:
        sources.extend(result.get("results", []))
    return {
        "enabled": True,
        "queries": queries,
        "sources": sources[:8],
        "errors": [r.get("error") for r in results if r.get("error")],
        "summary": "External web context is supplementary evidence only. It must not override validated market data or deterministic risk gates.",
    }
