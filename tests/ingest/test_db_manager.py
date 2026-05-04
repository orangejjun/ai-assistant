from pathlib import Path
from typing import List

import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트마다 tmp_path 기반 독립 ChromaDB 디렉토리를 사용한다.
    EphemeralClient는 내부 싱글턴을 공유하므로 PersistentClient + 고유 경로로 격리한다."""
    monkeypatch.setenv("VECTORDB_PATH", str(tmp_path / "chroma"))


def _make_chunks(n: int, md5: str = "testhash") -> List[dict]:
    return [
        {
            "chunk_text": f"청크 내용 {i}번",
            "chunk_index": i,
            "source_file": "/data/raw/test.txt",
            "md5_hash": md5,
        }
        for i in range(n)
    ]


def _make_embeddings(n: int, dim: int = 8) -> List[List[float]]:
    return [[float(i) / 100] * dim for i in range(n)]


class TestSaveChunks:
    def test_returns_saved_count(self) -> None:
        from backend.ingest.db_manager import save_chunks

        chunks = _make_chunks(3)
        embeddings = _make_embeddings(3)

        result = save_chunks(chunks, embeddings)

        assert result == 3

    def test_persists_to_collection(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_stats

        chunks = _make_chunks(4)
        embeddings = _make_embeddings(4)

        save_chunks(chunks, embeddings)

        stats = get_stats()
        assert stats["total_chunks"] == 4

    def test_mismatched_lengths_raises_value_error(self) -> None:
        from backend.ingest.db_manager import save_chunks

        with pytest.raises(ValueError, match="불일치"):
            save_chunks(_make_chunks(3), _make_embeddings(2))

    def test_upsert_is_idempotent(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_stats

        chunks = _make_chunks(3)
        embeddings = _make_embeddings(3)

        save_chunks(chunks, embeddings)
        save_chunks(chunks, embeddings)  # 동일 데이터 재저장

        # upsert이므로 중복 없이 3개 유지
        assert get_stats()["total_chunks"] == 3

    def test_saves_chunk_text_as_document(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_collection

        chunks = _make_chunks(1)
        embeddings = _make_embeddings(1)
        save_chunks(chunks, embeddings)

        col = get_collection()
        docs = col.get(include=["documents"])
        assert chunks[0]["chunk_text"] in docs["documents"]

    def test_saves_metadata_fields(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_collection

        chunks = _make_chunks(1)
        embeddings = _make_embeddings(1)
        save_chunks(chunks, embeddings)

        col = get_collection()
        result = col.get(include=["metadatas"])
        meta = result["metadatas"][0]

        assert meta["source_file"] == "/data/raw/test.txt"
        assert meta["chunk_index"] == 0
        assert meta["md5_hash"] == "testhash"

    def test_id_format_is_hash_plus_index(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_collection

        chunks = _make_chunks(2, md5="abc123")
        embeddings = _make_embeddings(2)
        save_chunks(chunks, embeddings)

        col = get_collection()
        result = col.get()
        ids = sorted(result["ids"])

        assert "abc123_0" in ids
        assert "abc123_1" in ids

    def test_multiple_files_stored_independently(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_stats

        chunks_a = _make_chunks(2, md5="file_a_hash")
        chunks_b = _make_chunks(3, md5="file_b_hash")

        save_chunks(chunks_a, _make_embeddings(2))
        save_chunks(chunks_b, _make_embeddings(3))

        assert get_stats()["total_chunks"] == 5


class TestGetCollection:
    def test_returns_collection_with_correct_name(self) -> None:
        from backend.ingest.db_manager import get_collection, COLLECTION_NAME

        col = get_collection()

        assert col.name == COLLECTION_NAME

    def test_get_or_create_is_idempotent(self) -> None:
        from backend.ingest.db_manager import get_collection

        col1 = get_collection()
        col2 = get_collection()

        assert col1.name == col2.name


class TestGetStats:
    def test_returns_required_keys(self) -> None:
        from backend.ingest.db_manager import get_stats

        stats = get_stats()

        assert "collection" in stats
        assert "total_chunks" in stats

    def test_collection_name_correct(self) -> None:
        from backend.ingest.db_manager import get_stats, COLLECTION_NAME

        stats = get_stats()

        assert stats["collection"] == COLLECTION_NAME

    def test_count_zero_for_empty_collection(self) -> None:
        from backend.ingest.db_manager import get_stats

        stats = get_stats()

        assert stats["total_chunks"] == 0

    def test_count_increases_after_save(self) -> None:
        from backend.ingest.db_manager import save_chunks, get_stats

        save_chunks(_make_chunks(5), _make_embeddings(5))

        assert get_stats()["total_chunks"] == 5
