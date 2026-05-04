# AI Assistant — 사내 문서 기반 RAG 비서

## 프로젝트 개요

사내 문서 기반 RAG AI 비서.
사용자가 지정 폴더의 문서를 업로드/스캔하면 자동으로 임베딩 후 벡터 DB에 저장하고,
자연어 질의에 대해 관련 문서를 검색하여 Claude API로 답변과 출처를 함께 반환한다.

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 임베딩 모델 | OpenAI `text-embedding-3-small` |
| 벡터 DB | ChromaDB (로컬) → 추후 Pinecone 전환 고려 |
| LLM | OpenAI GPT (`gpt-4o-mini`) |
| 프론트엔드 | Streamlit (프로토타입) → React 전환 고려 |
| 환경변수 | python-dotenv + `.env` 파일 |

---

## 폴더 구조

```
doc-assistant/
├── backend/
│   ├── ingest/        # 파일 파싱, 청크 분할, 임베딩
│   ├── retrieval/     # 벡터 검색
│   ├── agent/         # Sub Agent 정의, Claude API 연동
│   └── api/           # FastAPI 라우터
├── frontend/          # Streamlit UI
├── data/
│   ├── raw/           # 원본 문서 보관
│   └── vectordb/      # ChromaDB 저장소
├── skills/            # 반복 작업 패턴 저장
├── .env               # API 키 (gitignore 처리)
└── CLAUDE.md
```

---

## Sub Agent 구조

| Agent | 역할 |
|-------|------|
| **Main Agent** | 라우팅만 담당 — 다른 Agent로 위임 |
| **Ingest Agent** | 파싱 → 청크 → 임베딩 → DB 저장 |
| **Retrieval Agent** | 질의 임베딩 → 벡터 검색 → 청크 반환 |
| **Answer Agent** | 컨텍스트 조합 → Claude API → 답변 + 출처 |
| **File Watcher Agent** | 폴더 변경 감지 → Ingest Agent 트리거 |

**통신 규칙**
- Sub Agent 간 직접 통신 금지 — 반드시 Main Agent 경유
- 모든 Sub Agent 결과는 JSON으로 반환

---

## 토큰 절약 규칙

- 임베딩 대상: 전처리 완료된 청크만 (원본 원문 직접 임베딩 금지)
- Claude API 컨텍스트: 검색된 청크 최대 **5개**로 제한
- 파일 변경 감지: MD5 해시 비교로 중복 임베딩 방지
- Sub Agent 결과 반환: 핵심 데이터만 포함 (로그/디버그 정보 제외)

---

## 개발 규칙

- **타입 힌트 필수** — 모든 함수 인자 및 반환값에 타입 명시
- **환경변수 하드코딩 금지** — API 키, URL 등은 반드시 `.env` + `os.getenv()` 사용
- **모든 모듈 단독 실행 가능하게 작성** — `if __name__ == "__main__":` 블록 포함
- **Phase 완료 시 이 파일의 Progress 섹션 업데이트** — 체크박스 체크 후 완료 일자 기재

---

## 개발 Phase

| Phase | 내용 |
|-------|------|
| Phase 1 | 문서 파싱 + 청크 분할 + 임베딩 + ChromaDB 저장 (CLI) |
| Phase 2 | 벡터 검색 + Claude API 답변 생성 |
| Phase 3 | Streamlit UI + 파일 업로드 |
| Phase 4 | Docker + 클라우드 배포 |
| Phase 5 | UI 파일 업로드 + 단일 파일 인덱싱 API (POST /upload) |

---

## Progress

- [x] Phase 1 — 문서 파싱, 청크, 임베딩, ChromaDB 저장 (CLI) ✅ 2026-05-04
- [x] Phase 2 — 벡터 검색, Claude API 답변 생성 ✅ 2026-05-04
- [x] Phase 3 — Streamlit UI, FastAPI 백엔드 ✅ 2026-05-04
- [x] Phase 4 — Docker, 클라우드 배포 ✅ 2026-05-04
- [x] Phase 5 — UI 파일 업로드, POST /upload 엔드포인트, MD5 중복 방지 ✅ 2026-05-05
