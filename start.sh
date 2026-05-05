#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

# 종료 시 백그라운드 백엔드도 함께 정리
cleanup() {
    echo ""
    echo "서버를 종료합니다..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# 기존 포트 점유 프로세스 정리
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

echo "백엔드 시작 중..."
uvicorn backend.api.main:app --reload &
BACKEND_PID=$!
sleep 2

open http://localhost:8501 2>/dev/null || true

echo "프론트엔드 시작 중..."
streamlit run frontend/app.py
