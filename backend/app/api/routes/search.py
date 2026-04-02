from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.models.schemas import SearchResponse, SearchResult
from app.services.neo4j_service import Neo4jService
from app.dependencies import get_neo4j

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    neo4j: Neo4jService = Depends(get_neo4j),
) -> SearchResponse:
    papers = await neo4j.search_papers(q, limit=limit)
    results = [
        SearchResult(
            id=p.get("id", ""),
            type="paper",
            title=p.get("title", ""),
            snippet=(p.get("abstract") or "")[:200],
            url=p.get("url"),
            metadata={
                "source": p.get("source"),
                "published_date": p.get("published_date"),
            },
        )
        for p in papers
    ]
    return SearchResponse(results=results, total=len(results))
