from typing import Any

from backend.retrieval.retrieval_agent import RetrievalAgent
from backend.agent.answer_agent import AnswerAgent
from backend.agent.web_search import NaverSearchAgent


class MainAgent:
    """사용자 입력을 라우팅하며 Sub Agent 간 통신을 중재한다."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent | None = None,
        answer_agent: AnswerAgent | None = None,
    ) -> None:
        # 기본값은 실제 구현체, 테스트 시 mock 주입 가능
        self._agents: dict[str, Any] = {
            "retrieval": retrieval_agent or RetrievalAgent(),
            "answer": answer_agent or AnswerAgent(),
        }

    def route(self, agent_name: str, payload: dict) -> dict:
        agent = self._agents.get(agent_name)
        if agent is None:
            return {
                "success": False,
                "data": None,
                "error": f"등록되지 않은 Agent: {agent_name}",
            }
        return agent.run(payload)

    def query(self, user_query: str, use_web_search: bool = False) -> dict:
        """
        사용자 질의를 받아 Retrieval → Answer 순서로 처리 후 결과를 반환한다.

        Returns:
            dict: success, data(answer, sources, query), error
        """
        # 1. 벡터 검색
        retrieval_result = self.route("retrieval", {"query": user_query})
        if not retrieval_result["success"]:
            return {
                "success": False,
                "data": None,
                "error": f"검색 실패: {retrieval_result['error']}",
            }

        chunks = retrieval_result["data"]["chunks"]

        # 2. 웹 검색 (선택)
        web_results = []
        if use_web_search:
            web_result = NaverSearchAgent().run({"query": user_query, "display": 5})
            if web_result["success"]:
                web_results = web_result["data"]["results"]

        # 3. 답변 생성
        answer_result = self.route("answer", {"query": user_query, "chunks": chunks, "web_results": web_results})
        if not answer_result["success"]:
            return {
                "success": False,
                "data": None,
                "error": f"답변 생성 실패: {answer_result['error']}",
            }

        return {
            "success": True,
            "data": {
                "answer": answer_result["data"]["answer"],
                "sources": answer_result["data"]["sources"],
                "web_sources": answer_result["data"].get("web_sources", []),
                "query": user_query,
            },
            "error": None,
        }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = MainAgent()
    result = agent.query("연차 휴가는 몇 일 전에 신청해야 하나요?")

    if result["success"]:
        data = result["data"]
        print(f"\n[질문] {data['query']}")
        print(f"\n[답변]\n{data['answer']}")
        print(f"\n[출처]")
        for src in data["sources"]:
            print(f"  - {src}")
    else:
        print(f"오류: {result['error']}")
