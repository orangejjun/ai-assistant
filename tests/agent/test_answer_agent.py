from unittest.mock import patch, MagicMock

import pytest


def _make_chunks(n: int = 2, same_source: bool = False) -> list[dict]:
    return [
        {
            "chunk_text": f"문서 내용 {i}번 청크입니다.",
            "source_file": "doc_a.txt" if same_source else f"doc_{i}.txt",
            "chunk_index": i,
            "distance": 0.1 * (i + 1),
        }
        for i in range(n)
    ]


@pytest.fixture
def mock_gpt():
    """OpenAI GPT API Mock."""
    with patch("backend.agent.answer_agent.OpenAI") as mock_cls:
        mock_message = MagicMock()
        mock_message.content = "테스트 답변입니다."
        mock_cls.return_value.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )
        yield mock_cls


class TestAnswerAgentRun:
    def test_returns_success_structure(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        result = AnswerAgent().run({"query": "질문", "chunks": _make_chunks()})

        assert result["success"] is True
        assert result["error"] is None
        assert "answer" in result["data"]
        assert "sources" in result["data"]

    def test_answer_text_from_gpt(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        result = AnswerAgent().run({"query": "질문", "chunks": _make_chunks()})

        assert result["data"]["answer"] == "테스트 답변입니다."

    def test_empty_chunks_returns_not_found(self) -> None:
        from backend.agent.answer_agent import AnswerAgent

        result = AnswerAgent().run({"query": "질문", "chunks": []})

        assert result["success"] is True
        assert result["data"]["answer"] == "문서에서 찾을 수 없습니다."
        assert result["data"]["sources"] == []

    def test_empty_chunks_does_not_call_gpt(self) -> None:
        from backend.agent.answer_agent import AnswerAgent

        with patch("backend.agent.answer_agent.OpenAI") as mock_cls:
            AnswerAgent().run({"query": "질문", "chunks": []})
            mock_cls.return_value.chat.completions.create.assert_not_called()

    def test_sources_extracted_from_chunks(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        chunks = _make_chunks(3)
        result = AnswerAgent().run({"query": "질문", "chunks": chunks})

        assert set(result["data"]["sources"]) == {"doc_0.txt", "doc_1.txt", "doc_2.txt"}

    def test_duplicate_sources_deduplicated(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        chunks = _make_chunks(3, same_source=True)
        result = AnswerAgent().run({"query": "질문", "chunks": chunks})

        assert result["data"]["sources"] == ["doc_a.txt"]

    def test_sources_preserve_order(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        chunks = [
            {"chunk_text": "내용", "source_file": "z.txt", "chunk_index": 0, "distance": 0.1},
            {"chunk_text": "내용", "source_file": "a.txt", "chunk_index": 1, "distance": 0.2},
            {"chunk_text": "내용", "source_file": "z.txt", "chunk_index": 2, "distance": 0.3},
        ]
        result = AnswerAgent().run({"query": "질문", "chunks": chunks})

        assert result["data"]["sources"] == ["z.txt", "a.txt"]

    def test_missing_query_returns_error(self) -> None:
        from backend.agent.answer_agent import AnswerAgent

        result = AnswerAgent().run({"chunks": _make_chunks()})

        assert result["success"] is False
        assert result["error"] is not None

    def test_gpt_called_with_correct_model(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent, GPT_MODEL

        AnswerAgent().run({"query": "질문", "chunks": _make_chunks()})

        _, kwargs = mock_gpt.return_value.chat.completions.create.call_args
        assert kwargs["model"] == GPT_MODEL

    def test_gpt_receives_query_in_user_message(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        AnswerAgent().run({"query": "특정 질문 내용", "chunks": _make_chunks()})

        _, kwargs = mock_gpt.return_value.chat.completions.create.call_args
        # messages[0]=system, messages[1]=user
        user_content = kwargs["messages"][1]["content"]
        assert "특정 질문 내용" in user_content

    def test_system_prompt_in_first_message(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        AnswerAgent().run({"query": "질문", "chunks": _make_chunks()})

        _, kwargs = mock_gpt.return_value.chat.completions.create.call_args
        assert kwargs["messages"][0]["role"] == "system"

    def test_context_contains_chunk_text(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        chunks = [{"chunk_text": "고유한청크내용XYZ", "source_file": "f.txt", "chunk_index": 0, "distance": 0.1}]
        AnswerAgent().run({"query": "질문", "chunks": chunks})

        _, kwargs = mock_gpt.return_value.chat.completions.create.call_args
        user_content = kwargs["messages"][1]["content"]
        assert "고유한청크내용XYZ" in user_content

    def test_context_contains_source_file(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        chunks = [{"chunk_text": "내용", "source_file": "important_doc.txt", "chunk_index": 0, "distance": 0.1}]
        AnswerAgent().run({"query": "질문", "chunks": chunks})

        _, kwargs = mock_gpt.return_value.chat.completions.create.call_args
        user_content = kwargs["messages"][1]["content"]
        assert "important_doc.txt" in user_content

    def test_uses_env_api_key(self, mock_gpt: MagicMock) -> None:
        from backend.agent.answer_agent import AnswerAgent

        AnswerAgent().run({"query": "질문", "chunks": _make_chunks()})

        mock_gpt.assert_called_once_with(api_key="test-openai-key")
