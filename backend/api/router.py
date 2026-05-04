from typing import Any, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.ingest.file_scanner import scan_folder, mark_as_ingested
from backend.ingest.parsers import parse
from backend.ingest.chunker import chunk_text
from backend.ingest.embedder import embed_texts
from backend.ingest.db_manager import save_chunks, get_stats
from backend.agent.main_agent import MainAgent

router = APIRouter(tags=["assistant"])


# ── 스키마 ──────────────────────────────────────────────────────────────────

class ApiResponse(BaseModel):
    success: bool
    data: Any
    error: str | None = None


class IngestRequest(BaseModel):
    folder_path: str


class QueryRequest(BaseModel):
    query: str


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
            raw_text = parse(file_info["file_path"])
            chunks = chunk_text(raw_text, file_info["file_path"], file_info["md5_hash"])
            embeddings = embed_texts([c["chunk_text"] for c in chunks])
            saved = save_chunks(chunks, embeddings)
            mark_as_ingested(file_info["file_path"], file_info["md5_hash"])
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
