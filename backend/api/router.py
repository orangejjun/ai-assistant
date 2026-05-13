import asyncio
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.ingest.file_scanner import scan_folder, mark_as_ingested, compute_md5, remove_from_hash_store
from backend.ingest.parsers import parse
from backend.ingest.chunker import chunk_text
from backend.ingest.embedder import embed_texts
from backend.ingest.translator import translate_texts_to_english
from backend.ingest.db_manager import save_chunks, get_stats, reset_collection, delete_by_source_file
from backend.agent.main_agent import MainAgent
from backend.agent.poster_agent import PosterAgent
from backend.agent.ppt_agent import PptAgent
from backend.agent.plan_agent import PlanAgent
from backend.agent.suggestion_agent import SuggestionAgent
from backend.agent.email_draft_agent import EmailDraftAgent
from backend.agent.email_recipient_agent import EmailRecipientAgent
from backend.agent.email_sender_agent import EmailSenderAgent
from backend.memory.history_manager import (
    save_session,
    load_session,
    list_sessions,
    rename_session,
    delete_session,
)

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
    use_web_search: bool = False
    session_id: str = ""
    chat_history: List[Dict] = []


class DeleteRequest(BaseModel):
    source_file: str


class PosterRequest(BaseModel):
    topic: str
    size: str = "1024x1536"


class PptRequest(BaseModel):
    topic: str
    num_slides: int = 5


class PlanRequest(BaseModel):
    goal: str
    chat_history: List[Dict] = []


class SaveHistoryRequest(BaseModel):
    session_id: str
    messages: List[Dict]


class RenameHistoryRequest(BaseModel):
    title: str


class EmailDraftRequest(BaseModel):
    messages: List[Dict]


class EmailRecipientsRequest(BaseModel):
    subject: str
    body: str


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _is_already_indexed(md5_hash: str) -> bool:
    """hash_store에 동일한 MD5가 있으면 True (내용 기반 중복 판단)."""
    if not _HASH_STORE_PATH.exists():
        return False
    data: dict = json.loads(_HASH_STORE_PATH.read_text(encoding="utf-8"))
    return md5_hash in data.values()


def _ingest_one_file(file_path: str, md5_hash: str) -> int:
    """단일 파일을 파싱 → 청킹 → 영어 번역 → 임베딩 → DB 저장까지 처리하고 저장된 청크 수를 반환한다.

    임베딩은 영어 번역본으로 생성하고, ChromaDB에는 원본 텍스트를 저장한다.
    이를 통해 질의 언어와 문서 언어가 달라도 유사도 검색이 정확하게 동작한다.
    """
    raw_text = parse(file_path)
    chunks = chunk_text(raw_text, file_path, md5_hash)
    translated_texts = translate_texts_to_english([c["chunk_text"] for c in chunks])
    embeddings = embed_texts(translated_texts)
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

        saved = await asyncio.to_thread(_ingest_one_file, str(save_path), md5_hash)
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
        result = agent.query(
            request.query,
            use_web_search=request.use_web_search,
            session_id=request.session_id,
            chat_history=request.chat_history,
        )

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


