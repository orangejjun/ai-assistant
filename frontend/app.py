import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AI 문서 비서", page_icon="📚", layout="wide")

# ── 세션 상태 초기화 ─────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan_data" not in st.session_state:
    st.session_state.plan_data = None


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _get_status() -> dict | None:
    try:
        res = requests.get(f"{API_BASE}/status", timeout=3)
        if res.ok:
            return res.json().get("data")
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
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


def _run_query(query: str, use_web_search: bool = False) -> dict:
    res = requests.post(
        f"{API_BASE}/query",
        json={"query": query, "use_web_search": use_web_search},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def _list_files() -> list:
    try:
        res = requests.get(f"{API_BASE}/files", timeout=5)
        if res.ok:
            return res.json().get("data", {}).get("files", [])
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        pass
    return []


def _delete_file(source_file: str) -> dict:
    res = requests.delete(
        f"{API_BASE}/files",
        json={"source_file": source_file},
        timeout=30,
    )
    res.raise_for_status()
    return res.json()


def _create_poster(topic: str) -> dict:
    res = requests.post(
        f"{API_BASE}/poster",
        json={"topic": topic},
        timeout=180,
    )
    res.raise_for_status()
    return res.json()


def _create_plan(goal: str, chat_history: list) -> dict:
    res = requests.post(
        f"{API_BASE}/plan",
        json={"goal": goal, "chat_history": chat_history},
        timeout=120,
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
    st.subheader("🗂️ 인덱싱된 파일 관리")

    indexed_files = _list_files()
    if indexed_files:
        file_options = {f["filename"]: f["source_file"] for f in indexed_files}
        selected_name = st.selectbox("삭제할 파일 선택", list(file_options.keys()))

        if st.button("🗑️ 선택 파일 삭제", type="primary", use_container_width=True):
            with st.spinner(f"{selected_name} 삭제 중..."):
                try:
                    result = _delete_file(file_options[selected_name])
                    if result.get("success"):
                        d = result["data"]
                        st.success(
                            f"✅ 삭제 완료\n\n"
                            f"- 파일명: **{d['filename']}**\n"
                            f"- 삭제된 청크: **{d['deleted_chunks']}개**\n"
                            f"- 이동 경로: `{d['moved_to'] or '파일 없음'}`"
                        )
                    else:
                        st.error(f"오류: {result.get('error')}")
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                    st.error(f"오류: {detail}")
                except Exception as e:
                    st.error(f"알 수 없는 오류: {e}")
    else:
        st.caption("인덱싱된 파일이 없습니다.")

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── 메인 탭 ──────────────────────────────────────────────────────────────────

st.title("📚 AI 문서 비서")

tab_chat, tab_poster, tab_plan = st.tabs(["💬 채팅", "🎨 포스터 생성", "📋 플랜 생성"])


# ── 탭 1: 채팅 ────────────────────────────────────────────────────────────────

with tab_chat:
    st.caption("사내 문서를 기반으로 질문에 답변합니다.")
    use_web_search = st.toggle("🌐 Naver 웹 검색 포함", value=False, help="켜면 사내 문서 검색에 Naver 웹 검색 결과를 추가합니다.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 사내 문서 출처"):
                    for src in msg["sources"]:
                        st.caption(f"📄 {src}")
            if msg.get("web_sources"):
                with st.expander("🌐 웹 출처"):
                    for link in msg["web_sources"]:
                        st.caption(link)

    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중입니다..."):
                try:
                    result = _run_query(prompt, use_web_search=use_web_search)
                    if result.get("success"):
                        data = result["data"]
                        answer = data["answer"]
                        sources = data.get("sources", [])
                        web_sources = data.get("web_sources", [])
                        st.write(answer)
                        if sources:
                            with st.expander("📎 사내 문서 출처"):
                                for src in sources:
                                    st.caption(f"📄 {src}")
                        if web_sources:
                            with st.expander("🌐 웹 출처"):
                                for link in web_sources:
                                    st.caption(link)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                            "web_sources": web_sources,
                        })
                    else:
                        error_msg = f"오류: {result.get('error', '알 수 없는 오류')}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg, "sources": [], "web_sources": []})
                except requests.exceptions.ConnectionError:
                    st.error("백엔드에 연결할 수 없습니다.")
                except requests.exceptions.HTTPError as e:
                    detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                    st.error(f"서버 오류: {detail}")
                except Exception as e:
                    st.error(f"알 수 없는 오류: {e}")


