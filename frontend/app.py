import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AI 문서 비서", page_icon="📚", layout="wide")

# ── 세션 상태 초기화 ─────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _get_status() -> dict | None:
    try:
        res = requests.get(f"{API_BASE}/status", timeout=3)
        if res.ok:
            return res.json().get("data")
    except requests.exceptions.ConnectionError:
        pass
    return None


def _run_ingest(folder_path: str) -> dict:
    res = requests.post(
        f"{API_BASE}/ingest",
        json={"folder_path": folder_path},
        timeout=300,
    )
    res.raise_for_status()
    return res.json()


def _run_query(query: str) -> dict:
    res = requests.post(
        f"{API_BASE}/query",
        json={"query": query},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def _upload_file(file) -> dict:
    res = requests.post(
        f"{API_BASE}/upload",
        files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
        timeout=300,
    )
    res.raise_for_status()
    return res.json()


# ── 사이드바 ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📁 문서 인덱싱")

    status = _get_status()
    if status:
        st.metric("저장된 청크 수", status.get("total_chunks", 0))
    else:
        st.warning("⚠️ 백엔드에 연결할 수 없습니다.\n`uvicorn backend.api.main:app --reload` 를 실행하세요.")

    st.divider()

    folder_path = st.text_input("스캔할 폴더 경로", value="data/raw", placeholder="data/raw")

    if st.button("🔄 인덱싱 실행", type="primary", use_container_width=True):
        with st.spinner("문서를 인덱싱 중입니다..."):
            try:
                result = _run_ingest(folder_path)
                if result.get("success"):
                    data = result["data"]
                    if data["processed_files"] == 0:
                        st.info("처리할 새 파일이 없습니다.")
                    else:
                        st.success(
                            f"✅ 완료\n\n"
                            f"- 처리 파일: **{data['processed_files']}개**\n"
                            f"- 신규 청크: **{data['total_chunks']}개**\n"
                            f"- DB 누적 청크: **{data['db_total_chunks']}개**"
                        )
                    st.rerun()
                else:
                    st.error(f"오류: {result.get('error')}")
            except requests.exceptions.ConnectionError:
                st.error("백엔드에 연결할 수 없습니다.")
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")

    st.divider()
    st.subheader("📤 파일 업로드")

    uploaded = st.file_uploader(
        "파일 선택",
        type=["pdf", "docx", "txt", "xlsx"],
        help="업로드하면 즉시 임베딩 후 벡터DB에 저장됩니다.",
    )

    if uploaded and st.button("업로드 & 인덱싱", type="primary", use_container_width=True):
        with st.spinner(f"{uploaded.name} 인덱싱 중..."):
            try:
                result = _upload_file(uploaded)
                if result.get("success"):
                    d = result["data"]
                    if d.get("duplicate"):
                        st.warning("⚠️ 이미 인덱싱된 파일입니다.")
                    else:
                        st.success(
                            f"✅ 완료\n\n"
                            f"- 파일명: **{d['filename']}**\n"
                            f"- 신규 청크: **{d['chunks']}개**\n"
                            f"- DB 누적 청크: **{d['db_total_chunks']}개**"
                        )
                    st.rerun()
                else:
                    st.error(f"오류: {result.get('error')}")
            except requests.exceptions.ConnectionError:
                st.error("백엔드에 연결할 수 없습니다.")
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── 메인 채팅 인터페이스 ───────────────────────────────────────────────────────

st.title("📚 AI 문서 비서")
st.caption("사내 문서를 기반으로 질문에 답변합니다.")

# 채팅 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 출처 보기"):
                for src in msg["sources"]:
                    st.caption(f"📄 {src}")

# 질문 입력
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("답변을 생성하는 중입니다..."):
            try:
                result = _run_query(prompt)

                if result.get("success"):
                    data = result["data"]
                    answer = data["answer"]
                    sources = data.get("sources", [])

                    st.write(answer)

                    if sources:
                        with st.expander("📎 출처 보기"):
                            for src in sources:
                                st.caption(f"📄 {src}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                else:
                    error_msg = f"오류가 발생했습니다: {result.get('error', '알 수 없는 오류')}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                    })

            except requests.exceptions.ConnectionError:
                msg = "백엔드에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
                st.error(msg)
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"서버 오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")
