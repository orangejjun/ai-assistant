# 개발 Phase & Progress

| Phase | 내용 |
|-------|------|
| Phase 1 | 문서 파싱 + 청크 분할 + 임베딩 + ChromaDB 저장 (CLI) |
| Phase 2 | 벡터 검색 + GPT 답변 생성 |
| Phase 3 | Streamlit UI + FastAPI 백엔드 |
| Phase 4 | Docker + 클라우드 배포 |
| Phase 5 | UI 파일 업로드 + 단일 파일 인덱싱 API (POST /upload) |
| Phase 6 | 영어 Pivot 번역 — Cross-lingual Retrieval 해결 |
| Phase 7 | 파일 삭제 기능 — 휴지통 방식 (GET /files, DELETE /files) |
| Phase 8 | start.sh 자동 실행 스크립트 |
| Phase 9 | dall-e-3 포스터 생성 (POST /poster, 포스터 탭) |
| Phase 10 | 문서 + 채팅 히스토리 기반 인터랙티브 TODO 플랜 생성 (POST /plan, 플랜 탭) |
| Phase 11 | Naver 웹 검색 연동 — 채팅 토글로 선택 활성화 |
| Phase 12 | 번역 병렬 배치 처리 + 토큰/청크 크기 최적화 |
| Phase 15 | python-pptx PPT 생성 (POST /ppt, PPT 탭) |
| Phase 16 | Resend API 실제 이메일 발송 (개인 메일 계정 불필요) |

## Progress

- [x] Phase 1 — 문서 파싱, 청크, 임베딩, ChromaDB 저장 (CLI) ✅ 2026-05-04
- [x] Phase 2 — 벡터 검색, GPT 답변 생성 ✅ 2026-05-04
- [x] Phase 3 — Streamlit UI, FastAPI 백엔드 ✅ 2026-05-04
- [x] Phase 4 — Docker, 클라우드 배포 ✅ 2026-05-04
- [x] Phase 5 — UI 파일 업로드, POST /upload 엔드포인트, MD5 중복 방지 ✅ 2026-05-05
- [x] Phase 6 — 영어 Pivot 번역, translator.py, 전체 재인덱싱 ✅ 2026-05-05
- [x] Phase 7 — 파일 삭제(휴지통), GET /files, DELETE /files, .gitignore 정비 ✅ 2026-05-05
- [x] Phase 8 — start.sh 자동 실행 스크립트 ✅ 2026-05-05
- [x] Phase 9 — dall-e-3 포스터 생성, POST /poster, 포스터 탭 ✅ 2026-05-08
- [x] Phase 10 — 인터랙티브 TODO 플랜 생성, POST /plan, 플랜 탭 ✅ 2026-05-08
- [x] Phase 11 — Naver 웹 검색 연동, NaverSearchAgent, 채팅 토글 ✅ 2026-05-08
- [x] Phase 12 — 번역 병렬 배치 처리, 토큰/청크 크기 최적화 ✅ 2026-05-08
- [x] Phase 15 — python-pptx PPT 생성, POST /ppt, PPT 탭 ✅ 2026-05-12
- [x] Phase 16 — Resend API 실제 이메일 발송, email_sender_agent.py 교체 ✅ 2026-05-13
