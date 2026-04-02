from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatIntent, ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.services.neo4j_service import Neo4jService
from app.dependencies import get_neo4j, get_llm

router = APIRouter(prefix="/api/chat", tags=["chat"])

_INTENT_PATTERNS: dict[ChatIntent, list[str]] = {
    ChatIntent.SUMMARIZE: [r"\bsummar", r"\bsummarise", r"\bsum up", r"\boverview of"],
    ChatIntent.DISCOVER: [r"\bconnect", r"\brelat", r"\blink", r"\bbetween\b", r"\bhow does .+ relate"],
    ChatIntent.INGEST: [r"\badd\b", r"\bingest\b", r"\bimport\b", r"\bsearch for papers"],
    ChatIntent.SEARCH: [r"\bfind\b", r"\bsearch\b", r"\blook for\b", r"\bshow me papers"],
}


def _detect_intent(message: str) -> ChatIntent:
    lower = message.lower()
    for intent, patterns in _INTENT_PATTERNS.items():
        if any(re.search(p, lower) for p in patterns):
            return intent
    return ChatIntent.QA


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    neo4j: Neo4jService = Depends(get_neo4j),
    llm: LLMService = Depends(get_llm),
) -> StreamingResponse:
    intent = _detect_intent(request.message)

    async def _generate():
        # Emit intent metadata first so the client knows the type
        yield f"data: {json.dumps({'type': 'intent', 'intent': intent.value})}\n\n"

        if intent == ChatIntent.SUMMARIZE:
            # Try to extract a paper title/ID from the message and summarize it
            papers = await neo4j.search_papers(request.message, limit=1)
            if not papers:
                yield f"data: {json.dumps({'type': 'text', 'content': 'No matching paper found in the knowledge graph. Try ingesting it first.'})}\n\n"
                yield "data: [DONE]\n\n"
                return
            paper = papers[0]
            context = await neo4j.get_paper_context([paper["id"]])
            messages = llm.build_summarize_messages(context[0] if context else paper)

        elif intent == ChatIntent.DISCOVER:
            # Search for relevant papers and find connections
            papers = await neo4j.search_papers(request.message, limit=5)
            paper_ids = [p["id"] for p in papers]
            context = await neo4j.get_paper_context(paper_ids)
            paths = []
            if len(paper_ids) >= 2:
                paths = await neo4j.find_connections(paper_ids[0], paper_ids[1])
            messages = llm.build_discovery_messages(request.message, paths, context)

        else:
            # Default: QA with graph context
            papers = await neo4j.search_papers(request.message, limit=5)
            paper_ids = [p["id"] for p in papers] + request.context_paper_ids
            context = await neo4j.get_paper_context(list(set(paper_ids))[:8])
            history = [{"role": m.role, "content": m.content} for m in request.history]
            messages = llm.build_qa_messages(request.message, context, history)

        async for token in llm.stream(messages):
            yield f"data: {json.dumps({'type': 'text', 'content': token})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    neo4j: Neo4jService = Depends(get_neo4j),
    llm: LLMService = Depends(get_llm),
) -> ChatResponse:
    intent = _detect_intent(request.message)
    papers = await neo4j.search_papers(request.message, limit=5)
    paper_ids = [p["id"] for p in papers] + request.context_paper_ids
    context = await neo4j.get_paper_context(list(set(paper_ids))[:8])
    history = [{"role": m.role, "content": m.content} for m in request.history]
    messages = llm.build_qa_messages(request.message, context, history)
    reply = await llm.chat(messages)
    sources = [{"id": p.get("id"), "title": p.get("title"), "url": p.get("url")} for p in papers]
    return ChatResponse(reply=reply, intent=intent, sources=sources)
