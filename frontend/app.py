import os

import requests
import streamlit as st
import streamlit.components.v1 as components

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AI 문서 비서", page_icon="📚", layout="wide")

st.markdown("""<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, [class*="css"], .stApp { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important; background: #F9FAFB !important; color: #191F28 !important; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton, [data-testid="stHeader"] { display:none !important; }
[data-testid="stSidebar"] { background: #FFFFFF !important; border-right: 1px solid #E5E8EB !important; }
section[data-testid="stSidebar"] { min-width:260px !important; max-width:260px !important; transform:none !important; visibility:visible !important; }
[data-testid="stSidebarUserContent"] { padding: 24px 16px !important; }
[data-testid="stSidebar"] .stTitle, [data-testid="stSidebar"] h1 { font-size:16px !important; font-weight:700 !important; color:#191F28 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button { background: #F2F4F6 !important; border: none !important; color: #191F28 !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 14px !important; padding: 10px 16px !important; transition: background 150ms !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover { background: #E5E8EB !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] { background: #3182F6 !important; color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover { background: #1B6EE8 !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 700 !important; color: #3182F6 !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { font-size: 12px !important; color: #6B7684 !important; }
[data-testid="stMainBlockContainer"] { background: #F9FAFB !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
h1 { font-size: 24px !important; font-weight: 800 !important; color: #191F28 !important; letter-spacing: -0.5px !important; }
h2 { font-size: 18px !important; font-weight: 700 !important; color: #191F28 !important; }
h3 { font-size: 15px !important; font-weight: 600 !important; color: #191F28 !important; }
p, li, label { color: #191F28 !important; font-size: 14px !important; }
[data-testid="stCaptionContainer"] p { color: #6B7684 !important; font-size: 13px !important; }
[data-testid="stTabs"] [role="tablist"] { border-bottom: 2px solid #E5E8EB !important; gap: 0 !important; }
[data-testid="stTabs"] [role="tab"] { font-size: 14px !important; font-weight: 600 !important; color: #6B7684 !important; padding: 10px 20px !important; border: none !important; background: transparent !important; border-bottom: 2px solid transparent !important; margin-bottom: -2px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #3182F6 !important; border-bottom: 2px solid #3182F6 !important; }
[data-testid="stTabs"] [role="tab"]:hover { color: #3182F6 !important; background: #F2F4F6 !important; border-radius: 8px 8px 0 0 !important; }
[data-testid="stButton"] > button { border-radius: 10px !important; font-weight: 600 !important; font-size: 14px !important; border: 1px solid #E5E8EB !important; background: #FFFFFF !important; color: #191F28 !important; transition: all 150ms !important; padding: 9px 18px !important; }
[data-testid="stButton"] > button:hover { background: #F2F4F6 !important; border-color: #D1D6DB !important; }
[data-testid="stButton"] > button[kind="primary"] { background: #3182F6 !important; color: #FFFFFF !important; border: none !important; }
[data-testid="stButton"] > button[kind="primary"]:hover { background: #1B6EE8 !important; }
[data-testid="stButton"] > button:disabled { opacity: 0.4 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background: #FFFFFF !important; border: 1px solid #E5E8EB !important; color: #191F28 !important; border-radius: 10px !important; font-size: 14px !important; padding: 10px 14px !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: #3182F6 !important; box-shadow: 0 0 0 3px rgba(49,130,246,0.12) !important; }
input::placeholder, textarea::placeholder { color: #B0B8C1 !important; }
[data-testid="stSelectbox"] > div > div { background: #FFFFFF !important; border: 1px solid #E5E8EB !important; border-radius: 10px !important; color: #191F28 !important; }
[data-testid="stChatInput"] > div { border: 1px solid #E5E8EB !important; border-radius: 14px !important; background: #FFFFFF !important; box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important; }
[data-testid="stChatInput"] textarea { background: transparent !important; border: none !important; color: #191F28 !important; }
[data-testid="stChatInput"] textarea:focus { box-shadow: none !important; border: none !important; }
[data-testid="stChatInput"] button { color: #3182F6 !important; }
[data-testid="stBottomBlockContainer"] { background: #F9FAFB !important; border-top: 1px solid #E5E8EB !important; }
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; border-radius: 0 !important; margin-bottom: 8px !important; }
[data-testid="stChatMessage"]:has(img[alt="user"]) [data-testid="stChatMessageContent"] { background: #3182F6 !important; border-radius: 18px 18px 4px 18px !important; border: none !important; padding: 12px 16px !important; }
[data-testid="stChatMessage"]:has(img[alt="user"]) [data-testid="stChatMessageContent"] p, [data-testid="stChatMessage"]:has(img[alt="user"]) [data-testid="stChatMessageContent"] span, [data-testid="stChatMessage"]:has(img[alt="user"]) [data-testid="stChatMessageContent"] li { color: #fff !important; }
[data-testid="stChatMessage"]:has(img[alt="assistant"]) [data-testid="stChatMessageContent"] { background: #F2F4F6 !important; border-radius: 18px 18px 18px 4px !important; border: none !important; padding: 12px 16px !important; }
[data-testid="stToggle"] label { color: #191F28 !important; font-size: 14px !important; font-weight: 500 !important; }
[data-testid="stToggle"] [role="switch"][aria-checked="true"] { background: #3182F6 !important; }
[data-testid="stCheckbox"] label span { color: #191F28 !important; font-size: 14px !important; }
[data-testid="stExpander"] { background: #FFFFFF !important; border: 1px solid #E5E8EB !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #191F28 !important; font-weight: 600 !important; }
[data-testid="stFileUploaderDropzone"] { background: #F2F4F6 !important; border: 1.5px dashed #C2CAD4 !important; border-radius: 12px !important; }
[data-testid="stSuccess"] { background: #E8F5E9 !important; border: 1px solid #81C784 !important; border-radius: 10px !important; }
[data-testid="stError"] { background: #FFEBEE !important; border: 1px solid #E57373 !important; border-radius: 10px !important; }
[data-testid="stWarning"] { background: #FFF8E1 !important; border: 1px solid #FFD54F !important; border-radius: 10px !important; }
[data-testid="stInfo"] { background: #E3F2FD !important; border: 1px solid #64B5F6 !important; border-radius: 10px !important; }
hr { border-color: #E5E8EB !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #F2F4F6; }
::-webkit-scrollbar-thumb { background: #D1D6DB; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #B0B8C1; }
[data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #E5E8EB !important; border-radius: 12px !important; padding: 16px !important; }
[data-testid="stDownloadButton"] > button { background: #F2F4F6 !important; border: 1px solid #E5E8EB !important; color: #191F28 !important; border-radius: 10px !important; }
</style>""", unsafe_allow_html=True)

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
if "generating" not in st.session_state:
    st.session_state.generating = False
