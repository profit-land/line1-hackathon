import unittest

from booktalk_ai.graph import GraphIndex
from booktalk_ai.models import Document, GraphEdge, GraphNode, Route
from booktalk_ai.orchestrator import RagOrchestrator
from booktalk_ai.planner import QueryRouter
from booktalk_ai.retrieval import HybridRetriever


class RagCoreTests(unittest.TestCase):
    def setUp(self):
        self.documents = [
            Document("exp_1", "두근두근은 기대되거나 긴장될 때 가슴이 뛰는 모양을 나타내는 말이에요.", "두근두근", "CONTENT"),
            Document("exp_2", "깡충깡충은 두 발을 모아 가볍게 계속 뛰는 모양이에요.", "깡충깡충", "CONTENT"),
            Document("profile", "아이 연령은 4세이고 설명 언어는 베트남어입니다.", "아이 프로필", "PROFILE"),
            Document("history", "두근두근 문장 연습을 한 번 완료했습니다.", "학습 기록", "HISTORY"),
        ]
        self.nodes = [
            GraphNode("exp_1", "두근두근", "EXPRESSION"),
            GraphNode("type_1", "의태어", "TYPE"),
            GraphNode("scene_1", "선물 상자 열기", "SCENE"),
        ]
        self.edges = [GraphEdge("exp_1", "type_1", "HAS_TYPE"), GraphEdge("exp_1", "scene_1", "USED_IN")]

    def test_hybrid_retrieval_prefers_exact_expression(self):
        results = HybridRetriever().search("두근두근 뜻", self.documents)
        self.assertEqual("exp_1", results[0].id)

    def test_graph_local_expands_neighbors(self):
        results = GraphIndex(self.nodes, self.edges).local_search("두근두근 어떤 상황")
        ids = {result.id for result in results}
        self.assertIn("graph:exp_1", ids)
        self.assertIn("graph:scene_1", ids)

    def test_router_uses_plan_for_personalized_multi_source_question(self):
        route = QueryRouter().route("4세 아이의 학습 이력을 보고 두근두근을 어떻게 가르칠지 추천해줘")
        self.assertEqual(Route.PLAN, route)

    def test_orchestrator_returns_cited_grounded_answer(self):
        result = RagOrchestrator(minimum_confidence=0.15).answer(
            "두근두근은 어떤 뜻이고 언제 써?", self.documents, self.nodes, self.edges
        )
        self.assertFalse(result.abstained)
        self.assertTrue(result.verification.passed)
        self.assertIn("exp_1", result.citations)

    def test_orchestrator_abstains_without_evidence(self):
        result = RagOrchestrator().answer("근거 없는 질문", [], [], [])
        self.assertTrue(result.abstained)
        self.assertEqual("INSUFFICIENT_EVIDENCE", result.diagnostics["reason"])


if __name__ == "__main__":
    unittest.main()
