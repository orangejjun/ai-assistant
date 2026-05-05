import os
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


def get_stats() -> Dict:
    collection = get_collection()
    return {"collection": COLLECTION_NAME, "total_chunks": collection.count()}


if __name__ == "__main__":
    stats = get_stats()
    print(f"컬렉션: {stats['collection']}")
    print(f"저장된 총 청크: {stats['total_chunks']}개")
