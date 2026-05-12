import os
import uuid

import resend


class EmailSenderAgent:
    """Resend API를 사용해 이메일을 실제 발송하는 에이전트."""

    def run(self, payload: dict) -> dict:
        try:
            result = self._execute(payload)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _execute(self, payload: dict) -> dict:
        to: str = payload.get("to", "").strip()
        cc: list[str] = [addr.strip() for addr in payload.get("cc", []) if addr.strip()]
        subject: str = payload.get("subject", "").strip()
        body: str = payload.get("body", "")
        attachments: list[dict] = payload.get("attachments", [])

        if not to:
            raise ValueError("수신자(to)가 비어 있습니다.")
        if not subject:
            raise ValueError("제목(subject)이 비어 있습니다.")

        api_key = os.getenv("RESEND_API_KEY", "")
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        if not api_key:
            raise ValueError("RESEND_API_KEY 환경변수가 필요합니다.")

        resend.api_key = api_key

        params: resend.Emails.SendParams = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "text": body,
        }
        if cc:
            params["cc"] = cc
        if attachments:
            params["attachments"] = [
                {"filename": att["filename"], "content": list(att["content"])}
                for att in attachments
            ]

        response = resend.Emails.send(params)

        return {
            "message_id": response.id if hasattr(response, "id") else str(uuid.uuid4()),
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "attachment_names": [a["filename"] for a in attachments],
        }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    agent = EmailSenderAgent()
    result = agent.run(
        {
            "to": "test@naver.com",
            "cc": [],
            "subject": "[테스트] AI 비서 이메일 발송",
            "body": "Resend API를 통한 실제 발송 테스트입니다.",
            "attachments": [],
        }
    )
    if result["success"]:
        print(f"전송 성공: {result['data']}")
    else:
        print(f"전송 실패: {result['error']}")
