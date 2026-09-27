from __future__ import annotations

import re
from html import unescape
from typing import Any

import httpx


SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "The-Trader/4.0 research bot"


def _clean(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def research_web(symbol: str, timeframe: str, bars: list[Any]) -> dict[str, Any]:
    """Small, read-only web research layer. It returns source metadata, never execution instructions."""
    queries = [
        f"{symbol} market news latest",
        f"{symbol} ETF official holdings methodology",
    ]
    sources: list[dict[str, str]] = []
    errors: list[str] = []
    try:
        with httpx.Client(timeout=12, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            for query in queries:
                response = client.get(SEARCH_URL, params={"q": query})
                response.raise_for_status()
                html = response.text
                pattern = re.compile(
                    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
                    r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                    re.I | re.S,
                )
                for match in pattern.findall(html)[:4]:
                    url, title, snippet = match
                    sources.append({"title": _clean(title), "url": unescape(url), "snippet": _clean(snippet)})
    except (httpx.HTTPError, ValueError) as exc:
        errors.append(f"web search failed: {exc}")

    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in sources:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return {
        "enabled": True,
        "queries": queries,
        "sources": unique[:8],
        "errors": errors,
        "summary": "External web context is supplementary evidence only. It must not override validated market data or deterministic risk gates.",
    }
