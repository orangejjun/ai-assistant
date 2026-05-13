import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

_HISTORY_DIR = Path("data/history")


def _ensure_dir() -> None:
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def save_session(session_id: str, messages: List[Dict]) -> None:
    _ensure_dir()
    path = _HISTORY_DIR / f"{session_id}.json"
    payload = {
        "session_id": session_id,
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
            sessions.append({
                "session_id": data.get("session_id", p.stem),
                "updated_at": data.get("updated_at", ""),
                "preview": _preview(data.get("messages", [])),
            })
        except Exception:
            continue
    return sessions


def delete_session(session_id: str) -> bool:
    path = _HISTORY_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def _preview(messages: List[Dict]) -> str:
    for m in messages:
        if m.get("role") == "user":
            return m.get("content", "")[:40]
    return ""


if __name__ == "__main__":
    sid = new_session_id()
    save_session(sid, [{"role": "user", "content": "테스트 질문"}, {"role": "assistant", "content": "테스트 답변"}])
    print(f"저장된 세션: {sid}")
    print(list_sessions())
