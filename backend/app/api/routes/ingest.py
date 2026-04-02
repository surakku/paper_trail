from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import IngestionSource, IngestRequest, IngestResponse
from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.pdf_service import PDFService
from app.services.web_search_service import WebSearchService
from app.services.embeddings_service import EmbeddingsService
from app.services.neo4j_service import Neo4jService
from app.services.llm_service import LLMService
from app.dependencies import get_neo4j, get_embeddings, get_llm

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


async def _extract_concepts(abstract: str, llm: LLMService) -> list[str]:
    prompt = [
        {"role": "system", "content": "Extract 3-8 key research concepts from the abstract. Return ONLY a JSON array of short concept strings, e.g. [\"transformer\", \"attention mechanism\"]."},
        {"role": "user", "content": abstract[:1500]},
    ]
    raw = await llm.chat(prompt, temperature=0.2, max_tokens=200)
    try:
        concepts = json.loads(raw.strip())
        return [c for c in concepts if isinstance(c, str)][:8]
    except Exception:
        return []


async def _ingest_papers(
    papers: list[dict[str, Any]],
    neo4j: Neo4jService,
    embeddings: EmbeddingsService,
    llm: LLMService,
) -> None:
    for paper in papers:
        # Embed
        text = f"{paper['title']} {paper['abstract'] or ''}"
        paper["embedding"] = embeddings.embed(text)

        # Extract concepts
        concepts = await _extract_concepts(paper.get("abstract") or "", llm)

        # Upsert paper
        await neo4j.upsert_paper({
            "id": paper["id"],
            "title": paper["title"],
            "abstract": paper.get("abstract"),
            "published_date": paper.get("published_date"),
            "url": paper.get("url"),
            "doi": paper.get("doi"),
            "source": paper.get("source"),
            "embedding": paper["embedding"],
        })

        # Upsert authors
        for author_name in paper.get("authors", []):
            author_id = f"author:{author_name.lower().replace(' ', '_')}"
            await neo4j.upsert_author({"id": author_id, "name": author_name, "affiliation": None})
            await neo4j.link_author_paper(author_id, paper["id"])

        # Upsert concepts
        for concept_name in concepts:
            concept_id = f"concept:{concept_name.lower().replace(' ', '_')}"
            concept_text = concept_name
            await neo4j.upsert_concept({
                "id": concept_id,
                "name": concept_name,
                "description": None,
                "embedding": embeddings.embed(concept_text),
            })
            await neo4j.link_paper_concept(paper["id"], concept_id)


async def _ingest_web_content(
    items: list[dict[str, Any]],
    neo4j: Neo4jService,
    embeddings: EmbeddingsService,
) -> None:
    for item in items:
        text = f"{item['title']} {item['content'] or ''}"
        item["embedding"] = embeddings.embed(text[:512])
        await neo4j.upsert_web_content({
            "id": item["id"],
            "title": item["title"],
            "url": item["url"],
            "content": (item.get("content") or "")[:5000],
            "source_type": item.get("source_type", "web"),
            "published_date": item.get("published_date"),
            "embedding": item["embedding"],
        })


@router.post("", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    neo4j: Neo4jService = Depends(get_neo4j),
    embeddings: EmbeddingsService = Depends(get_embeddings),
    llm: LLMService = Depends(get_llm),
) -> IngestResponse:
    papers: list[dict[str, Any]] = []
    web_content: list[dict[str, Any]] = []

    if request.source == IngestionSource.ARXIV:
        svc = ArxivService()
        papers = await svc.search(request.query or "", request.max_results)

    elif request.source == IngestionSource.SEMANTIC_SCHOLAR:
        svc = SemanticScholarService()
        papers = await svc.search(request.query or "", request.max_results)
        await svc.close()

    elif request.source == IngestionSource.WEB_SEARCH:
        svc = WebSearchService()
        web_content = await svc.search(request.query or "", request.max_results)

    elif request.source == IngestionSource.URL:
        if not request.url:
            raise HTTPException(400, "url is required for URL source")
        svc = WebSearchService()
        web_content = [svc._normalize(request.url, request.url, "")]

    await _ingest_papers(papers, neo4j, embeddings, llm)
    await _ingest_web_content(web_content, neo4j, embeddings)

    return IngestResponse(ingested=len(papers) + len(web_content), papers=papers, web_content=web_content)


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    neo4j: Neo4jService = Depends(get_neo4j),
    embeddings: EmbeddingsService = Depends(get_embeddings),
    llm: LLMService = Depends(get_llm),
) -> IngestResponse:
    content = await file.read()
    svc = PDFService()
    paper = svc.extract(content, file.filename or "upload.pdf")
    await _ingest_papers([paper], neo4j, embeddings, llm)
    return IngestResponse(ingested=1, papers=[paper], web_content=[])