if "suggested_questions" not in st.session_state:
    st.session_state.suggested_questions = []
if "session_id" not in st.session_state:
    import uuid as _uuid
    st.session_state.session_id = _uuid.uuid4().hex[:12]
if "history_list" not in st.session_state:
    st.session_state.history_list = []


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
        json={"query": query, "use_web_search": use_web_search, "session_id": st.session_state.session_id},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def _new_session_id() -> str:
    import uuid as _uuid
    return _uuid.uuid4().hex[:12]


def _save_history() -> None:
    try:
        if not st.session_state.session_id:
            return
        requests.post(
            f"{API_BASE}/history",
            json={"session_id": st.session_state.session_id, "messages": st.session_state.messages},
            timeout=10,
        )
    except Exception:
        pass


def _list_history() -> list:
    try:
        res = requests.get(f"{API_BASE}/history", timeout=5)
        if res.ok:
            return res.json().get("data", {}).get("sessions", [])
    except Exception:
        pass
    return []


def _load_history(session_id: str) -> None:
    try:
        res = requests.get(f"{API_BASE}/history/{session_id}", timeout=10)
        if res.ok:
            data = res.json().get("data", {})
            st.session_state.messages = data.get("messages", [])
            st.session_state.session_id = session_id
    except Exception:
        pass


def _delete_history(session_id: str) -> None:
    try:
        requests.delete(f"{API_BASE}/history/{session_id}", timeout=10)
    except Exception:
        pass


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


