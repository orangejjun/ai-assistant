import json
import os
from typing import List

from openai import OpenAI

from backend.ingest.db_manager import get_random_chunks

_GPT_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 512

_SYSTEM_PROMPT = """You are an assistant helping users discover what questions to ask about their company documents.
Given document excerpts, generate exactly 3 natural, specific questions a user might ask.
Rules:
- Write questions in the SAME language as the document excerpts
- Make questions specific to the actual content, not generic
- Each question must be under 30 characters
- Respond ONLY with a JSON object: {"questions": ["질문1", "질문2", "질문3"]}"""


class SuggestionAgent:
    """인덱싱된 문서에서 랜덤 청크를 샘플링해 추천 질문 3개를 생성하는 에이전트."""

    def run(self, payload: dict) -> dict:
        try:
            return {"success": True, "data": self._execute(), "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self) -> dict:
        chunks = get_random_chunks(k=5)
        if not chunks:
            return {"suggestions": []}

        context = "\n\n".join(
            f"[{i}] {c['chunk_text'][:400]}" for i, c in enumerate(chunks, 1)
        )
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Document excerpts:\n{context}\n\nGenerate 3 questions.",
                },
            ],
        )
        raw = json.loads(response.choices[0].message.content)
        suggestions: List[str] = (
            raw if isinstance(raw, list)
            else raw.get("questions", raw.get("suggestions", []))
        )
        return {"suggestions": suggestions[:3]}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = SuggestionAgent()
    result = agent.run({})
    if result["success"]:
        for q in result["data"]["suggestions"]:
            print(f"  • {q}")
    else:
        print(f"오류: {result['error']}")
