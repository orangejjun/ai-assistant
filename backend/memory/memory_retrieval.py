import os
from typing import Dict, List

from openai import OpenAI

from backend.ingest.db_manager import save_memory_pair, search_memory

_EMBED_MODEL = "text-embedding-3-small"


def _embed(text: str) -> List[float]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client.embeddings.create(input=text, model=_EMBED_MODEL).data[0].embedding


def index_qa_pair(session_id: str, query: str, answer: str) -> None:
    """Q&A 쌍을 임베딩하여 conversation_memory 컬렉션에 저장한다."""
    embedding = _embed(f"Q: {query}\nA: {answer}")
    save_memory_pair(session_id, query, answer, embedding)


def retrieve_relevant_memory(query: str, k: int = 3) -> List[Dict]:
    """질의 임베딩으로 과거 유사 Q&A를 검색하여 반환한다."""
    embedding = _embed(query)
    return search_memory(embedding, k=k)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    index_qa_pair("test_session", "연차는 몇 일인가요?", "연차는 15일입니다.")
    results = retrieve_relevant_memory("휴가 일수가 궁금합니다.")
    for r in results:
        print(f"[{r['distance']:.3f}] {r['document'][:80]}")
