"""
Phase 1 CLI 진입점.

프로젝트 루트에서 실행:
    python backend/ingest/run_ingest.py --folder data/raw
"""
import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (패키지 외부 실행 지원)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv()

from backend.ingest.file_scanner import scan_folder, mark_as_ingested
from backend.ingest.parsers import parse
from backend.ingest.chunker import chunk_text
from backend.ingest.embedder import embed_texts
from backend.ingest.db_manager import save_chunks, get_stats


def run(folder_path: str) -> None:
    print(f"\n{'='*50}")
    print(f" Ingest 시작: {folder_path}")
    print(f"{'='*50}\n")

    # 1. 파일 스캔 (중복 파일 자동 스킵)
    print("[1/5] 파일 스캔 중...")
    files = scan_folder(folder_path)

    if not files:
        print("\n처리할 새 파일이 없습니다. 종료합니다.")
        return

    print(f"      → {len(files)}개 파일 처리 예정\n")

    total_files = 0
    total_chunks = 0

    for file_info in files:
        file_path = file_info["file_path"]
        file_name = Path(file_path).name

        print(f"┌─ {file_name}")

        # 2. 텍스트 추출
        print("│  [2/5] 파싱 중...")
        raw_text = parse(file_path)
        print(f"│        추출 완료: {len(raw_text):,}자")

        # 3. 청크 분할
        print("│  [3/5] 청킹 중...")
        chunks = chunk_text(
            raw_text,
            source_file=file_path,
            md5_hash=file_info["md5_hash"],
        )
        print(f"│        {len(chunks)}개 청크 생성")

        # 4. 임베딩
        print("│  [4/5] 임베딩 중...")
        texts = [c["chunk_text"] for c in chunks]
        embeddings = embed_texts(texts)

        # 5. DB 저장
        print("│  [5/5] DB 저장 중...")
        saved = save_chunks(chunks, embeddings)
        print(f"│        {saved}개 청크 저장 완료")

        mark_as_ingested(file_path, file_info["md5_hash"])
        total_files += 1
        total_chunks += saved
        print(f"└─ 완료\n")

    # 최종 요약
    stats = get_stats()
    print(f"{'='*50}")
    print(f" Ingest 완료")
    print(f"{'='*50}")
    print(f"  처리 파일  : {total_files}개")
    print(f"  총 청크    : {total_chunks}개")
    print(f"  DB 누적 청크: {stats['total_chunks']}개")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="문서 폴더를 ChromaDB에 인제스트합니다.")
    parser.add_argument(
        "--folder",
        type=str,
        default="data/raw",
        help="스캔할 폴더 경로 (기본값: data/raw)",
    )
    args = parser.parse_args()
    run(args.folder)
