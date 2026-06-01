"""Tacit-Knowledge Curator Agent — RAG over SOPs, manuals, and expert interviews."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Protocol, Self

import structlog

from industrial_agents.agents.base import (
    AgentCapability,
    AgentDecision,
    AgentMessage,
    AgentRole,
    BaseIndustrialAgent,
    ContextBrokerProtocol,
    GovernanceProtocol,
)

if TYPE_CHECKING:
    from industrial_agents.agents._llm import LLMProvider

log = structlog.get_logger(__name__)


class _VectorStoreProtocol(Protocol):
    def query(self: Self, query_texts: list[str], n_results: int) -> dict[str, Any]: ...

_SYSTEM_PROMPT = """You are the Tacit-Knowledge Curator for an industrial manufacturing facility.
You have access to SOPs, OEM manuals, expert interview transcripts, and historical work orders.

Given a query, return a JSON object with:
- answer: string (concise, actionable answer)
- source_documents: list of strings (document titles/IDs that informed the answer)
- confidence: float 0.0-1.0
- warnings: list of strings (safety warnings or caveats, if any)
- related_procedures: list of strings (related SOP IDs)

If you cannot answer from available knowledge, set confidence below 0.5 and explain why.
"""


class TacitKnowledgeCuratorAgent(BaseIndustrialAgent):
    role = AgentRole.TACIT_KNOWLEDGE_CURATOR
    capabilities = [
        AgentCapability(
            name="rag_query",
            description="RAG retrieval over SOPs, manuals, expert knowledge",
            inputs={"query": "string", "asset_class": "string (optional)"},
            outputs={
                "answer": "string",
                "source_documents": "list[string]",
                "confidence": "float",
            },
            purdue_zone_required=4,
            reversibility="reversible",
        ),
    ]

    def __init__(
        self: Self,
        name: str,
        llm: LLMProvider,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
        vector_store: _VectorStoreProtocol | None = None,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._vector_store = vector_store

    async def _retrieve(self: Self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if self._vector_store is None:
            return []
        try:
            results = self._vector_store.query(query_texts=[query], n_results=k)
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            return [{"text": d, "metadata": m} for d, m in zip(docs, metas, strict=False)]
        except Exception as exc:
            log.warning("vector_store_error", error=str(exc))
            return []

    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        query = message.payload.get("query", message.intent)
        log.info("tacit_knowledge_handle", query=query, trace_id=message.trace_id)

        context_docs = await self._retrieve(query)
        context_text = (
            "\n\n".join(f"[{i + 1}] {d['text'][:500]}" for i, d in enumerate(context_docs))
            or "No documents retrieved."
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (f"Query: {query}\n\nRetrieved context:\n{context_text}"),
            },
        ]

        response = await self._llm.complete(messages, temperature=0.2, max_tokens=1024)

        raw_text = next(
            (b["text"] for b in response.get("content", []) if b.get("type") == "text"),
            "{}",
        )

        try:
            result = json.loads(raw_text)
        except Exception:
            result = {
                "answer": raw_text,
                "source_documents": [],
                "confidence": 0.3,
                "warnings": [],
                "related_procedures": [],
            }

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="knowledge_response",
            payload=result,
            confidence=float(result.get("confidence", 0.5)),
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
