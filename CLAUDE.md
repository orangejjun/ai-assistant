# AI Assistant — 사내 문서 기반 RAG 비서

사내 문서를 벡터 DB에 인덱싱하고, 자연어 질의에 RAG + GPT로 답변하는 시스템.
화장품 회사(K-beauty) 특화 포스터 생성, PPT, 프로젝트 플랜, 이메일 발송, 대화 메모리 기능을 포함한다.

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 임베딩 | OpenAI `text-embedding-3-small` |
| 벡터 DB | ChromaDB (로컬) |
| LLM | OpenAI `gpt-4o-mini` |
| 이미지 생성 | OpenAI `gpt-image-1` (K-beauty 특화) |
| PPT 생성 | `python-pptx` |
| 웹 검색 | Naver Search API |
| 이메일 발송 | Resend API |
| 프론트엔드 | Streamlit ≥ 1.35 |

## 환경변수 (.env)

| 변수 | 용도 |
|------|------|
| `OPENAI_API_KEY` | GPT, 임베딩, gpt-image-1 |
| `NAVER_CLIENT_ID` | Naver Search API |
| `NAVER_CLIENT_SECRET` | Naver Search API |
| `RESEND_API_KEY` | Resend 이메일 발송 |
| `RESEND_FROM_EMAIL` | 발신자 주소 (기본: `onboarding@resend.dev`) |

---

## 개발 규칙 (반드시 준수)

- **타입 힌트 필수** — 모든 함수 인자 및 반환값
- **환경변수 하드코딩 금지** — 반드시 `.env` + `os.getenv()` 사용
- **모든 모듈에 `if __name__ == "__main__":` 블록 포함**
- **Sub Agent 간 직접 통신 금지** — 반드시 Main Agent 경유
- **모든 Sub Agent 결과는 `{"success": bool, "data": ..., "error": ...}` JSON 반환**
- **Phase 완료 시 `docs/phases.md` Progress 업데이트**

---

## 토큰 설정

| 항목 | 값 |
|------|-----|
| 청크 크기 | 800 토큰 (`chunker.py`) |
| 청크 오버랩 | 150 토큰 |
| 검색 청크 수 (k) | 5개 |
| 답변 max_tokens | 2048 |
| 플랜 max_tokens | 4096 |
| 포스터 프롬프트 max_tokens | 1536 |
| PPT 슬라이드 max_tokens | 4096 |
| 번역 배치 max_tokens | 4096 |
| 추천 질문 max_tokens | 512 |
| 대화 제목 생성 max_tokens | 20 |

---

## 주요 동작 원칙

- 임베딩은 **영어 번역본**으로 생성, ChromaDB에는 **원본** 저장 (Cross-lingual Retrieval)
- MD5 해시로 중복 인덱싱 방지 (`hash_store.json`)
- 번역: 20개 배치 + `ThreadPoolExecutor(max_workers=10)` 병렬 처리

### 대화 메모리 (Phase 18)
- 세션 이력: `data/history/{session_id}.json` — 브라우저 새로고침 후에도 재개 가능
- Q&A 임베딩: ChromaDB `conversation_memory` 컬렉션 — 과거 유사 대화를 RAG 파이프라인에 주입
- 유사도 임계값: distance < 0.6 (너무 먼 과거 대화 자동 제외)
- 메모리 저장 실패는 무시 (답변 흐름 방해하지 않음)
- 대화 제목: 첫 Q&A 완성 시 GPT로 자동 생성, 사용자가 인라인 편집 가능

### 멀티턴 대화 컨텍스트 (Phase 22)
- 질의 시 최근 20개 메시지(10턴)를 `chat_history`로 백엔드에 전달
- `answer_agent.py`의 `_call_gpt()`가 `[system] + [이전 대화 이력] + [현재 질문+RAG]` 형태의 멀티턴 포맷으로 GPT 호출
- "방금 말한 내용 더 설명해줘" 같은 연속 대화 가능
- `sources`, `web_sources` 등 UI 전용 필드는 제거하고 `role`/`content`만 전달

### 포스터 생성 (Phase 21)
- 이미지 모델: `gpt-image-1` (개인 인증 필요), `quality="high"`
- K-beauty 브랜드 특화 시스템 프롬프트 (색상 팔레트, 레이아웃, 보태니컬 장식)
- 지원 크기: `1024x1536` (세로형), `1024x1024` (정방형), `1536x1024` (가로형)
- 생성된 포스터는 세션 내 히스토리로 누적 표시 (session_state.poster_history)

### PPT 생성
- 생성된 PPT는 세션 내 히스토리로 누적 표시 (session_state.ppt_history)

### UI 구조 (Phase 19 + 사이드바 개선)
- 사이드바: 대화 이력 전용 (세션 목록 · 새 대화 · 제목 편집 · 삭제), 너비 300px
- 파일 관리: `📁` 아이콘 버튼 → `@st.dialog` 모달 (파일 업로드 / 폴더 인덱싱 / 파일 목록 탭)
- 세션 카드: 연한 회색 배경(#F7F8FA), 두 줄 버튼(제목+날짜), 호버 시 ✏/🗑 아이콘 노출
- 활성 세션: CSS `:has()` 마커로 파란 배경(#EFF6FF) 하이라이트

---

> 아키텍처 상세 → `docs/architecture.md`
> Phase 목록 및 진행 현황 → `docs/phases.md`
