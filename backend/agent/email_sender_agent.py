import uuid


class EmailSenderAgent:
    """데모용 이메일 전송 에이전트 — 실제 전송 없이 이메일 데이터를 반환한다."""

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

        return {
            "message_id": str(uuid.uuid4()),
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body,
            "attachment_names": [a["filename"] for a in attachments],
        }


if __name__ == "__main__":
    agent = EmailSenderAgent()
    result = agent.run(
        {
            "to": "demo@example.com",
            "cc": ["cc@example.com"],
            "subject": "[데모] AI 비서 이메일 테스트",
            "body": "이 메일은 데모용 이메일입니다.",
            "attachments": [],
        }
    )
    if result["success"]:
        print(f"전송 성공: {result['data']}")
    else:
        print(f"전송 실패: {result['error']}")
