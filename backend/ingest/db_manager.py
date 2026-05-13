import os
import random
import uuid
from typing import List, Dict

import chromadb

COLLECTION_NAME = "doc_assistant"
_DEFAULT_DB_PATH = "data/vectordb"


def _get_client() -> chromadb.PersistentClient:
    db_path = os.getenv("VECTORDB_PATH", _DEFAULT_DB_PATH)
    return chromadb.PersistentClient(path=db_path)


def get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def save_chunks(chunks: List[Dict], embeddings: List[List[float]]) -> int:
    """
    청크와 임베딩을 ChromaDB에 저장(upsert)한다.

    Args:
        chunks: chunker.py 출력 (chunk_text, chunk_index, source_file, md5_hash)
        embeddings: embedder.py 출력 (각 청크에 대응하는 벡터)

    Returns:
        int: 저장된 청크 수
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"청크 수({len(chunks)})와 임베딩 수({len(embeddings)}) 불일치"
        )

    collection = get_collection()

    # ID: md5_hash + chunk_index 조합으로 동일 파일 재처리 시 upsert 보장
    ids = [f"{c['md5_hash']}_{c['chunk_index']}" for c in chunks]
    documents = [c["chunk_text"] for c in chunks]
    metadatas = [
        {
            "source_file": c["source_file"],
            "chunk_index": c["chunk_index"],
            "md5_hash": c["md5_hash"],
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(chunks)


def delete_by_source_file(source_file: str) -> int:
    """source_file 메타데이터 기준으로 해당 파일의 모든 청크를 삭제하고 삭제된 수를 반환한다."""
    collection = get_collection()
    result = collection.get(where={"source_file": source_file})
    ids = result["ids"]
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def reset_collection() -> None:
    """기존 컬렉션을 삭제하고 새로 생성한다. 재인덱싱 시 사용한다."""
    client = _get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def get_random_chunks(k: int = 5) -> List[Dict]:
    """ChromaDB에서 랜덤 오프셋으로 k개 청크를 샘플링해 반환한다."""
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []
    offset = random.randint(0, max(0, total - k))
    result = collection.get(
        limit=k,
        offset=offset,
        include=["documents", "metadatas"],
    )
    return [
        {"chunk_text": doc, "source_file": meta.get("source_file", "")}
        for doc, meta in zip(result["documents"], result["metadatas"])
    ]


def get_memory_collection() -> chromadb.Collection:
    """대화 메모리 전용 ChromaDB 컬렉션을 반환한다."""
    client = _get_client()
    return client.get_or_create_collection(
        name="conversation_memory",
        metadata={"hnsw:space": "cosine"},
    )


def save_memory_pair(
    session_id: str,
    query: str,
    answer: str,
    embedding: List[float],
) -> None:
    """Q&A 쌍을 conversation_memory 컬렉션에 upsert한다."""
    collection = get_memory_collection()
    doc_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
    collection.upsert(
        ids=[doc_id],
        documents=[f"Q: {query}\nA: {answer}"],
        embeddings=[embedding],
        metadatas=[{"session_id": session_id, "query": query[:200]}],
    )


def search_memory(embedding: List[float], k: int = 3) -> List[Dict]:
    """임베딩 벡터로 과거 유사 Q&A를 검색한다. distance < 0.6 인 결과만 반환."""
    collection = get_memory_collection()
    total = collection.count()
    if total == 0:
        return []
    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(k, total),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "document": doc,
            "session_id": meta.get("session_id", ""),
            "distance": dist,
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
        if dist < 0.6
    ]


def get_stats() -> Dict:
    collection = get_collection()
    return {"collection": COLLECTION_NAME, "total_chunks": collection.count()}


if __name__ == "__main__":
    stats = get_stats()
    print(f"컬렉션: {stats['collection']}")
    print(f"저장된 총 청크: {stats['total_chunks']}개")
