import os
from typing import Any, List, Dict

from openai import OpenAI
from backend.ingest.db_manager import get_collection

_EMBED_MODEL = "text-embedding-3-small"
TOP_K = 5


class RetrievalAgent:
    """사용자 질의를 임베딩 후 ChromaDB에서 유사 청크를 검색한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        query: str = payload.get("query", "")
        if not query:
            raise ValueError("payload에 'query' 키가 필요합니다.")

        k: int = payload.get("k", TOP_K)
        embedding = self._embed_query(query)
        chunks = self._search(embedding, k)
        return {"chunks": chunks}

    def _embed_query(self, query: str) -> List[float]:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(model=_EMBED_MODEL, input=[query])
        return response.data[0].embedding

    def _search(self, embedding: List[float], k: int) -> List[Dict]:
        collection = get_collection()

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
                "chunk_text": doc,
                "source_file": meta.get("source_file", ""),
                "chunk_index": int(meta.get("chunk_index", 0)),
                "distance": dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = RetrievalAgent()
    result = agent.run({"query": "연차 휴가 신청 방법"})
    if result["success"]:
        for chunk in result["data"]["chunks"]:
            print(f"  [{chunk['distance']:.4f}] {chunk['chunk_text'][:80]}")
    else:
        print(f"오류: {result['error']}")
