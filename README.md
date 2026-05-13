# AI Assistant — 사내 문서 기반 RAG 비서

사내 문서를 벡터 DB에 인덱싱하고, 자연어 질의에 RAG + GPT-4o-mini로 답변하는 시스템.
K-beauty 특화 포스터 생성, PPT 생성, 프로젝트 플랜, 이메일 발송, 대화 메모리 기능을 포함한다.

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 임베딩 | OpenAI `text-embedding-3-small` |
| 벡터 DB | ChromaDB (로컬) |
| LLM | OpenAI `gpt-4o-mini` |
| 이미지 생성 | OpenAI `gpt-image-1` |
| PPT 생성 | `python-pptx` |
| 웹 검색 | Naver Search API |
| 이메일 발송 | Resend API |
| 프론트엔드 | Streamlit ≥ 1.35 |

---

## 주요 기능

| 탭 | 기능 |
|----|------|
| 💬 채팅 | 문서 기반 RAG 질의응답 · Naver 웹 검색 토글 · 임베딩 기반 추천 질문 · 대화 이력 저장/불러오기 |
| 🎨 포스터 생성 | K-beauty 특화 프롬프트 → gpt-image-1 생성 · 크기 3종 선택 (세로/정방/가로) |
| 📊 PPT 생성 | 주제 + 슬라이드 수 입력 → python-pptx .pptx 파일 다운로드 |
| 📋 플랜 생성 | 프로젝트 목표 + 채팅 이력 기반 TODO 마크다운 플랜 생성 |
| ✉️ 이메일 작성 | 대화로 이메일 초안 작성 → 수신자 추천 → Resend API 실제 발송 |

---

## 개발 Phase

| Phase | 내용 |
|-------|------|
| Phase 1 ✅ | 문서 파싱, 청크, 임베딩, ChromaDB 저장 (CLI) |
| Phase 2 ✅ | 벡터 검색, GPT 답변 생성 |
| Phase 3 ✅ | Streamlit UI + FastAPI 백엔드 |
| Phase 4 ✅ | Docker, 클라우드 배포 |
| Phase 5 ✅ | UI 파일 업로드 + POST /upload 인덱싱 API |
| Phase 6 ✅ | 영어 Pivot 번역 — Cross-lingual Retrieval 해결 |
| Phase 7 ✅ | 파일 삭제 기능 (휴지통 방식) |
| Phase 8 ✅ | start.sh 자동 실행 스크립트 |
| Phase 9 ✅ | 포스터 생성 (POST /poster, 포스터 탭) |
| Phase 10 ✅ | 문서 + 채팅 이력 기반 인터랙티브 TODO 플랜 생성 (POST /plan) |
| Phase 11 ✅ | Naver 웹 검색 연동 — 채팅 토글로 선택 활성화 |
| Phase 12 ✅ | 번역 병렬 배치 처리 + 토큰/청크 크기 최적화 |
| Phase 15 ✅ | python-pptx PPT 생성 (POST /ppt, PPT 탭) |
| Phase 16 ✅ | Resend API 실제 이메일 발송 (개인 메일 계정 불필요) |
| Phase 17 ✅ | 임베딩 기반 동적 추천 질문 생성 (GET /suggestions) |
| Phase 18 ✅ | 대화 메모리 시스템 — 세션 이력 저장/불러오기 + Q&A 임베딩 벡터화 |
| Phase 19 ✅ | 사이드바 리팩토링 — 파일 관리 다이얼로그 분리, 사이드바는 대화 이력 전용 |
| Phase 20 ✅ | 대화 이력 UI 개선 — GPT 자동 제목 생성, 인라인 제목 편집, PATCH /history/{id} |
| Phase 21 ✅ | 포스터 고도화 — gpt-image-1 교체, K-beauty 특화 프롬프트, 크기 3종 선택 |

---

## 환경변수 설정

```bash
cp .env.example .env
```

`.env`를 열어 아래 값을 입력합니다.

| 변수 | 용도 | 필수 |
|------|------|------|
| `OPENAI_API_KEY` | GPT, 임베딩, gpt-image-1 | ✅ |
| `NAVER_CLIENT_ID` | Naver 웹 검색 | 웹 검색 사용 시 |
| `NAVER_CLIENT_SECRET` | Naver 웹 검색 | 웹 검색 사용 시 |
| `RESEND_API_KEY` | 이메일 실제 발송 | 이메일 발송 사용 시 |
| `RESEND_FROM_EMAIL` | 발신자 주소 (기본: `onboarding@resend.dev`) | 이메일 발송 사용 시 |

