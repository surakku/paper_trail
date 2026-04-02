from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IngestionSource(str, Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    PDF = "pdf"
    URL = "url"
    WEB_SEARCH = "web_search"


class ChatIntent(str, Enum):
    QA = "qa"
    SUMMARIZE = "summarize"
    DISCOVER = "discover"
    INGEST = "ingest"
    SEARCH = "search"


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    source: IngestionSource
    query: str | None = Field(None, description="Search query for arxiv/semantic_scholar/web_search")
    url: str | None = Field(None, description="Direct URL to ingest")
    max_results: int = Field(10, ge=1, le=50)


class IngestResponse(BaseModel):
    ingested: int
    papers: list[dict[str, Any]]
    web_content: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    context_paper_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    intent: ChatIntent
    sources: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(20, ge=1, le=100)
    source_filter: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    id: str
    type: str  # "paper" | "web_content" | "concept"
    title: str
    snippet: str
    url: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "Paper" | "Author" | "Concept" | "Institution" | "WebContent"
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
