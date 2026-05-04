from unittest.mock import patch, MagicMock, call

import pytest

from backend.ingest.embedder import EMBED_MODEL, BATCH_SIZE


def _make_mock_response(texts: list[str], base_val: float = 0.1) -> MagicMock:
    """n개 텍스트에 대응하는 OpenAI 임베딩 응답 Mock을 생성한다."""
    items = [
        MagicMock(embedding=[base_val] * 1536, index=i)
        for i in range(len(texts))
    ]
    return MagicMock(data=items)


class TestEmbedTexts:
    @patch("backend.ingest.embedder.OpenAI")
    def test_returns_correct_count(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        texts = ["텍스트 A", "텍스트 B", "텍스트 C"]
        mock_openai_cls.return_value.embeddings.create.return_value = (
            _make_mock_response(texts)
        )

        result = embed_texts(texts)

        assert len(result) == 3

    @patch("backend.ingest.embedder.OpenAI")
    def test_vector_dimension_is_1536(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        texts = ["차원 확인용 텍스트"]
        mock_openai_cls.return_value.embeddings.create.return_value = (
            _make_mock_response(texts)
        )

        result = embed_texts(texts)

        assert len(result[0]) == 1536

    @patch("backend.ingest.embedder.OpenAI")
    def test_uses_correct_model(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        texts = ["모델 확인"]
        mock_client = mock_openai_cls.return_value
        mock_client.embeddings.create.return_value = _make_mock_response(texts)

        embed_texts(texts)

        _, kwargs = mock_client.embeddings.create.call_args
        assert kwargs["model"] == EMBED_MODEL

    @patch("backend.ingest.embedder.OpenAI")
    def test_passes_texts_to_api(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        texts = ["첫 문장", "둘째 문장"]
        mock_client = mock_openai_cls.return_value
        mock_client.embeddings.create.return_value = _make_mock_response(texts)

        embed_texts(texts)

        _, kwargs = mock_client.embeddings.create.call_args
        assert kwargs["input"] == texts

    @patch("backend.ingest.embedder.OpenAI")
    def test_empty_input_returns_empty_list(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        result = embed_texts([])

        mock_openai_cls.return_value.embeddings.create.assert_not_called()
        assert result == []

    @patch("backend.ingest.embedder.OpenAI")
    def test_batch_processing_calls_api_twice(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        texts = [f"텍스트 {i}" for i in range(BATCH_SIZE + 10)]
        mock_client = mock_openai_cls.return_value

        first_batch = _make_mock_response(texts[:BATCH_SIZE])
        second_batch = _make_mock_response(texts[BATCH_SIZE:])
        mock_client.embeddings.create.side_effect = [first_batch, second_batch]

        result = embed_texts(texts)

        assert mock_client.embeddings.create.call_count == 2
        assert len(result) == len(texts)

    @patch("backend.ingest.embedder.OpenAI")
    def test_batch_total_vector_count_matches_input(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        count = BATCH_SIZE * 2 + 5
        texts = [f"t{i}" for i in range(count)]
        mock_client = mock_openai_cls.return_value

        batches = [
            _make_mock_response(texts[i : i + BATCH_SIZE])
            for i in range(0, count, BATCH_SIZE)
        ]
        mock_client.embeddings.create.side_effect = batches

        result = embed_texts(texts)

        assert len(result) == count

    @patch("backend.ingest.embedder.OpenAI")
    def test_uses_env_api_key(self, mock_openai_cls: MagicMock) -> None:
        from backend.ingest.embedder import embed_texts

        mock_openai_cls.return_value.embeddings.create.return_value = (
            _make_mock_response(["키 확인"])
        )

        embed_texts(["키 확인"])

        mock_openai_cls.assert_called_once_with(api_key="test-openai-key")
