# Skill: Sub Agent 신규 추가 (sub-agent)

새로운 Sub Agent를 추가할 때 따라야 할 구조와 통신 규칙.

---

## Agent 구조 원칙

- **Main Agent**: 라우팅만 담당. 직접 비즈니스 로직을 실행하지 않는다.
- **Sub Agent**: 단일 책임 원칙. 하나의 역할만 수행한다.
- **Sub Agent 간 직접 통신 금지**: 모든 호출은 Main Agent를 경유한다.
- **모든 반환값은 JSON(dict)**: 로그, 프린트 출력은 반환하지 않는다.

```
사용자 요청
    │
    ▼
Main Agent  ──► Ingest Agent
            ──► Retrieval Agent
            ──► Answer Agent
            ──► File Watcher Agent
```

---

## 파일 위치 규칙

| 역할 | 경로 |
|------|------|
| Sub Agent 구현 | `backend/agent/<name>_agent.py` |
| Main Agent | `backend/agent/main_agent.py` |

---

## Sub Agent 표준 템플릿

```python
# backend/agent/<name>_agent.py

from typing import Any


class <Name>Agent:
    """<역할 한 줄 설명>"""

    def run(self, payload: dict) -> dict:
        """
        Main Agent로부터 payload를 받아 처리하고 결과를 반환한다.

        Args:
            payload: Main Agent가 전달한 입력 데이터

        Returns:
            dict: success, data, error 키를 포함한 JSON 결과
        """
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> Any:
        # 실제 비즈니스 로직 구현
        raise NotImplementedError


if __name__ == "__main__":
    agent = <Name>Agent()
    test_payload = {}  # 테스트용 payload
    print(agent.run(test_payload))
```

---

## Main Agent 라우팅 등록 패턴

```python
# backend/agent/main_agent.py

from backend.agent.ingest_agent import IngestAgent
from backend.agent.retrieval_agent import RetrievalAgent
from backend.agent.answer_agent import AnswerAgent
from backend.agent.<name>_agent import <Name>Agent

AGENT_REGISTRY: dict[str, object] = {
    "ingest": IngestAgent(),
    "retrieval": RetrievalAgent(),
    "answer": AnswerAgent(),
    "<name>": <Name>Agent(),   # ← 신규 Agent 등록
}


class MainAgent:
    def route(self, agent_name: str, payload: dict) -> dict:
        agent = AGENT_REGISTRY.get(agent_name)
        if agent is None:
            return {"success": False, "data": None, "error": f"Unknown agent: {agent_name}"}
        return agent.run(payload)
```

---

## JSON 반환 포맷

모든 Sub Agent의 `run()` 메서드는 아래 구조를 반환한다.

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

실패 시:
```json
{
  "success": false,
  "data": null,
  "error": "에러 메시지"
}
```

### data 필드 예시 (Agent별)

**IngestAgent**
```json
{
  "data": {
    "file_path": "data/raw/example.pdf",
    "chunks_stored": 12,
    "skipped": false
  }
}
```

**RetrievalAgent**
```json
{
  "data": {
    "chunks": [
      { "chunk_text": "...", "metadata": { "source_path": "...", "chunk_index": 0 } }
    ]
  }
}
```

**AnswerAgent**
```json
{
  "data": {
    "answer": "답변 텍스트",
    "sources": ["data/raw/example.pdf", "data/raw/guide.docx"]
  }
}
```

---

## 체크리스트 (Sub Agent 추가 시)

- [ ] `backend/agent/<name>_agent.py` 파일 생성
- [ ] `run(payload: dict) -> dict` 시그니처 준수
- [ ] 반환값이 `success / data / error` 구조인지 확인
- [ ] 예외를 `try/except`로 잡아 `error` 필드로 반환 (raise 금지)
- [ ] `main_agent.py`의 `AGENT_REGISTRY`에 등록
- [ ] `if __name__ == "__main__":` 단독 실행 블록 포함
- [ ] Sub Agent 내부에서 다른 Sub Agent를 직접 import/호출하지 않음
