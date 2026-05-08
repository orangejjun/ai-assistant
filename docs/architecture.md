# 아키텍처

## 폴더 구조

```
ai-assistant/
├── backend/
│   ├── ingest/        # 파일 파싱, 청크 분할, 영어 번역, 임베딩
│   ├── retrieval/     # 벡터 검색
│   ├── agent/         # Sub Agent (Answer, Poster, Plan, NaverSearch)
│   └── api/           # FastAPI 라우터 (router.py)
├── frontend/          # Streamlit UI (app.py)
├── docs/              # 프로젝트 문서
├── data/
│   ├── raw/           # 원본 문서 보관
│   ├── vectordb/      # ChromaDB 저장소 + hash_store.json
│   └── trash/         # 삭제된 파일 보관 (휴지통)
├── tests/             # pytest 테스트
├── .env               # API 키 (gitignore 처리)
└── start.sh           # 서버 일괄 실행 스크립트
```

## Sub Agent 역할

| Agent | 파일 | 역할 |
|-------|------|------|
| **Main Agent** | `agent/main_agent.py` | 라우팅 — Retrieval → (WebSearch) → Answer 순서 조율 |
| **Retrieval Agent** | `retrieval/retrieval_agent.py` | 질의 영어 번역 → 임베딩 → ChromaDB 검색 → 청크 반환 |
| **Answer Agent** | `agent/answer_agent.py` | 사내 문서 + 웹 결과 조합 → GPT → 답변 + 출처 |
| **Poster Agent** | `agent/poster_agent.py` | RAG 검색 → GPT 이미지 프롬프트 → dall-e-3 생성 |
| **Plan Agent** | `agent/plan_agent.py` | RAG 검색 + 채팅 히스토리 → GPT → JSON 플랜 구조 |
| **Naver Search Agent** | `agent/web_search.py` | Naver Search API → 웹 결과 5개 반환 |

## 인덱싱 파이프라인

```
파일 업로드/스캔
    ↓ parse()           — PDF/DOCX/XLSX/TXT → 텍스트
    ↓ chunk_text()      — 800 토큰 단위 청크 분할 (오버랩 150)
    ↓ translate_texts_to_english()  — 병렬 배치 번역 (영어 pivot)
    ↓ embed_texts()     — text-embedding-3-small (100개 배치)
    ↓ save_chunks()     — ChromaDB 저장 (원본 텍스트 + 영어 임베딩)
```

## 질의 파이프라인

```
사용자 질문
    ↓ translate_to_english()     — 질의 영어 번역
    ↓ embed_texts()              — 질의 임베딩
    ↓ ChromaDB 검색 (k=5)
    ↓ [선택] NaverSearchAgent    — 웹 검색 결과 5개
    ↓ AnswerAgent                — GPT 답변 생성
```
