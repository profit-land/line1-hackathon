from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .models import Document, GraphEdge, GraphNode, Route
from .orchestrator import RagOrchestrator

app = FastAPI(title="Booktalk AI Service", version="0.1.0")
orchestrator = RagOrchestrator()


class DocumentInput(BaseModel):
    id: str
    text: str
    title: str = ""
    kind: str = "CONTENT"
    metadata: dict[str, Any] = Field(default_factory=dict)


class NodeInput(BaseModel):
    id: str
    label: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class EdgeInput(BaseModel):
    source: str
    target: str
    type: str
    weight: float = Field(default=1.0, ge=0, le=1)


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    route: Route | None = None
    documents: list[DocumentInput] = Field(default_factory=list, max_length=200)
    nodes: list[NodeInput] = Field(default_factory=list, max_length=500)
    edges: list[EdgeInput] = Field(default_factory=list, max_length=1500)


def convert(request: AnswerRequest):
    documents = [Document(**item.model_dump()) for item in request.documents]
    nodes = [GraphNode(**item.model_dump()) for item in request.nodes]
    edges = [GraphEdge(**item.model_dump()) for item in request.edges]
    return documents, nodes, edges


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/routes/preview")
def preview(request: AnswerRequest) -> dict:
    documents, _, _ = convert(request)
    return orchestrator.preview_route(request.query, documents)


@app.post("/v1/answers")
def answer(request: AnswerRequest) -> dict:
    documents, nodes, edges = convert(request)
    result = orchestrator.answer(request.query, documents, nodes, edges, request.route)
    return {
        "answer": result.answer,
        "route": result.route.value,
        "citations": list(result.citations),
        "confidence": result.confidence,
        "abstained": result.abstained,
        "plan": [{"order": step.order, "tool": step.tool.value, "reason": step.reason} for step in result.plan],
        "evidence": [{"id": item.id, "text": item.text, "source": item.source, "score": item.score,
                      "metadata": item.metadata} for item in result.evidence],
        "verification": {
            "passed": result.verification.passed,
            "citationValidity": result.verification.citation_validity,
            "evidenceCoverage": result.verification.evidence_coverage,
            "unsupportedClaims": list(result.verification.unsupported_claims),
        },
        "diagnostics": result.diagnostics,
    }
