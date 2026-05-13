# AI Assistant — 사내 문서 기반 RAG 비서

사내 문서를 벡터 DB에 인덱싱하고, 자연어 질의에 RAG + GPT로 답변하는 시스템.

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 런타임 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 임베딩 | OpenAI `text-embedding-3-small` |
| 벡터 DB | ChromaDB (로컬) |
| LLM | OpenAI `gpt-4o-mini` |
| 이미지 생성 | OpenAI `dall-e-3` |
| PPT 생성 | `python-pptx` |
| 웹 검색 | Naver Search API |
| 이메일 발송 | Resend API |
| 프론트엔드 | Streamlit |

## 환경변수 (.env)

| 변수 | 용도 |
|------|------|
| `OPENAI_API_KEY` | GPT, 임베딩, dall-e-3 |
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

- 임베딩은 **영어 번역본**으로 생성, ChromaDB에는 **원본** 저장 (Cross-lingual Retrieval)
- MD5 해시로 중복 인덱싱 방지 (`hash_store.json`)
- 번역: 20개 배치 + `ThreadPoolExecutor(max_workers=10)` 병렬 처리
- 대화 메모리: `data/history/{session_id}.json` + ChromaDB `conversation_memory` 컬렉션 (Phase 18)
  - 유사도 임계값: distance < 0.6 (너무 먼 과거 대화 자동 제외)
  - 메모리 저장 실패는 무시 (답변 흐름 방해하지 않음)

---

> 아키텍처 상세 → `docs/architecture.md`
> Phase 목록 및 진행 현황 → `docs/phases.md`
