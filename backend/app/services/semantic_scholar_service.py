from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "paperId,title,abstract,year,authors,externalIds,url,citationCount,references"


class SemanticScholarService:
    def __init__(self) -> None:
        api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        headers = {"x-api-key": api_key} if api_key else {}
        self._client = httpx.AsyncClient(base_url=_BASE, headers=headers, timeout=30)

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        resp = await self._client.get(
            "/paper/search",
            params={"query": query, "limit": max_results, "fields": _FIELDS},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return [self._normalize(p) for p in data]

    async def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        resp = await self._client.get(f"/paper/{paper_id}", params={"fields": _FIELDS})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return self._normalize(resp.json())

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[str]:
        resp = await self._client.get(
            f"/paper/{paper_id}/citations",
            params={"fields": "paperId", "limit": limit},
        )
        resp.raise_for_status()
        return [
            d["citedPaper"]["paperId"]
            for d in resp.json().get("data", [])
            if d.get("citedPaper", {}).get("paperId")
        ]

    def _normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        doi = (raw.get("externalIds") or {}).get("DOI")
        return {
            "id": f"s2:{raw['paperId']}",
            "title": raw.get("title") or "",
            "abstract": raw.get("abstract") or "",
            "published_date": str(raw["year"]) if raw.get("year") else None,
            "url": raw.get("url") or f"https://www.semanticscholar.org/paper/{raw['paperId']}",
            "doi": doi,
            "source": "semantic_scholar",
            "authors": [a["name"] for a in raw.get("authors", [])],
            "pdf_url": None,
            "categories": [],
            "embedding": None,
            "full_text": None,
        }

    async def close(self) -> None:
        await self._client.aclose()
