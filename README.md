# AI Assistant — 사내 문서 기반 RAG 비서

사내 문서를 벡터 DB에 저장하고 자연어 질의로 검색하여 GPT-4o-mini로 답변을 반환하는 RAG 시스템.

---

## 개발 Phase

| Phase | 상태 | 내용 |
|-------|------|------|
| Phase 1 | ✅ | 문서 파싱, 청크, 임베딩, ChromaDB 저장 (CLI) |
| Phase 2 | ✅ | 벡터 검색, GPT 답변 생성 |
| Phase 3 | ✅ | Streamlit UI + FastAPI 백엔드 |
| Phase 4 | ✅ | Docker, 클라우드 배포 |
| Phase 5 | ✅ | UI 파일 업로드 + POST /upload 인덱싱 API |

---

## 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 API 키를 입력합니다.

```dotenv
OPENAI_API_KEY=sk-...
```

---

## 실행 방법

### A. 로컬 실행 (venv)

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 터미널 1 — FastAPI 백엔드
uvicorn backend.api.main:app --reload

# 터미널 2 — Streamlit 프론트엔드
streamlit run frontend/app.py
```

접속: `http://localhost:8501`

---

### B. Docker 실행

#### 사전 요구사항

- Docker Desktop 설치 및 실행 중
- `.env` 파일에 `OPENAI_API_KEY` 입력 완료

#### 빌드 및 실행

```bash
docker-compose up --build
```

백그라운드 실행:

```bash
docker-compose up --build -d
```

접속: `http://localhost:8501`

#### 서비스 중지

```bash
docker-compose down
```

#### 로그 확인

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

### C. 파일 업로드 (UI)

서버 실행 후 `http://localhost:8501` 에 접속하여 왼쪽 사이드바 **파일 업로드** 섹션을 사용합니다.

1. **파일 선택** — PDF, DOCX, TXT, XLSX 중 하나를 선택합니다.
2. **업로드 & 인덱싱** 버튼 클릭 → 파일이 `data/raw/` 에 저장되고 즉시 임베딩 후 ChromaDB에 추가됩니다.
3. 업로드 완료 후 채팅에서 해당 파일 내용을 바로 질문할 수 있습니다.

> **중복 처리**: 이미 인덱싱된 파일(내용 기준 MD5 비교)은 재처리 없이 안내 메시지를 반환합니다.

#### API 직접 사용 (curl)

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/document.pdf"
```

---

### D. CLI (문서 인덱싱 / 질의)

```bash
# 문서 인덱싱
python run_ingest.py --folder data/raw

# 질의
python run_query.py --query "연차 신청은 며칠 전에 해야 하나요?"

# 디버그 모드 (검색된 청크 출력)
python run_query.py --query "..." --debug
```

---

## 폴더 구조

```
ai-assistant/
├── backend/
│   ├── ingest/     # 파일 파싱, 청크, 임베딩
│   ├── retrieval/  # 벡터 검색
│   ├── agent/      # Sub Agent (Retrieval, Answer, Main)
│   └── api/        # FastAPI 라우터
├── frontend/       # Streamlit UI
├── data/
│   ├── raw/        # 원본 문서 보관
│   └── vectordb/   # ChromaDB 저장소 (볼륨 마운트)
├── tests/          # pytest 테스트 (100개)
├── skills/         # 반복 작업 패턴
├── Dockerfile
├── docker-compose.yml
├── deploy.sh       # 프로덕션 배포 스크립트
└── .env            # API 키 (gitignore 처리)
```
