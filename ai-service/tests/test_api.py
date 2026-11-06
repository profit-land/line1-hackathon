import unittest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError as error:
    raise unittest.SkipTest("FastAPI optional test dependencies are not installed") from error

from booktalk_ai.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_answer_contract_and_citations():
    response = client.post("/v1/answers", json={
        "query": "두근두근은 무슨 뜻이야?",
        "documents": [{
            "id": "exp_1",
            "title": "두근두근",
            "kind": "CONTENT",
            "text": "두근두근은 기대되거나 긴장되어 가슴이 뛰는 모양을 나타내는 말이에요.",
            "metadata": {"reviewed": True},
        }],
        "nodes": [{"id": "exp_1", "label": "두근두근", "type": "EXPRESSION"}],
        "edges": [],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "HYBRID"
    assert body["abstained"] is False
    assert body["verification"]["passed"] is True
    assert "exp_1" in body["citations"]


def test_answer_abstains_when_evidence_missing():
    response = client.post("/v1/answers", json={"query": "모르는 질문", "documents": [], "nodes": [], "edges": []})
    assert response.status_code == 200
    assert response.json()["abstained"] is True
