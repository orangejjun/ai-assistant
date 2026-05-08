import json
import os
from typing import Dict, List

from openai import OpenAI

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "당신은 프로젝트 관리 전문가입니다.\n"
    "제공된 사내 문서와 대화 내역을 참고하여 실행 가능한 프로젝트 플랜을 작성하십시오.\n"
    "문서에 없는 내용은 추측하지 마십시오.\n\n"
    "반드시 아래 JSON 형식으로만 응답하십시오:\n"
    "{\n"
    '  "title": "플랜 제목",\n'
    '  "phases": [\n'
    "    {\n"
    '      "name": "Phase 1: 명칭",\n'
    '      "duration": "예상 기간",\n'
    '      "tasks": [\n'
    '        {"text": "태스크 설명"},\n'
    "        ...\n"
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}"
)


class PlanAgent:
    """문서 컨텍스트와 채팅 히스토리를 바탕으로 인터랙티브 TODO 플랜 구조를 생성한다."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        goal: str = payload.get("goal", "")
        chat_history: List[Dict] = payload.get("chat_history", [])

        if not goal:
            raise ValueError("payload에 'goal' 키가 필요합니다.")

        chunks = self._retrieve(goal)
        plan = self._generate_plan(goal, chunks, chat_history)
        sources = list(dict.fromkeys(c["source_file"] for c in chunks))

        return {"plan": plan, "sources": sources}

    def _retrieve(self, goal: str) -> List[Dict]:
        agent = RetrievalAgent()
        result = agent.run({"query": goal, "k": 5})
        if not result["success"]:
            return []
        return result["data"]["chunks"]

    def _generate_plan(self, goal: str, chunks: List[Dict], chat_history: List[Dict]) -> dict:
        context = "\n\n".join(
            f"[문서 {i}] 출처: {c['source_file']}\n{c['chunk_text']}"
            for i, c in enumerate(chunks, 1)
        )

        history_text = ""
        if chat_history:
            lines = [
                f"{'사용자' if m['role'] == 'user' else '비서'}: {m['content']}"
                for m in chat_history[-10:]
            ]
            history_text = "\n[대화 내역]\n" + "\n".join(lines)

        user_message = (
            f"프로젝트 목표: {goal}\n\n"
            f"[참고 문서]\n{context}"
            f"{history_text}\n\n"
            "위 내용을 바탕으로 실행 가능한 프로젝트 플랜을 JSON 형식으로 작성해 주세요."
        )

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = PlanAgent()
    result = agent.run({"goal": "REM 수면 연구 프로젝트 계획"})
    if result["success"]:
        import pprint
        pprint.pprint(result["data"]["plan"])
    else:
        print("오류:", result["error"])
