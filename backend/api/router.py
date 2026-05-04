import json
import shutil
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.ingest.file_scanner import scan_folder, mark_as_ingested, compute_md5
from backend.ingest.parsers import parse
from backend.ingest.chunker import chunk_text
from backend.ingest.embedder import embed_texts
from backend.ingest.db_manager import save_chunks, get_stats
from backend.agent.main_agent import MainAgent

router = APIRouter(tags=["assistant"])

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".xlsx"}
_HASH_STORE_PATH = Path("data/vectordb/hash_store.json")
_UPLOAD_DIR = Path("data/raw")


# ── 스키마 ──────────────────────────────────────────────────────────────────

class ApiResponse(BaseModel):
    success: bool
    data: Any
    error: str | None = None


class IngestRequest(BaseModel):
    folder_path: str


class QueryRequest(BaseModel):
    query: str


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _is_already_indexed(md5_hash: str) -> bool:
    """hash_store에 동일한 MD5가 있으면 True (내용 기반 중복 판단)."""
    if not _HASH_STORE_PATH.exists():
        return False
    data: dict = json.loads(_HASH_STORE_PATH.read_text(encoding="utf-8"))
    return md5_hash in data.values()


def _ingest_one_file(file_path: str, md5_hash: str) -> int:
    """단일 파일을 파싱 → 청킹 → 임베딩 → DB 저장까지 처리하고 저장된 청크 수를 반환한다."""
    raw_text = parse(file_path)
    chunks = chunk_text(raw_text, file_path, md5_hash)
    embeddings = embed_texts([c["chunk_text"] for c in chunks])
    saved = save_chunks(chunks, embeddings)
    mark_as_ingested(file_path, md5_hash)
    return saved


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def ingest(request: IngestRequest) -> ApiResponse:
    """폴더 경로를 받아 문서 파싱 → 청킹 → 임베딩 → DB 저장 파이프라인을 실행한다."""
    try:
        files = scan_folder(request.folder_path)

        if not files:
            return ApiResponse(
                success=True,
                data={"processed_files": 0, "total_chunks": 0, "db_total_chunks": get_stats()["total_chunks"]},
            )

        total_files = 0
        total_chunks = 0

        for file_info in files:
            saved = _ingest_one_file(file_info["file_path"], file_info["md5_hash"])
            total_files += 1
            total_chunks += saved

        stats = get_stats()
        return ApiResponse(
            success=True,
            data={
                "processed_files": total_files,
                "total_chunks": total_chunks,
                "db_total_chunks": stats["total_chunks"],
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def upload_file(file: UploadFile = File(...)) -> ApiResponse:
    """
    단일 파일을 업로드하고 즉시 인덱싱한다.

    중복 처리:
    - 동일 내용(MD5 일치): 인덱싱 건너뜀, duplicate=True 반환
    - 동일 파일명이지만 내용이 다른 경우: 새 MD5로 새 청크가 추가되며
      이전 청크는 ChromaDB에 잔존할 수 있음 (ChromaDB upsert 특성)
    """
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            return ApiResponse(
                success=False,
                data=None,
                error=f"지원하지 않는 파일 형식입니다: {suffix} (지원: pdf, docx, txt, xlsx)",
            )

        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        save_path = _UPLOAD_DIR / file.filename

        with save_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        md5_hash = compute_md5(str(save_path))

        if _is_already_indexed(md5_hash):
            return ApiResponse(
                success=True,
                data={
                    "filename": file.filename,
                    "chunks": 0,
                    "duplicate": True,
                    "db_total_chunks": get_stats()["total_chunks"],
                },
            )

        saved = _ingest_one_file(str(save_path), md5_hash)
        stats = get_stats()
        return ApiResponse(
            success=True,
            data={
                "filename": file.filename,
                "chunks": saved,
                "duplicate": False,
                "db_total_chunks": stats["total_chunks"],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/query", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def query(request: QueryRequest) -> ApiResponse:
    """질문을 받아 벡터 검색 + LLM 답변 생성 후 답변과 출처를 반환한다."""
    try:
        if not request.query.strip():
            raise ValueError("질문 내용이 비어 있습니다.")

        agent = MainAgent()
        result = agent.query(request.query)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def get_status() -> ApiResponse:
    """ChromaDB에 저장된 총 청크 수를 반환한다."""
    try:
        stats = get_stats()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
