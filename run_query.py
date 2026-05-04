"""
Phase 2 CLI 진입점.

프로젝트 루트에서 실행:
    python run_query.py --query "연차 휴가는 몇 일 전에 신청해야 하나요?"
    python run_query.py --query "연차 휴가는 몇 일 전에 신청해야 하나요?" --debug
"""
import argparse
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv()

from backend.agent.main_agent import MainAgent


def _print_debug_chunks(chunks: List[Dict]) -> None:
    print(f"\n[DEBUG] 검색된 청크 {len(chunks)}개")
    for i, chunk in enumerate(chunks, 1):
        source = Path(chunk.get("source_file", "알 수 없음")).name
        distance = chunk.get("distance", 0.0)
        print(f"--- 청크 {i} (출처: {source}, 거리: {distance:.3f}) ---")
        print(chunk.get("chunk_text", ""))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="사내 문서 기반 질의응답")
    parser.add_argument("--query", type=str, required=True, help="질문 내용")
    parser.add_argument("--debug", action="store_true", help="검색된 청크를 답변 전에 출력")
    args = parser.parse_args()

    print(f"\n질문: {args.query}\n{'─' * 50}")

    agent = MainAgent()

    if args.debug:
        # 검색과 답변을 분리 실행하여 중간 결과 출력
        ret = agent.route("retrieval", {"query": args.query})
        if not ret["success"]:
            print(f"오류: {ret['error']}")
            raise SystemExit(1)

        chunks = ret["data"]["chunks"]
        _print_debug_chunks(chunks)

        ans = agent.route("answer", {"query": args.query, "chunks": chunks})
        if not ans["success"]:
            print(f"오류: {ans['error']}")
            raise SystemExit(1)

        data = ans["data"]
    else:
        result = agent.query(args.query)
        if not result["success"]:
            print(f"오류: {result['error']}")
            raise SystemExit(1)
        data = result["data"]

    print(f"[답변]\n{data['answer']}\n")

    if data["sources"]:
        print("[출처]")
        for src in data["sources"]:
            print(f"  - {src}")
    else:
        print("[출처] 없음")


if __name__ == "__main__":
    main()
