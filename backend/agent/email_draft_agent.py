import json
import os

from openai import OpenAI

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 4096

_SYSTEM_PROMPT = """당신은 사내 비즈니스 이메일 작성 전문가입니다.
사용자가 채팅으로 설명하는 이메일 목적과 내용을 바탕으로 간결하고 명확한 비즈니스 이메일을 작성하십시오.

규칙:
- 핵심만 담아 간결하게 작성 (불필요한 미사여구 배제)
- 경어체 사용, 정중하되 군더더기 없이
- 참고 사내 문서가 있으면 내용에 반영할 것
- 사실관계가 불명확한 부분은 [확인 필요] 태그를 붙일 것

반드시 아래 JSON 형식으로만 응답하십시오:
{
  "subject": "이메일 제목",
  "body": "이메일 본문 (줄바꿈은 \\n 사용)"
}"""


class EmailDraftAgent:
    """멀티턴 채팅 이력을 받아 RAG 컨텍스트 기반으로 이메일 초안을 생성하는 에이전트."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        messages: list[dict] = payload.get("messages", [])
        if not messages:
            raise ValueError("payload에 'messages' 키가 필요합니다.")

        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        chunks = self._retrieve(last_user_msg)
        draft = self._generate_draft(messages, chunks)
        sources = list(dict.fromkeys(c["source_file"] for c in chunks if c["source_file"]))
        return {"subject": draft["subject"], "body": draft["body"], "sources": sources}

    def _retrieve(self, query: str) -> list[dict]:
        if not query:
            return []
        agent = RetrievalAgent()
        result = agent.run({"query": query, "k": 3})
        if not result["success"]:
            return []
        return result["data"]["chunks"]

    def _generate_draft(self, messages: list[dict], chunks: list[dict]) -> dict:
        system_prompt = _SYSTEM_PROMPT
        if chunks:
            context = "\n\n".join(
                f"[사내 문서 {i}] 출처: {c['source_file']}\n{c['chunk_text'][:500]}"
                for i, c in enumerate(chunks, 1)
            )
            system_prompt += f"\n\n[참고 가능한 사내 문서]\n{context}"

        chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-10:]
        ]

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system_prompt}] + chat_history,
        )
        return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = EmailDraftAgent()
    result = agent.run(
        {
            "messages": [
                {"role": "user", "content": "가격 정책 변경 사항을 팀장님께 보고하는 이메일을 써줘."},
            ]
        }
    )
    if result["success"]:
        data = result["data"]
        print(f"제목: {data['subject']}")
        print(f"본문:\n{data['body']}")
    else:
        print(f"오류: {result['error']}")
