from __future__ import annotations

import hashlib
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class WebSearchService:
    """Search the web for blog posts and articles. Uses Tavily if API key is set, else DuckDuckGo."""

    def __init__(self) -> None:
        self._tavily_key = os.environ.get("TAVILY_API_KEY")

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        if self._tavily_key:
            return await self._tavily_search(query, max_results)
        return await self._ddg_search(query, max_results)

    async def _tavily_search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        from tavily import TavilyClient
        client = TavilyClient(api_key=self._tavily_key)
        response = client.search(query=query, max_results=max_results, include_raw_content=True)
        results = []
        for r in response.get("results", []):
            results.append(self._normalize(r.get("url", ""), r.get("title", ""), r.get("content", "")))
        return results

    async def _ddg_search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(self._normalize(r.get("href", ""), r.get("title", ""), r.get("body", "")))
        return results

    def _normalize(self, url: str, title: str, content: str) -> dict[str, Any]:
        doc_id = f"web:{hashlib.sha256(url.encode()).hexdigest()[:16]}"
        return {
            "id": doc_id,
            "title": title,
            "url": url,
            "content": content,
            "source_type": "web",
            "published_date": None,
            "embedding": None,
        }
