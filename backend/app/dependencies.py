from __future__ import annotations

from fastapi import Request

from app.services.neo4j_service import Neo4jService
from app.services.llm_service import LLMService
from app.services.embeddings_service import EmbeddingsService


def get_neo4j(request: Request) -> Neo4jService:
    return request.app.state.neo4j


def get_llm(request: Request) -> LLMService:
    return request.app.state.llm


def get_embeddings(request: Request) -> EmbeddingsService:
    return request.app.state.embeddings
