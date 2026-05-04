import os
from typing import Any, List, Dict

from openai import OpenAI

GPT_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "당신은 사내 문서 기반 AI 비서입니다.\n"
    "제공된 문서에서 관련 내용을 최대한 활용하여 답변하십시오.\n"
    "부분적으로 관련된 내용도 적극적으로 활용하여 도움이 되는 답변을 생성하십시오.\n"
    "문서와 전혀 관련 없는 질문인 경우에만 '문서에서 찾을 수 없습니다.'라고 답변하십시오.\n"
    "추측이나 외부 지식을 사용하지 마십시오."
)

_NOT_FOUND = "문서에서 찾을 수 없습니다."


class AnswerAgent:
    """검색된 청크를 컨텍스트로 조합하여 OpenAI GPT로 답변을 생성한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        query: str = payload.get("query", "")
        chunks: List[Dict] = payload.get("chunks", [])

        if not query:
            raise ValueError("payload에 'query' 키가 필요합니다.")

        if not chunks:
            return {"answer": _NOT_FOUND, "sources": []}

        context = self._build_context(chunks)
        answer = self._call_gpt(query, context)
        # dict.fromkeys: 순서 유지하면서 중복 제거
        sources = list(dict.fromkeys(c["source_file"] for c in chunks))

        return {"answer": answer, "sources": sources}

    def _build_context(self, chunks: List[Dict]) -> str:
        parts = [
            f"[문서 {i}] 출처: {chunk.get('source_file', '알 수 없음')}\n{chunk['chunk_text']}"
            for i, chunk in enumerate(chunks, 1)
        ]
        return "\n\n---\n\n".join(parts)

    def _call_gpt(self, query: str, context: str) -> str:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=GPT_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"[참고 문서]\n{context}\n\n[질문]\n{query}"},
            ],
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = AnswerAgent()
    test_chunks = [
        {
            "chunk_text": "연차 유급휴가 사용 시 최소 3일 전에 신청하여야 한다.",
            "source_file": "data/raw/규정.txt",
            "chunk_index": 0,
            "distance": 0.12,
        }
    ]
    result = agent.run({"query": "연차 신청은 며칠 전에 해야 하나요?", "chunks": test_chunks})
    print(result)
