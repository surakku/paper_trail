from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatIntent, ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.services.neo4j_service import Neo4jService
from app.services.embeddings_service import EmbeddingsService
from app.pipelines.client import RocketRideClient, PIPELINE_QA, PIPELINE_SUMMARIZE, PIPELINE_DISCOVERY, PIPELINE_WEB_SEARCH
from app.dependencies import get_neo4j, get_llm, get_embeddings, get_rocketride

router = APIRouter(prefix="/api/chat", tags=["chat"])

_INTENT_PATTERNS: dict[ChatIntent, list[str]] = {
    ChatIntent.SUMMARIZE: [r"\bsummar", r"\bsummarise", r"\bsum up", r"\boverview of"],
    ChatIntent.DISCOVER: [r"\bconnect", r"\brelat", r"\blink", r"\bbetween\b", r"\bhow does .+ relate"],
    ChatIntent.INGEST: [r"\badd\b", r"\bingest\b", r"\bimport\b", r"\bsearch for papers"],
    ChatIntent.SEARCH: [r"\bfind papers\b", r"\bsearch for papers\b", r"\blook for papers\b", r"\bshow me papers\b", r"\bfetch papers\b"],
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
    embeddings: EmbeddingsService = Depends(get_embeddings),
    rocketride: RocketRideClient = Depends(get_rocketride),
) -> StreamingResponse:
    intent = _detect_intent(request.message)

    async def _generate():
        # Emit intent metadata first so the client knows the type
        yield f"data: {json.dumps({'type': 'intent', 'intent': intent.value})}\n\n"

        try:
            if intent == ChatIntent.SUMMARIZE:
                # Try to extract a paper title/ID from the message and summarize it
                papers = await neo4j.search_papers(request.message, limit=1)
                if not papers:
                    yield f"data: {json.dumps({'type': 'text', 'content': 'No matching paper found in the knowledge graph. Try ingesting it first.'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                paper = papers[0]
                context = await neo4j.get_paper_context([paper["id"]])
                
                # Run through RocketRide summarize pipeline
                async with rocketride as client:
                    pipeline_input = {
                        "paper": context[0] if context else paper,
                        "question": request.message,
                    }
                    result = await client.run(PIPELINE_SUMMARIZE, pipeline_input)
                
                # Use result from pipeline if available, otherwise fall back to direct LLM
                if result.get("status") != "passthrough":
                    yield f"data: {json.dumps({'type': 'text', 'content': result.get('output', 'Pipeline completed.')})}\n\n"
                else:
                    messages = llm.build_summarize_messages(context[0] if context else paper)
                    async for token in llm.stream(messages):
                        yield f"data: {json.dumps({'type': 'text', 'content': token})}\n\n"

            elif intent == ChatIntent.DISCOVER:
                # Search for relevant papers and find connections
                papers = await neo4j.search_papers(request.message, limit=5)
                paper_ids = [p["id"] for p in papers]
                context = await neo4j.get_paper_context(paper_ids)
                paths = []
                if len(paper_ids) >= 2:
                    paths = await neo4j.find_connections(paper_ids[0], paper_ids[1])
                
                # Run through RocketRide discovery pipeline
                async with rocketride as client:
                    pipeline_input = {
                        "query": request.message,
                        "papers": context,
                        "paths": paths,
                    }
                    result = await client.run(PIPELINE_DISCOVERY, pipeline_input)
                
                # Use result from pipeline if available, otherwise fall back to direct LLM
                if result.get("status") != "passthrough":
                    yield f"data: {json.dumps({'type': 'text', 'content': result.get('output', 'Pipeline completed.')})}\n\n"
                else:
                    messages = llm.build_discovery_messages(request.message, paths, context)
                    async for token in llm.stream(messages):
                        yield f"data: {json.dumps({'type': 'text', 'content': token})}\n\n"

            elif intent == ChatIntent.INGEST or intent == ChatIntent.SEARCH:
                # Search for papers online and add to graph (NO LLM NEEDED for this!)
                from app.api.routes.ingest import _ingest_papers
                
                # Extract search query from message - remove intent keywords and filler words
                query = request.message.lower()
                # Remove intent keywords
                for pattern in _INTENT_PATTERNS[ChatIntent.INGEST] + _INTENT_PATTERNS[ChatIntent.SEARCH]:
                    query = re.sub(pattern, "", query, flags=re.IGNORECASE)
                # Remove common filler words and propositions
                filler_words = r'\b(me|some|a|an|the|about|on|in|for|with|to|and|or)\b'
                query = re.sub(filler_words, "", query, flags=re.IGNORECASE)
                # Clean up extra whitespace
                query = re.sub(r'\s+', ' ', query).strip()
                
                if not query:
                    error_msg = 'Could not extract search query from your message. Try: "Search for papers about transformers"'
                    yield f"data: {json.dumps({'type': 'text', 'content': error_msg})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
                search_msg = f'🔍 Searching for papers about "{query}"...'
                yield f"data: {json.dumps({'type': 'text', 'content': search_msg})}\n\n"
                
                try:
                    # Try ArXiv first, then Semantic Scholar - NO LLM REQUIRED
                    from app.services.arxiv_service import ArxivService
                    from app.services.semantic_scholar_service import SemanticScholarService
                    
                    papers = []
                    sources = [
                        (ArxivService(), "ArXiv", 5),
                        (SemanticScholarService(), "Semantic Scholar", 3),
                    ]
                    
                    for service, source_name, max_results in sources:
                        try:
                            print(f"[CHAT] Searching {source_name}...")
                            service_papers = await service.search(query, max_results)
                            papers.extend(service_papers)
                            found_msg = f'✓ Found {len(service_papers)} papers from {source_name}'
                            yield f"data: {json.dumps({'type': 'text', 'content': found_msg})}\n\n"
                        except Exception as e:
                            print(f"[CHAT] {source_name} error: {str(e)}")
                            unavailable_msg = f'⚠️ {source_name} is temporarily unavailable'
                            yield f"data: {json.dumps({'type': 'text', 'content': unavailable_msg})}\n\n"
                    
                    if not papers:
                        yield f"data: {json.dumps({'type': 'text', 'content': 'No papers found. Try a different search.'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    
                    adding_msg = f'💾 Adding {len(papers)} papers to knowledge graph...'
                    yield f"data: {json.dumps({'type': 'text', 'content': adding_msg})}\n\n"
                    
                    # Ingest papers into Neo4j
                    ingested = await _ingest_papers(papers, neo4j, embeddings, llm)
                    
                    # Format results
                    paper_info = []
                    for p in papers[:5]:  # Show first 5
                        authors = ", ".join(p.get("authors", [])[:2])
                        if authors:
                            authors = f" by {authors}"
                        paper_info.append(f"• {p['title']}{authors}")
                    
                    result_msg = f'✅ Added {ingested} papers to your knowledge graph:\n\n' + '\n'.join(paper_info)
                    yield f"data: {json.dumps({'type': 'text', 'content': result_msg})}\n\n"
                    
                except Exception as e:
                    print(f"[CHAT] Ingest error: {str(e)}")
                    error_msg = f'Error during search: {str(e)}'
                    yield f"data: {json.dumps({'type': 'text', 'content': error_msg})}\n\n"

            else:
                # Default: QA with graph context - run through QA pipeline
                papers = await neo4j.search_papers(request.message, limit=3)  # Reduced from 5
                paper_ids = [p["id"] for p in papers] + request.context_paper_ids
                context = await neo4j.get_paper_context(list(set(paper_ids))[:3])  # Reduced from 8
                history = [{"role": m.role, "content": m.content} for m in request.history]
                
                # Run through RocketRide QA pipeline
                async with rocketride as client:
                    pipeline_input = {
                        "question": request.message,
                        "context": context,
                        "history": history,
                    }
                    result = await client.run(PIPELINE_QA, pipeline_input)
                
                # Use result from pipeline if available, otherwise fall back to direct LLM
                if result.get("status") != "passthrough":
                    yield f"data: {json.dumps({'type': 'text', 'content': result.get('output', 'Pipeline completed.')})}\n\n"
                else:
                    messages = llm.build_qa_messages(request.message, context, history)
                    async for token in llm.stream(messages):
                        yield f"data: {json.dumps({'type': 'text', 'content': token})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    neo4j: Neo4jService = Depends(get_neo4j),
    llm: LLMService = Depends(get_llm),
    rocketride: RocketRideClient = Depends(get_rocketride),
) -> ChatResponse:
    intent = _detect_intent(request.message)
    papers = await neo4j.search_papers(request.message, limit=3)  # Reduced from 5
    paper_ids = [p["id"] for p in papers] + request.context_paper_ids
    context = await neo4j.get_paper_context(list(set(paper_ids))[:3])  # Reduced from 8
    history = [{"role": m.role, "content": m.content} for m in request.history]
    
    # Try to run through RocketRide QA pipeline
    async with rocketride as client:
        pipeline_input = {
            "question": request.message,
            "context": context,
            "history": history,
        }
        result = await client.run(PIPELINE_QA, pipeline_input)
    
    # Use result from pipeline if available, otherwise fall back to direct LLM
    if result.get("status") != "passthrough":
        reply = result.get("output", "Pipeline completed.")
    else:
        messages = llm.build_qa_messages(request.message, context, history)
        reply = await llm.chat(messages)
    
    sources = [{"id": p.get("id"), "title": p.get("title"), "url": p.get("url")} for p in papers]
    return ChatResponse(reply=reply, intent=intent, sources=sources)