@router.get("/files", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def list_files() -> ApiResponse:
    """인덱싱된 파일 목록을 반환한다."""
    try:
        if not _HASH_STORE_PATH.exists():
            return ApiResponse(success=True, data={"files": []})
        store: dict = json.loads(_HASH_STORE_PATH.read_text(encoding="utf-8"))
        files = [
            {"source_file": k, "filename": Path(k).name}
            for k in store.keys()
        ]
        return ApiResponse(success=True, data={"files": files})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/files", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def delete_file(request: DeleteRequest) -> ApiResponse:
    """
    source_file 기준으로 ChromaDB 청크를 삭제하고, hash_store에서 제거한 뒤
    원본 파일을 data/trash/ 폴더로 이동한다.
    """
    try:
        source_file = request.source_file
        file_path = Path(source_file)

        deleted_chunks = await asyncio.to_thread(delete_by_source_file, source_file)
        remove_from_hash_store(source_file)

        moved_to: str | None = None
        if file_path.exists():
            trash_dir = Path("data/trash")
            trash_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = trash_dir / f"{timestamp}_{file_path.name}"
            shutil.move(str(file_path), str(dest))
            moved_to = str(dest)

        return ApiResponse(
            success=True,
            data={
                "filename": file_path.name,
                "deleted_chunks": deleted_chunks,
                "moved_to": moved_to,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/poster", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def create_poster(request: PosterRequest) -> ApiResponse:
    """주제를 입력받아 관련 문서를 검색하고 gpt-image-2로 포스터 이미지를 생성한다."""
    try:
        if not request.topic.strip():
            raise ValueError("주제가 비어 있습니다.")
        agent = PosterAgent()
        result = await asyncio.to_thread(agent.run, {"topic": request.topic, "size": request.size})
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ppt", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def create_ppt(request: PptRequest) -> ApiResponse:
    """주제를 입력받아 관련 문서를 검색하고 python-pptx로 프레젠테이션을 생성한다."""
    try:
        if not request.topic.strip():
            raise ValueError("주제가 비어 있습니다.")
        agent = PptAgent()
        result = await asyncio.to_thread(
            agent.run, {"topic": request.topic, "num_slides": request.num_slides}
        )
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/plan", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def create_plan(request: PlanRequest) -> ApiResponse:
    """프로젝트 목표와 채팅 히스토리를 받아 문서 기반 프로젝트 플랜 마크다운을 생성한다."""
    try:
        if not request.goal.strip():
            raise ValueError("프로젝트 목표가 비어 있습니다.")
        agent = PlanAgent()
        result = await asyncio.to_thread(
            agent.run,
            {"goal": request.goal, "chat_history": request.chat_history},
        )
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/history", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def save_history(request: SaveHistoryRequest) -> ApiResponse:
    """세션 대화 이력을 data/history/{session_id}.json 에 저장한다."""
    try:
        await asyncio.to_thread(save_session, request.session_id, request.messages)
        return ApiResponse(success=True, data={"session_id": request.session_id})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def get_history_list() -> ApiResponse:
    """저장된 세션 목록을 최신순으로 반환한다."""
    try:
        sessions = await asyncio.to_thread(list_sessions)
        return ApiResponse(success=True, data={"sessions": sessions})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/{session_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def get_history(session_id: str) -> ApiResponse:
    """특정 세션의 대화 이력을 반환한다."""
    try:
        data = await asyncio.to_thread(load_session, session_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
        return ApiResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/history/{session_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def rename_history(session_id: str, request: RenameHistoryRequest) -> ApiResponse:
    """세션 제목을 수정한다."""
    try:
        ok = await asyncio.to_thread(rename_session, session_id, request.title)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
        return ApiResponse(success=True, data={"session_id": session_id, "title": request.title})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/history/{session_id}", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def remove_history(session_id: str) -> ApiResponse:
    """특정 세션 파일을 삭제한다."""
    try:
        deleted = await asyncio.to_thread(delete_session, session_id)
        return ApiResponse(success=True, data={"session_id": session_id, "deleted": deleted})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/suggestions", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def get_suggestions() -> ApiResponse:
    """인덱싱된 문서에서 랜덤 샘플링 후 GPT로 추천 질문 3개를 생성한다."""
    try:
        agent = SuggestionAgent()
        result = await asyncio.to_thread(agent.run, {})
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
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


@router.post("/email/draft", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def email_draft(request: EmailDraftRequest) -> ApiResponse:
    """채팅 이력을 받아 RAG 기반 이메일 초안(제목+본문)을 생성한다."""
    try:
        if not request.messages:
            raise ValueError("messages가 비어 있습니다.")
        agent = EmailDraftAgent()
        result = await asyncio.to_thread(agent.run, {"messages": request.messages})
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/email/recipients", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def email_recipients(request: EmailRecipientsRequest) -> ApiResponse:
    """이메일 제목/본문을 분석하여 사내 contacts 기반 CC 수신자를 추천한다."""
    try:
        agent = EmailRecipientAgent()
        result = await asyncio.to_thread(
            agent.run, {"subject": request.subject, "body": request.body}
        )
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/email/send", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def email_send(
    to: str = Form(...),
    cc: str = Form(""),
    subject: str = Form(...),
    body: str = Form(...),
    attachments: List[UploadFile] = File(default=[]),
) -> ApiResponse:
    """이메일을 Gmail SMTP로 전송한다. 파일 첨부 포함."""
    try:
        if not to.strip():
            raise ValueError("수신자(to)가 비어 있습니다.")
        if not subject.strip():
            raise ValueError("제목(subject)이 비어 있습니다.")

        cc_list = [addr.strip() for addr in cc.split(",") if addr.strip()]
        attachment_list = []
        for att in attachments:
            if att.filename:
                content = await att.read()
                attachment_list.append(
                    {
                        "filename": att.filename,
                        "content": content,
                        "mimetype": att.content_type or "application/octet-stream",
                    }
                )

        agent = EmailSenderAgent()
        result = await asyncio.to_thread(
            agent.run,
            {
                "to": to,
                "cc": cc_list,
                "subject": subject,
                "body": body,
                "attachments": attachment_list,
            },
        )
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
        return ApiResponse(success=True, data=result["data"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
