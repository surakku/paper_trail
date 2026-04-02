from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.models.schemas import GraphResponse
from app.services.neo4j_service import Neo4jService
from app.dependencies import get_neo4j

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
async def get_graph(
    limit: int = Query(200, ge=1, le=1000),
    neo4j: Neo4jService = Depends(get_neo4j),
) -> GraphResponse:
    data = await neo4j.get_graph(limit=limit)
    return GraphResponse(nodes=data["nodes"], edges=data["edges"])


@router.get("/connections")
async def get_connections(
    start_id: str = Query(...),
    end_id: str = Query(...),
    max_depth: int = Query(4, ge=1, le=6),
    neo4j: Neo4jService = Depends(get_neo4j),
) -> dict:
    paths = await neo4j.find_connections(start_id, end_id, max_depth)
    return {"paths": paths}
