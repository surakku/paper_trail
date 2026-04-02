from __future__ import annotations

import hashlib
from typing import Any

import arxiv


class ArxivService:
    def __init__(self) -> None:
        self._client = arxiv.Client()

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        papers = []
        for result in self._client.results(search):
            paper_id = result.entry_id.split("/")[-1]
            papers.append({
                "id": f"arxiv:{paper_id}",
                "title": result.title,
                "abstract": result.summary,
                "published_date": result.published.isoformat() if result.published else None,
                "url": result.entry_id,
                "doi": result.doi,
                "source": "arxiv",
                "authors": [a.name for a in result.authors],
                "pdf_url": result.pdf_url,
                "categories": result.categories,
                "embedding": None,  # filled by embeddings_service
                "full_text": None,
            })
        return papers
