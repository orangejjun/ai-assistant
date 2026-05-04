from unittest.mock import MagicMock

import pytest


def _mock_retrieval_agent(chunks: list[dict] | None = None, success: bool = True) -> MagicMock:
    agent = MagicMock()
    if success:
        agent.run.return_value = {
            "success": True,
            "data": {"chunks": chunks or [
                {"chunk_text": "테스트 청크", "source_file": "doc.txt", "chunk_index": 0, "distance": 0.1}
            ]},
            "error": None,
        }
    else:
        agent.run.return_value = {"success": False, "data": None, "error": "검색 오류"}
    return agent


def _mock_answer_agent(answer: str = "테스트 답변", sources: list[str] | None = None, success: bool = True) -> MagicMock:
    agent = MagicMock()
    if success:
        agent.run.return_value = {
            "success": True,
            "data": {"answer": answer, "sources": sources or ["doc.txt"]},
            "error": None,
        }
    else:
        agent.run.return_value = {"success": False, "data": None, "error": "답변 오류"}
    return agent


class TestMainAgentQuery:
    def test_returns_success_structure(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(),
            answer_agent=_mock_answer_agent(),
        )
        result = agent.query("질문")

        assert result["success"] is True
        assert result["error"] is None
        assert "answer" in result["data"]
        assert "sources" in result["data"]
        assert "query" in result["data"]

    def test_result_contains_original_query(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(),
            answer_agent=_mock_answer_agent(),
        )
        result = agent.query("원본 질문")

        assert result["data"]["query"] == "원본 질문"

    def test_retrieval_called_before_answer(self) -> None:
        from backend.agent.main_agent import MainAgent

        call_order: list[str] = []

        retrieval = MagicMock()
        retrieval.run.side_effect = lambda p: (
            call_order.append("retrieval"),
            {"success": True, "data": {"chunks": []}, "error": None},
        )[1]

        answer = MagicMock()
        answer.run.side_effect = lambda p: (
            call_order.append("answer"),
            {"success": True, "data": {"answer": "답변", "sources": []}, "error": None},
        )[1]

        MainAgent(retrieval_agent=retrieval, answer_agent=answer).query("질문")

        assert call_order == ["retrieval", "answer"]

    def test_retrieval_receives_query(self) -> None:
        from backend.agent.main_agent import MainAgent

        retrieval = _mock_retrieval_agent()
        agent = MainAgent(retrieval_agent=retrieval, answer_agent=_mock_answer_agent())
        agent.query("특정 질문")

        retrieval.run.assert_called_once_with({"query": "특정 질문"})

    def test_answer_receives_query_and_chunks(self) -> None:
        from backend.agent.main_agent import MainAgent

        chunks = [{"chunk_text": "내용", "source_file": "f.txt", "chunk_index": 0, "distance": 0.1}]
        retrieval = _mock_retrieval_agent(chunks=chunks)
        answer = _mock_answer_agent()

        MainAgent(retrieval_agent=retrieval, answer_agent=answer).query("질문")

        answer.run.assert_called_once_with({"query": "질문", "chunks": chunks})

    def test_retrieval_failure_propagated(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(success=False),
            answer_agent=_mock_answer_agent(),
        )
        result = agent.query("질문")

        assert result["success"] is False
        assert "검색 실패" in result["error"]

    def test_answer_failure_propagated(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(),
            answer_agent=_mock_answer_agent(success=False),
        )
        result = agent.query("질문")

        assert result["success"] is False
        assert "답변 생성 실패" in result["error"]

    def test_answer_not_called_if_retrieval_fails(self) -> None:
        from backend.agent.main_agent import MainAgent

        answer = _mock_answer_agent()
        MainAgent(
            retrieval_agent=_mock_retrieval_agent(success=False),
            answer_agent=answer,
        ).query("질문")

        answer.run.assert_not_called()

    def test_answer_and_sources_passed_through(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(),
            answer_agent=_mock_answer_agent(answer="최종 답변", sources=["src_a.txt", "src_b.txt"]),
        )
        result = agent.query("질문")

        assert result["data"]["answer"] == "최종 답변"
        assert result["data"]["sources"] == ["src_a.txt", "src_b.txt"]


class TestMainAgentRoute:
    def test_route_dispatches_to_registered_agent(self) -> None:
        from backend.agent.main_agent import MainAgent

        retrieval = _mock_retrieval_agent()
        agent = MainAgent(retrieval_agent=retrieval, answer_agent=_mock_answer_agent())

        agent.route("retrieval", {"query": "테스트"})

        retrieval.run.assert_called_once_with({"query": "테스트"})

    def test_route_unknown_agent_returns_error(self) -> None:
        from backend.agent.main_agent import MainAgent

        agent = MainAgent(
            retrieval_agent=_mock_retrieval_agent(),
            answer_agent=_mock_answer_agent(),
        )
        result = agent.route("nonexistent_agent", {})

        assert result["success"] is False
        assert "등록되지 않은 Agent" in result["error"]

    def test_route_passes_payload_unchanged(self) -> None:
        from backend.agent.main_agent import MainAgent

        answer = _mock_answer_agent()
        agent = MainAgent(retrieval_agent=_mock_retrieval_agent(), answer_agent=answer)

        payload = {"query": "질문", "chunks": [], "extra": "값"}
        agent.route("answer", payload)

        answer.run.assert_called_once_with(payload)
