import pytest

from backend.ingest.chunker import CHUNK_SIZE, OVERLAP_SIZE


class TestChunkText:
    def test_short_text_produces_single_chunk(self) -> None:
        from backend.ingest.chunker import chunk_text

        text = "짧은 텍스트"
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        assert len(result) == 1

    def test_long_text_produces_multiple_chunks(self) -> None:
        from backend.ingest.chunker import chunk_text

        text = "가" * (CHUNK_SIZE * 3)
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        assert len(result) > 1

    def test_each_chunk_within_size_limit(self) -> None:
        from backend.ingest.chunker import chunk_text

        text = "나" * (CHUNK_SIZE * 5)
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        for chunk in result:
            assert len(chunk["chunk_text"]) <= CHUNK_SIZE

    def test_overlap_exists_between_consecutive_chunks(self) -> None:
        from backend.ingest.chunker import chunk_text

        # 숫자 패턴: 중복 없는 명확한 경계 확인
        text = "".join(str(i % 10) for i in range(CHUNK_SIZE * 3))
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        assert len(result) >= 2
        tail = result[0]["chunk_text"][-OVERLAP_SIZE:]
        head = result[1]["chunk_text"][:OVERLAP_SIZE]
        assert tail == head

    def test_empty_text_returns_empty_list(self) -> None:
        from backend.ingest.chunker import chunk_text

        result = chunk_text("", source_file="f.txt", md5_hash="abc")

        assert result == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        from backend.ingest.chunker import chunk_text

        result = chunk_text("   \n\t\n   ", source_file="f.txt", md5_hash="abc")

        assert result == []

    def test_chunk_index_is_sequential(self) -> None:
        from backend.ingest.chunker import chunk_text

        text = "다" * (CHUNK_SIZE * 3)
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        indices = [c["chunk_index"] for c in result]
        assert indices == list(range(len(result)))

    def test_result_contains_required_fields(self) -> None:
        from backend.ingest.chunker import chunk_text

        result = chunk_text("테스트 텍스트", source_file="test.txt", md5_hash="deadbeef")

        assert "chunk_text" in result[0]
        assert "chunk_index" in result[0]
        assert "source_file" in result[0]
        assert "md5_hash" in result[0]

    def test_metadata_propagated_correctly(self) -> None:
        from backend.ingest.chunker import chunk_text

        result = chunk_text("메타데이터 확인", source_file="/path/to/doc.txt", md5_hash="ff00")

        assert result[0]["source_file"] == "/path/to/doc.txt"
        assert result[0]["md5_hash"] == "ff00"

    def test_preprocess_normalizes_whitespace(self) -> None:
        from backend.ingest.chunker import chunk_text

        text = "앞에   공백   중간   공백"
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        # 연속 공백이 단일 공백으로 정규화되어야 한다
        assert "   " not in result[0]["chunk_text"]

    def test_last_chunk_covers_end_of_text(self) -> None:
        from backend.ingest.chunker import chunk_text

        suffix = "마지막문장"
        text = ("가" * CHUNK_SIZE) + suffix
        result = chunk_text(text, source_file="f.txt", md5_hash="abc")

        last_chunk = result[-1]["chunk_text"]
        assert last_chunk.endswith(suffix)

    def test_chunk_count_formula(self) -> None:
        from backend.ingest.chunker import chunk_text, _split

        text = "x" * (CHUNK_SIZE + OVERLAP_SIZE + 1)
        chunks = _split(text, CHUNK_SIZE, OVERLAP_SIZE)

        # CHUNK_SIZE + OVERLAP_SIZE + 1 길이 → 정확히 2개 청크
        assert len(chunks) == 2