def _create_ppt(topic: str, num_slides: int) -> dict:
    res = requests.post(
        f"{API_BASE}/ppt",
        json={"topic": topic, "num_slides": num_slides},
        timeout=120,
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


def _get_suggestions() -> list[str]:
    try:
        res = requests.get(f"{API_BASE}/suggestions", timeout=15)
        if res.ok:
            return res.json().get("data", {}).get("suggestions", [])
    except Exception:
        pass
    return []


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


def _scroll_to_bottom() -> None:
    components.html(
        """<script>
        (function(){
          function scroll(){
            var el = window.parent.document.querySelector('[data-testid="stMain"]');
            if(el) el.scrollTop = el.scrollHeight;
          }
          scroll();
          setTimeout(scroll, 150);
          setTimeout(scroll, 400);
          setTimeout(scroll, 800);
        })();
        </script>""",
        height=0,
    )


@st.dialog("📁 파일 관리", width="large")
def _file_manager_dialog() -> None:
    tab_upload, tab_ingest, tab_manage = st.tabs(["📤 파일 업로드", "🔄 폴더 인덱싱", "🗂️ 파일 목록"])

    with tab_upload:
        st.caption("PDF, DOCX, TXT, XLSX 파일을 업로드하면 즉시 파싱·임베딩·인덱싱됩니다.")
        uploaded_files = st.file_uploader(
            "파일 선택 (여러 개 동시 선택 또는 드래그 앤 드롭)",
            type=["pdf", "docx", "txt", "xlsx"],
            accept_multiple_files=True,
        )
        if uploaded_files and st.button("업로드 & 인덱싱", type="primary", use_container_width=True):
            total_chunks = 0
            success_count = 0
            duplicate_count = 0
            errors = []
            progress = st.progress(0, text="업로드 준비 중...")
            for i, f in enumerate(uploaded_files):
                progress.progress(
                    (i + 1) / len(uploaded_files),
                    text=f"{f.name} 처리 중... ({i + 1}/{len(uploaded_files)})",
                )
                try:
                    result = _upload_file(f)
                    if result.get("success"):
                        d = result["data"]
                        if d.get("duplicate"):
                            duplicate_count += 1
                        else:
                            success_count += 1
                            total_chunks += d.get("chunks", 0)
                    else:
                        errors.append(f"{f.name}: {result.get('error')}")
                except requests.exceptions.ConnectionError:
                    errors.append(f"{f.name}: 백엔드에 연결할 수 없습니다.")
                except requests.exceptions.HTTPError as e:
                    detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                    errors.append(f"{f.name}: {detail}")
                except Exception as e:
                    errors.append(f"{f.name}: {e}")
            progress.empty()
            if success_count:
                st.success(
                    f"✅ {success_count}개 파일 인덱싱 완료  |  신규 청크: **{total_chunks}개**"
                    + (f"  |  중복 건너뜀: **{duplicate_count}개**" if duplicate_count else "")
                )
            elif duplicate_count:
                st.warning(f"⚠️ {duplicate_count}개 파일 모두 이미 인덱싱된 파일입니다.")
            for err in errors:
                st.error(f"오류: {err}")

    with tab_ingest:
        st.caption("지정한 폴더의 모든 문서를 일괄 스캔하여 인덱싱합니다.")
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
                                f"✅ 완료  |  처리 파일: **{data['processed_files']}개**"
                                f"  |  신규 청크: **{data['total_chunks']}개**"
                                f"  |  DB 누적: **{data['db_total_chunks']}개**"
                            )
                    else:
                        st.error(f"오류: {result.get('error')}")
                except requests.exceptions.ConnectionError:
                    st.error("백엔드에 연결할 수 없습니다.")
                except requests.exceptions.HTTPError as e:
                    detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                    st.error(f"오류: {detail}")
                except Exception as e:
                    st.error(f"알 수 없는 오류: {e}")

    with tab_manage:
        st.caption("인덱싱된 파일을 확인하고 삭제할 수 있습니다. (삭제된 파일은 휴지통으로 이동됩니다)")
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
                                f"✅ 삭제 완료  |  **{d['filename']}**  |  청크 {d['deleted_chunks']}개 제거"
                            )
                        else:
                            st.error(f"오류: {result.get('error')}")
                    except requests.exceptions.HTTPError as e:
                        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
                        st.error(f"오류: {detail}")
                    except Exception as e:
                        st.error(f"알 수 없는 오류: {e}")
        else:
            st.info("인덱싱된 파일이 없습니다.")


