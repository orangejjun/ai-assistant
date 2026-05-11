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
if "email_messages" not in st.session_state:
    st.session_state.email_messages = []
if "email_draft" not in st.session_state:
    st.session_state.email_draft = None
if "email_suggestions" not in st.session_state:
    st.session_state.email_suggestions = {"to_suggestion": None, "cc_suggestions": []}


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


def _draft_email(messages: list[dict]) -> dict:
    res = requests.post(
        f"{API_BASE}/email/draft",
        json={"messages": messages},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def _recommend_recipients(subject: str, body: str) -> dict:
    res = requests.post(
        f"{API_BASE}/email/recipients",
        json={"subject": subject, "body": body},
        timeout=45,
    )
    res.raise_for_status()
    return res.json()


def _send_email(
    to: str,
    cc_list: list[str],
    subject: str,
    body: str,
    attachments: list,
) -> dict:
    files = [
        ("attachments", (f.name, f.getvalue(), f.type or "application/octet-stream"))
        for f in attachments
    ]
    res = requests.post(
        f"{API_BASE}/email/send",
        data={"to": to, "cc": ",".join(cc_list), "subject": subject, "body": body},
        files=files if files else [("attachments", ("", b"", "application/octet-stream"))],
        timeout=60,
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

tab_chat, tab_poster, tab_plan, tab_email = st.tabs(["💬 채팅", "🎨 포스터 생성", "📋 플랜 생성", "✉️ 이메일 작성"])


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


# ── 탭 4: 이메일 작성 ─────────────────────────────────────────────────────────

with tab_email:
    st.caption("채팅으로 이메일 목적을 설명하면 AI가 초안을 생성하고 수신자를 추천합니다.")

    # ── Step 1: 채팅으로 이메일 내용 설명 ────────────────────────────────────

    st.markdown("### Step 1. 채팅으로 이메일 내용 설명")

    for msg in st.session_state.email_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if email_prompt := st.chat_input("이메일 내용을 설명해주세요...", key="email_chat_input"):
        st.session_state.email_messages.append({"role": "user", "content": email_prompt})
        with st.chat_message("user"):
            st.write(email_prompt)

        with st.chat_message("assistant"):
            with st.spinner("이메일 초안을 생성하는 중입니다..."):
                try:
                    draft_result = _draft_email(st.session_state.email_messages)
                    if draft_result.get("success"):
                        draft_data = draft_result["data"]

                        # 폼 필드 동기화 — session state 직접 업데이트해야 위젯에 반영됨
                        st.session_state.email_draft = {
                            "subject": draft_data["subject"],
                            "body": draft_data["body"],
                        }
                        st.session_state["email_subject"] = draft_data["subject"]
                        st.session_state["email_body"] = draft_data["body"]

                        # assistant 메시지에 전체 본문 포함 — 다음 수정 요청 시 GPT가 참조
                        assistant_msg = (
                            f"초안이 생성되었습니다. 수정이 필요하면 채팅으로 알려주세요.\n\n"
                            f"**제목**: {draft_data['subject']}\n\n"
                            f"**본문**:\n{draft_data['body']}"
                        )
                        st.write(assistant_msg)
                        st.session_state.email_messages.append({"role": "assistant", "content": assistant_msg})

                        # 수신자 추천 자동 실행
                        rec_result = _recommend_recipients(draft_data["subject"], draft_data["body"])
                        if rec_result.get("success"):
                            st.session_state.email_suggestions = {
                                "to_suggestion": rec_result["data"].get("to_suggestion"),
                                "cc_suggestions": rec_result["data"].get("cc_suggestions", []),
                            }

                        if draft_data.get("sources"):
                            with st.expander("📎 참고 사내 문서"):
                                for src in draft_data["sources"]:
                                    st.caption(f"📄 {src}")
                    else:
                        error_msg = f"초안 생성 실패: {draft_result.get('error')}"
                        st.error(error_msg)
                        st.session_state.email_messages.append({"role": "assistant", "content": error_msg})
                except requests.exceptions.ConnectionError:
                    st.error("백엔드에 연결할 수 없습니다.")
                except requests.exceptions.HTTPError as e:
                    detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                    st.error(f"오류: {detail}")
                except Exception as e:
                    st.error(f"알 수 없는 오류: {e}")

    if st.button("🗑️ 대화 초기화", key="email_clear", use_container_width=False):
        st.session_state.email_messages = []
        st.session_state.email_draft = None
        st.session_state.email_suggestions = {"to_suggestion": None, "cc_suggestions": []}
        for k in ["email_to", "email_cc", "email_subject", "email_body"]:
            st.session_state.pop(k, None)
        st.session_state.pop("email_sent", None)
        st.rerun()

    # ── Step 2: 초안 확인 및 수정 ────────────────────────────────────────────

    st.markdown("### Step 2. 초안 확인 및 수정")

    suggestions = st.session_state.email_suggestions
    to_sug = suggestions.get("to_suggestion")
    cc_sugs = suggestions.get("cc_suggestions", [])

    # 받는 사람 (To)
    if to_sug:
        with st.expander(f"💡 AI 주 수신자 추천: **{to_sug['name']}** ({to_sug['team']}) — {to_sug['reason']}"):
            if st.button("이 사람으로 설정", key="apply_to_sug"):
                st.session_state["email_to"] = to_sug["email"]
                st.rerun()

    email_to = st.text_input("받는 사람 (To)", placeholder="recipient@example.com", key="email_to")

    # 참조 (CC)
    if cc_sugs:
        with st.expander("💡 AI 참조(CC) 추천 (선택하면 CC에 추가됩니다)"):
            selected_cc_emails = []
            for rec in cc_sugs:
                if st.checkbox(
                    f"{rec['name']} ({rec['team']}) — {rec['reason']}",
                    key=f"email_rec_{rec['email']}",
                ):
                    selected_cc_emails.append(rec["email"])
            if selected_cc_emails and st.button("선택한 담당자를 CC에 추가", key="apply_cc_sug"):
                existing = st.session_state.get("email_cc", "")
                existing_list = [e.strip() for e in existing.split(",") if e.strip()]
                merged = list(dict.fromkeys(existing_list + selected_cc_emails))
                st.session_state["email_cc"] = ", ".join(merged)
                st.rerun()

    email_cc = st.text_area(
        "참조 (CC) — 쉼표로 구분",
        height=68,
        placeholder="cc1@example.com, cc2@example.com",
        key="email_cc",
    )
    email_subject = st.text_input("제목", key="email_subject")
    email_body = st.text_area("본문", height=300, key="email_body")

    # ── Step 3: 파일 첨부 & 전송 ─────────────────────────────────────────────

    st.markdown("### Step 3. 파일 첨부 & 전송")

    email_attachments = st.file_uploader(
        "첨부 파일",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "xlsx", "png", "jpg", "jpeg"],
        key="email_attachments",
    )

    if st.button("📨 전송하기", type="primary", use_container_width=True, disabled=not email_to.strip()):
        with st.spinner("이메일을 전송하는 중입니다..."):
            try:
                cc_list = [addr.strip() for addr in email_cc.split(",") if addr.strip()]
                send_result = _send_email(
                    to=email_to.strip(),
                    cc_list=cc_list,
                    subject=email_subject.strip(),
                    body=email_body,
                    attachments=list(email_attachments) if email_attachments else [],
                )
                if send_result.get("success"):
                    d = send_result["data"]
                    st.session_state["email_sent"] = d
                else:
                    st.error(f"전송 실패: {send_result.get('error')}")
            except requests.exceptions.ConnectionError:
                st.error("백엔드에 연결할 수 없습니다.")
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                st.error(f"오류: {detail}")
            except Exception as e:
                st.error(f"알 수 없는 오류: {e}")

    if st.session_state.get("email_sent"):
        sent = st.session_state["email_sent"]
        st.success("✅ 이메일이 전송되었습니다.")
        with st.container(border=True):
            st.markdown("#### 📧 전송된 이메일")
            st.markdown(f"**받는 사람** &nbsp; `{sent['to']}`")
            if sent.get("cc"):
                st.markdown(f"**참조(CC)** &nbsp; `{', '.join(sent['cc'])}`")
            st.markdown(f"**제목** &nbsp; {sent['subject']}")
            st.divider()
            st.markdown(sent["body"])
            if sent.get("attachment_names"):
                st.markdown("**첨부 파일**")
                for fname in sent["attachment_names"]:
                    st.caption(f"📎 {fname}")
        if st.button("새 이메일 작성", use_container_width=True):
            st.session_state.email_messages = []
            st.session_state.email_draft = None
            st.session_state.email_recipients = []
            st.session_state.pop("email_sent", None)
            st.rerun()
