from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Thin wrapper around an OpenAI-compatible LLM endpoint (Modal-hosted)."""

    def __init__(self) -> None:
        base_url = os.environ["MODAL_LLM_URL"]
        api_key = os.environ.get("MODAL_LLM_API_KEY") or "placeholder"
        self._model = os.environ["MODAL_LLM_MODEL"]
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 1.0,   # Qwen3.5 thinking mode default
        max_tokens: int = 8192,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 1.0,   # Qwen3.5 thinking mode default
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    def build_qa_messages(
        self,
        question: str,
        context: list[dict[str, Any]],
        history: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        context_text = "\n\n".join(
            f"[{i+1}] Title: {p.get('title','')}\n"
            f"Abstract: {(p.get('abstract','') or '')[:600]}\n"
            f"Authors: {', '.join(p.get('authors', []))}\n"
            f"Concepts: {', '.join(p.get('concepts', []))}"
            for i, p in enumerate(context)
        )
        system = (
            "You are an expert research assistant with access to an academic knowledge graph. "
            "Answer the user's question using the provided paper context. "
            "Cite papers by their number [1], [2], etc. when referencing them. "
            "Be concise and precise.\n\n"
            f"## Knowledge Graph Context\n{context_text}"
        )
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        return messages

    def build_summarize_messages(self, paper: dict[str, Any]) -> list[dict[str, str]]:
        system = (
            "You are an expert research assistant. "
            "Produce a structured summary of the following paper with sections: "
            "**TL;DR**, **Key Contributions**, **Methods**, **Results**, **Limitations**."
        )
        content = (
            f"Title: {paper.get('title', '')}\n"
            f"Authors: {', '.join(paper.get('authors', []))}\n"
            f"Published: {paper.get('published_date', '')}\n\n"
            f"Abstract:\n{paper.get('abstract', '')}\n\n"
            f"Full text excerpt:\n{(paper.get('full_text', '') or '')[:3000]}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]

    def build_discovery_messages(
        self,
        topic: str,
        paths: list[dict[str, Any]],
        related_papers: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        paths_text = "\n".join(
            " → ".join(
                f"{n['label']} ({n['type']})" for n in p["nodes"]
            )
            for p in paths
        )
        papers_text = "\n".join(
            f"- {p.get('title', '')} ({p.get('published_date', '')})"
            for p in related_papers[:10]
        )
        system = "You are an expert research assistant helping users discover connections in academic literature."
        user = (
            f"I'm exploring: **{topic}**\n\n"
            f"Knowledge graph paths found:\n{paths_text or 'No direct paths found.'}\n\n"
            f"Related papers:\n{papers_text or 'None found.'}\n\n"
            "Explain the connections between these concepts and papers, "
            "highlighting surprising or non-obvious relationships."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
