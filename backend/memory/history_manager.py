import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from openai import OpenAI

_HISTORY_DIR = Path("data/history")
_GPT_MODEL = "gpt-4o-mini"


def _ensure_dir() -> None:
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def generate_title(messages: List[Dict]) -> str:
    """첫 번째 사용자 메시지로부터 15자 이내 제목을 GPT로 생성한다."""
    first_user = next((m["content"] for m in messages if m.get("role") == "user"), "")
    if not first_user:
        return "새 대화"
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=_GPT_MODEL,
            max_tokens=20,
            messages=[
                {"role": "system", "content": "주어진 질문을 대화 제목으로 15자 이내 한국어로 요약하라. 제목만 출력하고 따옴표·부호는 붙이지 마라."},
                {"role": "user", "content": first_user[:300]},
            ],
        )
        return resp.choices[0].message.content.strip()[:20]
    except Exception:
        return first_user[:15] or "새 대화"


def save_session(session_id: str, messages: List[Dict]) -> None:
    _ensure_dir()
    path = _HISTORY_DIR / f"{session_id}.json"

    existing_title: str = ""
    if path.exists():
        try:
            existing_title = json.loads(path.read_text(encoding="utf-8")).get("title", "")
        except Exception:
            pass

    # 첫 Q&A가 완성된 시점에 한 번만 제목 자동 생성
    if not existing_title and len(messages) >= 2:
        existing_title = generate_title(messages)

    payload = {
        "session_id": session_id,
        "title": existing_title,
        "updated_at": datetime.utcnow().isoformat(),
        "messages": messages,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_session(session_id: str) -> Dict:
    path = _HISTORY_DIR / f"{session_id}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions() -> List[Dict]:
    _ensure_dir()
    sessions = []
    for p in sorted(_HISTORY_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            msgs = data.get("messages", [])
            sessions.append({
                "session_id": data.get("session_id", p.stem),
                "title": data.get("title") or _preview(msgs),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(msgs),
            })
        except Exception:
            continue
    return sessions


def rename_session(session_id: str, title: str) -> bool:
    path = _HISTORY_DIR / f"{session_id}.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    data["title"] = title.strip()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def delete_session(session_id: str) -> bool:
    path = _HISTORY_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def _preview(messages: List[Dict]) -> str:
    for m in messages:
        if m.get("role") == "user":
            return m.get("content", "")[:20]
    return "새 대화"


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sid = new_session_id()
    save_session(sid, [{"role": "user", "content": "연차 휴가 신청 방법이 궁금합니다"}, {"role": "assistant", "content": "연차는 3일 전 신청입니다."}])
    print(f"저장된 세션: {sid}")
    for s in list_sessions():
        print(s)
