import json
import os
from pathlib import Path

from openai import OpenAI

from backend.retrieval.retrieval_agent import RetrievalAgent

_GPT_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 1024
_CONTACTS_PATH = Path("data/contacts.json")

_SYSTEM_PROMPT = """당신은 사내 이메일 수신자 추천 전문가입니다.
이메일 내용을 분석하여 주 수신자(To)와 참조자(CC)를 추천하십시오.

규칙:
- 반드시 제공된 contacts 목록에 있는 사람만 추천할 것
- contacts에 없는 이메일 주소는 절대 생성하지 말 것
- to_suggestion: 이 이메일의 주 수신자 1명 (직접 보고·요청 대상, 없으면 null)
- cc_suggestions: 참조할 관련 부서 담당자 목록 (여러 명 가능, 없으면 빈 배열)
- 추천 이유는 20자 이내로 간결하게

반드시 아래 JSON 형식으로만 응답하십시오:
{
  "to_suggestion": {
    "email": "담당자 이메일",
    "name": "담당자 이름",
    "team": "팀명",
    "reason": "추천 이유"
  },
  "cc_suggestions": [
    {
      "email": "담당자 이메일",
      "name": "담당자 이름",
      "team": "팀명",
      "reason": "추천 이유"
    }
  ]
}"""


class EmailRecipientAgent:
    """이메일 내용과 사내 contacts.json을 기반으로 To/CC 수신자를 추천하는 에이전트."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        subject: str = payload.get("subject", "")
        body: str = payload.get("body", "")
        if not subject and not body:
            raise ValueError("subject 또는 body가 필요합니다.")

        contacts = self._load_contacts()
        if not contacts:
            return {"to_suggestion": None, "cc_suggestions": []}

        valid_emails = {c["email"] for c in contacts}
        chunks = self._retrieve(f"{subject} {body}")
        raw = self._recommend(subject, body, contacts, chunks)

        to_sug = raw.get("to_suggestion")
        if to_sug and to_sug.get("email") not in valid_emails:
            to_sug = None

        cc_sugs = [r for r in raw.get("cc_suggestions", []) if r.get("email") in valid_emails]
        # To와 CC가 겹치지 않도록
        if to_sug:
            cc_sugs = [r for r in cc_sugs if r["email"] != to_sug["email"]]

        return {"to_suggestion": to_sug, "cc_suggestions": cc_sugs}

    def _load_contacts(self) -> list[dict]:
        if not _CONTACTS_PATH.exists():
            return []
        return json.loads(_CONTACTS_PATH.read_text(encoding="utf-8"))

    def _retrieve(self, query: str) -> list[dict]:
        agent = RetrievalAgent()
        result = agent.run({"query": query, "k": 3})
        if not result["success"]:
            return []
        return result["data"]["chunks"]

    def _recommend(
        self,
        subject: str,
        body: str,
        contacts: list[dict],
        chunks: list[dict],
    ) -> dict:
        contacts_str = json.dumps(contacts, ensure_ascii=False, indent=2)
        rag_context = "\n\n".join(
            f"[문서 {i}] {c['chunk_text'][:300]}"
            for i, c in enumerate(chunks, 1)
        )

        user_content = (
            f"이메일 제목: {subject}\n\n"
            f"이메일 본문:\n{body}\n\n"
            f"[사용 가능한 연락처 목록]\n{contacts_str}"
        )
        if rag_context:
            user_content += f"\n\n[관련 사내 문서 발췌]\n{rag_context}"
        user_content += "\n\n이메일의 주 수신자(To) 1명과 참조(CC) 담당자를 contacts 목록에서만 선택하여 추천해 주세요."

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = EmailRecipientAgent()
    result = agent.run(
        {
            "subject": "가격 정책 변경 보고",
            "body": "이번 분기 가격 정책 변경 사항과 올리브영 채널 영향도를 공유드립니다.",
        }
    )
    if result["success"]:
        data = result["data"]
        to_sug = data.get("to_suggestion")
        if to_sug:
            print(f"To: {to_sug['name']} ({to_sug['team']}) — {to_sug['reason']}")
        for r in data.get("cc_suggestions", []):
            print(f"CC: {r['name']} ({r['team']}) — {r['reason']}")
    else:
        print(f"오류: {result['error']}")
