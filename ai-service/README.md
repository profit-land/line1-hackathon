# Booktalk AI Service

검증된 백엔드 데이터를 근거로 답변하는 독립 AI 오케스트레이션 서비스다.

## 처리 방식

1. 질문 복잡도와 의도를 분류한다.
2. 단순 질문은 Hybrid(BM25 + deterministic semantic hashing) 검색으로 처리한다.
3. 관계 질문은 GraphRAG Local Search를 사용한다.
4. 전체 주제 질문은 GraphRAG Global Search를 사용한다.
5. 아이 정보·학습 이력·표현 관계가 함께 필요한 질문은 제한형 PlanRAG로 처리한다.
6. 생성 답변의 evidence coverage와 citation을 검증한다.
7. 근거가 부족하면 답변을 추측하지 않고 보류한다.

그래프는 LLM이 자동 생성하지 않는다. Spring 백엔드가 소유권 검증을 마친 `아이–페이지–표현–유형–언어`
관계를 요청에 넣는다. 따라서 그래프 추출 환각이 영구 저장되는 것을 막는다.

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn booktalk_ai.api:app --host 127.0.0.1 --port 8090
```

## 테스트

핵심 RAG 엔진 테스트는 외부 패키지 없이 실행할 수 있다.

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## API

- `GET /health`
- `POST /v1/answers`
- `POST /v1/routes/preview`

현재 생성기는 테스트 가능한 extractive provider다. 실제 LLM을 연결할 때는 `AnswerGenerator` 구현만 교체하고
retrieval, plan, citation, verification 계약은 유지한다.
