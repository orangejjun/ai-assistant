from unittest.mock import patch, MagicMock

import pytest


def _make_chroma_response(texts: list[str], distances: list[float]) -> dict:
    """ChromaDB query 응답 형식 Mock을 생성한다."""
    return {
        "documents": [texts],
        "metadatas": [
            [{"source_file": f"/data/raw/doc{i}.txt", "chunk_index": i} for i in range(len(texts))]
        ],
        "distances": [distances],
    }


@pytest.fixture
def mock_openai_embed():
    """OpenAI 임베딩 API Mock: 1536차원 벡터 반환."""
    with patch("backend.retrieval.retrieval_agent.OpenAI") as mock_cls:
        mock_item = MagicMock()
        mock_item.embedding = [0.1] * 1536
        mock_cls.return_value.embeddings.create.return_value = MagicMock(data=[mock_item])
        yield mock_cls


@pytest.fixture
def mock_collection():
    """ChromaDB 컬렉션 Mock."""
    with patch("backend.retrieval.retrieval_agent.get_collection") as mock_fn:
        col = MagicMock()
        col.count.return_value = 10
        col.query.return_value = _make_chroma_response(
            ["청크 A", "청크 B", "청크 C"],
            [0.10, 0.25, 0.40],
        )
        mock_fn.return_value = col
        yield col


class TestRetrievalAgentRun:
    def test_returns_success_structure(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": "테스트 질문"})

        assert result["success"] is True
        assert result["error"] is None
        assert "chunks" in result["data"]

    def test_returns_list_of_chunks(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": "테스트"})

        assert isinstance(result["data"]["chunks"], list)

    def test_each_chunk_has_required_fields(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": "테스트"})
        chunk = result["data"]["chunks"][0]

        assert "chunk_text" in chunk
        assert "source_file" in chunk
        assert "chunk_index" in chunk
        assert "distance" in chunk

    def test_chunk_count_matches_mock_response(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": "테스트"})

        assert len(result["data"]["chunks"]) == 3

    def test_distance_values_correct(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": "테스트"})
        distances = [c["distance"] for c in result["data"]["chunks"]]

        assert distances == [0.10, 0.25, 0.40]

    def test_missing_query_returns_error(self) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({})

        assert result["success"] is False
        assert result["error"] is not None

    def test_empty_query_returns_error(self) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        result = RetrievalAgent().run({"query": ""})

        assert result["success"] is False

    def test_empty_collection_returns_empty_list(self, mock_openai_embed: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        with patch("backend.retrieval.retrieval_agent.get_collection") as mock_fn:
            col = MagicMock()
            col.count.return_value = 0
            mock_fn.return_value = col

            result = RetrievalAgent().run({"query": "테스트"})

        assert result["success"] is True
        assert result["data"]["chunks"] == []
        col.query.assert_not_called()

    def test_embed_called_with_query(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        RetrievalAgent().run({"query": "정확한 질문"})

        _, kwargs = mock_openai_embed.return_value.embeddings.create.call_args
        assert kwargs["input"] == ["정확한 질문"]

    def test_chroma_queried_with_embedding(self, mock_openai_embed: MagicMock, mock_collection: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        RetrievalAgent().run({"query": "테스트"})

        mock_collection.query.assert_called_once()
        _, kwargs = mock_collection.query.call_args
        assert kwargs["query_embeddings"] == [[0.1] * 1536]

    def test_k_param_limits_results(self, mock_openai_embed: MagicMock) -> None:
        from backend.retrieval.retrieval_agent import RetrievalAgent

        with patch("backend.retrieval.retrieval_agent.get_collection") as mock_fn:
            col = MagicMock()
            col.count.return_value = 20
            col.query.return_value = _make_chroma_response(["A", "B"], [0.1, 0.2])
            mock_fn.return_value = col

            RetrievalAgent().run({"query": "테스트", "k": 2})

        _, kwargs = col.query.call_args
        assert kwargs["n_results"] == 2
