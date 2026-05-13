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

_SYSTEM_PROMPT_WITH_WEB = (
    "당신은 사내 문서 기반 AI 비서입니다.\n"
    "제공된 사내 문서를 우선적으로 활용하고, 웹 검색 결과로 내용을 보완하여 답변하십시오.\n"
    "사내 문서 내용과 웹 정보를 명확히 구분하여 출처를 밝혀주십시오.\n"
    "추측은 하지 말고 제공된 정보에만 근거하여 답변하십시오."
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
        web_results: List[Dict] = payload.get("web_results", [])
        memory_context: List[Dict] = payload.get("memory_context", [])

        if not query:
            raise ValueError("payload에 'query' 키가 필요합니다.")

        if not chunks and not web_results:
            return {"answer": _NOT_FOUND, "sources": []}

        context = self._build_context(chunks, web_results)
        base_prompt = _SYSTEM_PROMPT_WITH_WEB if web_results else _SYSTEM_PROMPT
        system_prompt = self._build_system_prompt(base_prompt, memory_context)
        answer = self._call_gpt(query, context, system_prompt)
        doc_sources = list(dict.fromkeys(c["source_file"] for c in chunks))
        web_sources = [r["link"] for r in web_results if r.get("link")]

        return {"answer": answer, "sources": doc_sources, "web_sources": web_sources}

    def _build_system_prompt(self, base_prompt: str, memory_context: List[Dict]) -> str:
        if not memory_context:
            return base_prompt
        snippets = "\n".join(f"- {m['document'][:300]}" for m in memory_context)
        return f"{base_prompt}\n\n[과거 유사 대화 참고]\n{snippets}"

    def _build_context(self, chunks: List[Dict], web_results: List[Dict]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[사내 문서 {i}] 출처: {chunk.get('source_file', '알 수 없음')}\n{chunk['chunk_text']}")

        for i, item in enumerate(web_results, 1):
            parts.append(
                f"[웹 검색 {i}] 제목: {item.get('title', '')}\n"
                f"출처: {item.get('link', '')}\n"
                f"{item.get('description', '')}"
            )
        return "\n\n---\n\n".join(parts)

    def _call_gpt(self, query: str, context: str, system_prompt: str) -> str:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=GPT_MODEL,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
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
