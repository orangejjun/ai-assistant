from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router

app = FastAPI(
    title="AI 문서 비서 API",
    description="사내 문서 기반 RAG 질의응답 서비스",
    version="0.1.0",
)

# Streamlit(기본 8501)과의 연동을 위해 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"status": "ok", "docs": "/docs"}