def _render_email_steps(current: int) -> None:
    steps = ["채팅으로 내용 설명", "초안 검토 & 수신자", "첨부 & 전송"]
    html = '<div style="display:flex;align-items:center;margin-bottom:20px;padding:16px 20px;background:#fff;border:1px solid #E5E8EB;border-radius:12px;">'
    for i, label in enumerate(steps, 1):
        active = i == current
        done = i < current
        circle_bg = "#3182F6" if (active or done) else "#E5E8EB"
        circle_txt = "#fff" if (active or done) else "#B0B8C1"
        label_color = "#3182F6" if active else ("#191F28" if done else "#B0B8C1")
        label_weight = "700" if active else "500"
        num = "✓" if done else str(i)
        html += (
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="width:26px;height:26px;border-radius:50%;background:{circle_bg};'
            f'color:{circle_txt};display:flex;align-items:center;justify-content:center;'
            f'font-size:12px;font-weight:700;flex-shrink:0;">{num}</div>'
            f'<span style="font-size:13px;font-weight:{label_weight};color:{label_color};white-space:nowrap;">{label}</span>'
            f'</div>'
        )
        if i < 3:
            line_color = "#3182F6" if done else "#E5E8EB"
            html += f'<div style="flex:1;height:2px;background:{line_color};margin:0 10px;min-width:20px;"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── 사이드바 ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AI 문서 비서")

    status = _get_status()
    if status:
        st.metric("인덱싱된 청크", status.get("total_chunks", 0))
    else:
        st.warning("⚠️ 백엔드 연결 불가")

    if st.button("📁 파일 관리", use_container_width=True, type="primary"):
        _file_manager_dialog()

    st.divider()
    st.subheader("💬 대화 이력")

    col_new, col_refresh = st.columns([3, 1])
    with col_new:
        if st.button("+ 새 대화", use_container_width=True, type="primary"):
            _save_history()
            st.session_state.session_id = _new_session_id()
            st.session_state.messages = []
            st.session_state.suggested_questions = []
            st.session_state.history_list = _list_history()
            st.rerun()
    with col_refresh:
        if st.button("↺", use_container_width=True, help="이력 새로고침"):
            st.session_state.history_list = _list_history()
            st.rerun()

    if not st.session_state.history_list:
        st.session_state.history_list = _list_history()

    for s in st.session_state.history_list[:10]:
        sid = s["session_id"]
        date_str = s["updated_at"][:10] if s.get("updated_at") else ""
        preview = s.get("preview", "")[:22] or "빈 대화"
        label = f"{date_str}  {preview}"
        is_active = sid == st.session_state.session_id
        btn_col, del_col = st.columns([5, 1])
        with btn_col:
            if st.button(
                label,
                key=f"hist_{sid}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                help=f"세션 ID: {sid}",
            ):
                _save_history()
                _load_history(sid)
                st.rerun()
        with del_col:
            if st.button("✕", key=f"del_{sid}", help="이 이력 삭제"):
                _delete_history(sid)
                if sid == st.session_state.session_id:
                    st.session_state.session_id = _new_session_id()
                    st.session_state.messages = []
                st.session_state.history_list = _list_history()
                st.rerun()

    st.divider()

    if st.button("🗑️ 현재 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.suggested_questions = []
        st.rerun()


# ── 메인 탭 ──────────────────────────────────────────────────────────────────

st.title("📚 AI 문서 비서")

tab_chat, tab_poster, tab_ppt, tab_plan, tab_email = st.tabs(["💬 채팅", "🎨 포스터 생성", "📊 PPT 생성", "📋 플랜 생성", "✉️ 이메일 작성"])


# ── 탭 1: 채팅 ────────────────────────────────────────────────────────────────

with tab_chat:
    st.caption("사내 문서를 기반으로 질문에 답변합니다.")
    use_web_search = st.toggle("🌐 Naver 웹 검색 포함", value=False, help="켜면 사내 문서 검색에 Naver 웹 검색 결과를 추가합니다.")

    # ── 기존 메시지 표시 (항상 messages 루프 안에서만 렌더링) ──
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

    # ── 응답 생성 (chat_input 이전에 실행 → chat input 위에 렌더링) ──
    if st.session_state.generating:
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중입니다..."):
                try:
                    last_user_msg = next(
                        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
                        "",
                    )
                    result = _run_query(last_user_msg, use_web_search=use_web_search)
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
                        _save_history()
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
                finally:
                    st.session_state.generating = False

    # ── 빈 화면 Empty State ──
    if not st.session_state.messages and not st.session_state.generating:
        st.markdown(
            '<div style="text-align:center;padding:40px 24px 20px;">'
            '<div style="font-size:48px;margin-bottom:16px;">📚</div>'
            '<div style="font-size:20px;font-weight:700;color:#191F28;margin-bottom:8px;">AI 문서 비서에 오신 것을 환영합니다</div>'
            '<div style="font-size:14px;color:#6B7684;margin-bottom:28px;">인덱싱된 사내 문서를 기반으로 질문에 답변해 드립니다</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.suggested_questions:
            with st.spinner("추천 질문 생성 중..."):
                st.session_state.suggested_questions = _get_suggestions()

        st.markdown(
            '<p style="text-align:center;font-size:12px;color:#B0B8C1;margin:0 0 10px;">💡 추천 질문</p>',
            unsafe_allow_html=True,
        )

        suggestions = st.session_state.suggested_questions
        chips = suggestions if suggestions else []
        col_spec = [1] * max(len(chips), 1) + [0.13]
        cols = st.columns(col_spec)
        for i, q in enumerate(chips):
            if cols[i].button(f"↗  {q}", key=f"sq_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                st.session_state.generating = True
                st.rerun()
        if cols[-1].button("🔄", key="refresh_sq", help="새 추천 질문 생성", use_container_width=True):
            st.session_state.suggested_questions = []
            st.rerun()

    # ── 스크롤 → chat_input 이전 호출로 정상 flow 내 렌더링 ──
    _scroll_to_bottom()

    # ── 채팅 입력 ──
    user_input = st.chat_input("질문을 입력하세요...")
    if user_input and not st.session_state.generating:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.generating = True
        st.rerun()


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


# ── 탭 3: PPT 생성 ────────────────────────────────────────────────────────────

with tab_ppt:
    st.caption("사내 문서를 기반으로 PowerPoint 프레젠테이션을 생성합니다.")

    col1, col2 = st.columns([3, 1])
    with col1:
        ppt_topic = st.text_input("프레젠테이션 주제", placeholder="예: 2026 전략 보고서, 올리브영 채널 현황")
    with col2:
        ppt_num_slides = st.number_input("슬라이드 수", min_value=3, max_value=15, value=5)

    if st.button("📊 PPT 생성", type="primary", use_container_width=True, disabled=not ppt_topic.strip()):
        with st.spinner("PPT를 생성하는 중입니다... (약 20~40초 소요)"):
            try:
                result = _create_ppt(ppt_topic, int(ppt_num_slides))
                if result.get("success"):
                    import base64 as _b64
                    d = result["data"]
                    ppt_bytes = _b64.b64decode(d["presentation_b64"])
                    st.download_button(
                        "⬇️ PPT 다운로드 (.pptx)",
                        data=ppt_bytes,
                        file_name=f"ppt_{ppt_topic[:20].replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
                    with st.expander(f"📑 슬라이드 구성 ({d['slide_count']}장)", expanded=True):
                        for i, slide in enumerate(d.get("slides", []), 1):
                            label = "🎯 타이틀" if slide["type"] == "title" else ("✅ 요약" if slide["type"] == "summary" else f"슬라이드 {i}")
                            st.markdown(f"**{label}** — {slide.get('title', '')}")
                            for b in slide.get("bullets", []):
                                st.caption(f"  • {b}")
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


# ── 탭 4: 플랜 생성 ───────────────────────────────────────────────────────────

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
    if st.session_state.get("email_sent"):
        _render_email_steps(3)
    elif st.session_state.email_draft:
        _render_email_steps(2)
    else:
        _render_email_steps(1)

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
