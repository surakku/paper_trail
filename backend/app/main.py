from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.services.neo4j_service import Neo4jService
from app.services.llm_service import LLMService
from app.services.embeddings_service import EmbeddingsService
from app.pipelines.client import RocketRideClient
from app.api.routes import chat, ingest, search, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    neo4j = Neo4jService()
    await neo4j.create_constraints()
    app.state.neo4j = neo4j
    app.state.llm = LLMService()
    app.state.embeddings = EmbeddingsService()
    app.state.rocketride = RocketRideClient()

    yield

    # Shutdown
    await app.state.neo4j.close()


app = FastAPI(title="Research Knowledge Graph API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(graph.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
