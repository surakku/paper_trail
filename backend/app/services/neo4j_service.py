from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from dotenv import load_dotenv

load_dotenv()


class Neo4jService:
    def __init__(self) -> None:
        uri = os.environ["NEO4J_URI"]
        user = os.environ["NEO4J_USERNAME"]
        password = os.environ["NEO4J_PASSWORD"]
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self) -> None:
        await self._driver.close()

    # ------------------------------------------------------------------
    # Schema / indexes
    # ------------------------------------------------------------------

    async def create_constraints(self) -> None:
        async with self._driver.session() as session:
            statements = [
                "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT webcontent_id IF NOT EXISTS FOR (w:WebContent) REQUIRE w.id IS UNIQUE",
            ]
            for stmt in statements:
                await session.run(stmt)

    # ------------------------------------------------------------------
    # Paper upsert
    # ------------------------------------------------------------------

    async def upsert_paper(self, paper: dict[str, Any]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (p:Paper {id: $id})
                SET p.title = $title,
                    p.abstract = $abstract,
                    p.published_date = $published_date,
                    p.url = $url,
                    p.doi = $doi,
                    p.source = $source,
                    p.embedding = $embedding
                """,
                paper,
            )

    async def upsert_author(self, author: dict[str, Any]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (a:Author {id: $id})
                SET a.name = $name,
                    a.affiliation = $affiliation
                """,
                author,
            )

    async def link_author_paper(self, author_id: str, paper_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (a:Author {id: $author_id})
                MATCH (p:Paper {id: $paper_id})
                MERGE (a)-[:AUTHORED]->(p)
                """,
                {"author_id": author_id, "paper_id": paper_id},
            )

    async def link_citation(self, citing_id: str, cited_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (a:Paper {id: $citing_id})
                MATCH (b:Paper {id: $cited_id})
                MERGE (a)-[:CITES]->(b)
                """,
                {"citing_id": citing_id, "cited_id": cited_id},
            )

    # ------------------------------------------------------------------
    # Concept upsert
    # ------------------------------------------------------------------

    async def upsert_concept(self, concept: dict[str, Any]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (c:Concept {id: $id})
                SET c.name = $name,
                    c.description = $description,
                    c.embedding = $embedding
                """,
                concept,
            )

    async def link_paper_concept(self, paper_id: str, concept_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (p:Paper {id: $paper_id})
                MATCH (c:Concept {id: $concept_id})
                MERGE (p)-[:DISCUSSES]->(c)
                """,
                {"paper_id": paper_id, "concept_id": concept_id},
            )

    async def link_concepts(self, concept_a_id: str, concept_b_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (a:Concept {id: $a})
                MATCH (b:Concept {id: $b})
                MERGE (a)-[:RELATED_TO]->(b)
                """,
                {"a": concept_a_id, "b": concept_b_id},
            )

    # ------------------------------------------------------------------
    # WebContent upsert
    # ------------------------------------------------------------------

    async def upsert_web_content(self, content: dict[str, Any]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (w:WebContent {id: $id})
                SET w.title = $title,
                    w.url = $url,
                    w.content = $content,
                    w.source_type = $source_type,
                    w.published_date = $published_date,
                    w.embedding = $embedding
                """,
                content,
            )

    async def link_web_content_paper(self, web_id: str, paper_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (w:WebContent {id: $web_id})
                MATCH (p:Paper {id: $paper_id})
                MERGE (w)-[:REFERENCES]->(p)
                """,
                {"web_id": web_id, "paper_id": paper_id},
            )

    async def link_web_content_concept(self, web_id: str, concept_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (w:WebContent {id: $web_id})
                MATCH (c:Concept {id: $concept_id})
                MERGE (w)-[:DISCUSSES]->(c)
                """,
                {"web_id": web_id, "concept_id": concept_id},
            )

    # ------------------------------------------------------------------
    # Graph retrieval (for frontend viz)
    # ------------------------------------------------------------------

    async def get_graph(self, limit: int = 200) -> dict[str, Any]:
        async with self._driver.session() as session:
            # Step 1: Get nodes up to the limit
            nodes_result = await session.run(
                """
                MATCH (n)
                RETURN n, labels(n)[0] as node_type
                LIMIT $limit
                """,
                {"limit": limit},
            )
            nodes: dict[str, dict] = {}
            node_ids_set: set[str] = set()
            
            async for record in nodes_result:
                node = record["n"]
                node_type = record["node_type"]
                node_id = node.element_id
                node_ids_set.add(node_id)
                
                nodes[node_id] = {
                    "id": node_id,
                    "label": node.get("title") or node.get("name") or str(node_id)[:20],
                    "type": node_type,
                    "properties": dict(node),
                }
            
            # Step 2: Get ALL relationships and filter for those connecting our limited nodes
            edges: list[dict] = []
            edges_result = await session.run(
                """
                MATCH (n)-[r]->(m)
                RETURN n, r, m
                """
            )
            
            async for record in edges_result:
                start_node = record["n"]
                rel = record["r"]
                end_node = record["m"]
                
                start_id = start_node.element_id
                end_id = end_node.element_id
                
                # Only include edges where both nodes are in our limited set
                if start_id in node_ids_set and end_id in node_ids_set:
                    edges.append({
                        "source": start_id,
                        "target": end_id,
                        "relationship": rel.type,
                        "properties": dict(rel),
                    })
            
            return {"nodes": list(nodes.values()), "edges": edges}

    # ------------------------------------------------------------------
    # Search (full-text + vector fallback)
    # ------------------------------------------------------------------

    async def search_papers(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Paper)
                WHERE toLower(p.title) CONTAINS toLower($query)
                   OR toLower(p.abstract) CONTAINS toLower($query)
                RETURN p
                LIMIT $limit
                """,
                {"query": query, "limit": limit},
            )
            papers = []
            async for record in result:
                papers.append(dict(record["p"]))
            return papers

    async def get_paper_context(self, paper_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch papers + their concepts for LLM context."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.id IN $ids
                OPTIONAL MATCH (p)-[:DISCUSSES]->(c:Concept)
                OPTIONAL MATCH (a:Author)-[:AUTHORED]->(p)
                RETURN p, collect(DISTINCT c.name) AS concepts, collect(DISTINCT a.name) AS authors
                """,
                {"ids": paper_ids},
            )
            context = []
            async for record in result:
                entry = dict(record["p"])
                entry["concepts"] = record["concepts"]
                entry["authors"] = record["authors"]
                context.append(entry)
            return context

    async def find_connections(self, start_id: str, end_id: str, max_depth: int = 4) -> list[dict[str, Any]]:
        """Find paths between two nodes."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH path = shortestPath((a {id: $start_id})-[*1..$depth]-(b {id: $end_id}))
                RETURN [node IN nodes(path) | {id: node.id, label: coalesce(node.title, node.name), type: labels(node)[0]}] AS path_nodes,
                       [rel IN relationships(path) | type(rel)] AS rel_types
                LIMIT 5
                """,
                {"start_id": start_id, "end_id": end_id, "depth": max_depth},
            )
            paths = []
            async for record in result:
                paths.append({
                    "nodes": record["path_nodes"],
                    "relationships": record["rel_types"],
                })
            return paths