# ── 탭 2: 포스터 생성 ─────────────────────────────────────────────────────────

with tab_poster:
    st.caption("사내 문서를 기반으로 주제를 요약하는 포스터를 생성합니다.")

    topic = st.text_input("포스터 주제", placeholder="예: REM 수면 연구 요약, 2026 학회 발표 내용")

    if st.button("🎨 포스터 생성", type="primary", use_container_width=True, disabled=not topic.strip()):
        with st.spinner("포스터를 생성하는 중입니다... (약 30~60초 소요)"):
            try:
                result = _create_poster(topic)
                if result.get("success"):
                    d = result["data"]
                    import base64
                    img_bytes = base64.b64decode(d["image_b64"])
                    st.image(img_bytes, caption=d["topic"], use_container_width=True)
                    st.download_button(
                        "⬇️ 포스터 다운로드",
                        data=img_bytes,
                        file_name=f"poster_{topic[:20].replace(' ', '_')}.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                    if d.get("sources"):
                        with st.expander("📎 참고 문서"):
                            for src in d["sources"]:
                                st.caption(f"📄 {src}")
                else:
                    st.error(f"오류: {result.get('error')}")
            except requests.exceptions.ConnectionError:
                st.error("백엔드에 연결할 수 없습니다.")
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")


# ── 탭 3: 플랜 생성 ───────────────────────────────────────────────────────────

def _plan_to_markdown(plan: dict) -> str:
    lines = [f"# {plan.get('title', '프로젝트 플랜')}", ""]
    for pi, phase in enumerate(plan.get("phases", [])):
        lines.append(f"## {phase['name']}  ({phase.get('duration', '')})")
        for ti, task in enumerate(phase.get("tasks", [])):
            checked = st.session_state.get(f"plan_cb_{pi}-{ti}", False)
            lines.append(f"- {'[x]' if checked else '[ ]'} {task['text']}")
        lines.append("")
    return "\n".join(lines)


with tab_plan:
    st.caption("프로젝트 목표를 입력하면 사내 문서와 채팅 내역을 바탕으로 플랜을 생성합니다.")

    goal = st.text_area("프로젝트 목표", placeholder="예: 학회 발표 논문 제출 프로젝트 계획", height=100)
    use_history = st.checkbox("채팅 내역 포함", value=True, help="현재 채팅 탭의 대화 내역을 컨텍스트로 활용합니다.")

    if st.button("📋 플랜 생성", type="primary", use_container_width=True, disabled=not goal.strip()):
        with st.spinner("플랜을 생성하는 중입니다..."):
            try:
                history = st.session_state.messages if use_history else []
                result = _create_plan(goal, history)
                if result.get("success"):
                    d = result["data"]
                    # 이전 플랜의 체크박스 상태 초기화
                    if st.session_state.plan_data:
                        old_plan = st.session_state.plan_data
                        for old_pi, old_phase in enumerate(old_plan.get("phases", [])):
                            for old_ti in range(len(old_phase.get("tasks", []))):
                                st.session_state.pop(f"plan_cb_{old_pi}-{old_ti}", None)
                    st.session_state.plan_data = d["plan"]
                    if d.get("sources"):
                        with st.expander("📎 참고 문서"):
                            for src in d["sources"]:
                                st.caption(f"📄 {src}")
                else:
                    st.error(f"오류: {result.get('error')}")
            except requests.exceptions.ConnectionError:
                st.error("백엔드에 연결할 수 없습니다.")
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")

    if st.session_state.plan_data:
        plan = st.session_state.plan_data
        st.subheader(plan.get("title", "프로젝트 플랜"))

        for pi, phase in enumerate(plan.get("phases", [])):
            tasks = phase.get("tasks", [])
            done_count = sum(
                1 for ti in range(len(tasks))
                if st.session_state.get(f"plan_cb_{pi}-{ti}", False)
            )

            with st.expander(f"**{phase['name']}** — {phase.get('duration', '')}  ({done_count}/{len(tasks)})", expanded=True):
                st.progress(done_count / len(tasks) if tasks else 0)
                for ti, task in enumerate(tasks):
                    st.checkbox(task["text"], key=f"plan_cb_{pi}-{ti}")

        md_content = _plan_to_markdown(plan)
        st.download_button(
            "⬇️ 플랜 다운로드 (.md)",
            data=md_content,
            file_name=f"plan_{goal[:20].replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