> **Resend 설정**: [resend.com](https://resend.com) 가입 후 API 키 발급. 무료 테스트 발신자(`onboarding@resend.dev`)는 가입 시 등록한 이메일로만 수신 가능.
>
> **gpt-image-1 설정**: OpenAI 개인 인증(Organization verification) 완료 후 사용 가능.

---

## 실행 방법

### A. 자동 실행 (권장)

```bash
./start.sh
```

백엔드(8000)와 프론트엔드(8501)를 동시에 실행합니다. 접속: `http://localhost:8501`

---

### B. 수동 실행

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# 터미널 1 — FastAPI 백엔드
uvicorn backend.api.main:app --reload

# 터미널 2 — Streamlit 프론트엔드
streamlit run frontend/app.py
```

접속: `http://localhost:8501`

---

### C. Docker 실행

```bash
docker-compose up --build
```

백그라운드 실행:

```bash
docker-compose up --build -d
```

중지:

```bash
docker-compose down
```

로그 확인:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 파일 업로드 / 관리

1. 사이드바 상단 **📁 파일 관리** 버튼 클릭 → 모달 창 열림
2. **파일 업로드** 탭: PDF, DOCX, TXT, XLSX 드래그 앤 드롭 또는 다중 선택 → **업로드 & 인덱싱**
3. **폴더 인덱싱** 탭: 폴더 경로 입력 후 일괄 스캔
4. **파일 목록** 탭: 인덱싱된 파일 확인 및 삭제 (휴지통 이동)

> MD5 해시 기반 중복 방지 — 동일 내용 파일 재업로드 시 건너뜀

---

## 대화 이력

- 답변 생성 후 자동 저장 (`data/history/{session_id}.json`)
- 사이드바에서 과거 세션 클릭 → 대화 재개
- GPT가 첫 Q&A 내용으로 제목을 자동 생성
- 제목 편집(✏) · 삭제(✕) 인라인 지원
- Q&A 쌍을 ChromaDB `conversation_memory` 컬렉션에 임베딩 → 과거 유사 대화가 다음 답변 컨텍스트에 자동 반영

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/upload` | 파일 업로드 + 즉시 인덱싱 |
| POST | `/ingest` | 폴더 전체 인덱싱 |
| POST | `/query` | RAG 질의응답 (session_id 포함 시 메모리 활성화) |
| GET | `/files` | 인덱싱된 파일 목록 |
| DELETE | `/files` | 파일 삭제 (휴지통) |
| POST | `/poster` | K-beauty 포스터 이미지 생성 (size 선택 가능) |
| POST | `/ppt` | PPT 파일 생성 |
| POST | `/plan` | 프로젝트 플랜 생성 |
| POST | `/email/draft` | 이메일 초안 생성 |
| POST | `/email/recipients` | 수신자 추천 |
| POST | `/email/send` | 이메일 실제 발송 |
| GET | `/suggestions` | 문서 기반 추천 질문 3개 생성 |
| POST | `/history` | 세션 대화 이력 저장 |
| GET | `/history` | 저장된 세션 목록 조회 |
| GET | `/history/{id}` | 특정 세션 이력 로드 |
| PATCH | `/history/{id}` | 세션 제목 수정 |
| DELETE | `/history/{id}` | 세션 이력 삭제 |
| GET | `/status` | ChromaDB 청크 수 조회 |

API 문서: `http://localhost:8000/docs`

---

## 폴더 구조

```
ai-assistant/
├── backend/
│   ├── ingest/             # 파일 파싱, 청크, 영어 번역, 임베딩
│   ├── retrieval/          # 벡터 검색 에이전트
│   ├── agent/
│   │   ├── main_agent.py       # 라우팅 + 메모리 주입
│   │   ├── answer_agent.py     # GPT 답변 생성 (memory_context 반영)
│   │   ├── poster_agent.py     # K-beauty gpt-image-1 포스터
│   │   ├── ppt_agent.py
│   │   ├── plan_agent.py
│   │   ├── email_draft_agent.py
│   │   ├── email_recipient_agent.py
│   │   ├── email_sender_agent.py
│   │   └── suggestion_agent.py
│   ├── memory/
│   │   ├── history_manager.py  # 세션 JSON 저장/로드/목록/제목 편집
│   │   └── memory_retrieval.py # Q&A 임베딩 저장 및 유사 검색
│   └── api/                # FastAPI 라우터
├── frontend/
│   └── app.py              # Streamlit UI
├── data/
│   ├── raw/                # 업로드된 원본 문서
│   ├── trash/              # 삭제된 문서 (휴지통)
│   ├── history/            # 세션 대화 이력 JSON (.gitignore)
│   └── vectordb/           # ChromaDB + hash_store.json
├── docs/
│   ├── phases.md
│   └── architecture.md
├── tests/
├── start.sh                # 백엔드 + 프론트엔드 동시 실행
├── docker-compose.yml
└── .env.example
```
