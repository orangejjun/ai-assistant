from typing import List, Dict

# 1 토큰 ≈ 4자 (영문 기준 근사치). 한글 위주 문서는 이 값을 2~3으로 줄이면 토큰 수 추정이 더 정확해진다.
_CHARS_PER_TOKEN = 4
CHUNK_SIZE: int = 800 * _CHARS_PER_TOKEN   # ≈ 800 tokens → 3200자
OVERLAP_SIZE: int = 150 * _CHARS_PER_TOKEN  # ≈ 150 tokens → 600자


def chunk_text(text: str, source_file: str, md5_hash: str) -> List[Dict]:
    """
    텍스트를 일정 크기의 청크로 분할한다.

    Args:
        text: 분할할 원본 텍스트
        source_file: 원본 파일 경로 (메타데이터용)
        md5_hash: 원본 파일 MD5 (메타데이터용)

    Returns:
        List[Dict]: chunk_text, chunk_index, source_file, md5_hash
    """
    clean = _preprocess(text)
    raw_chunks = _split(clean, CHUNK_SIZE, OVERLAP_SIZE)

    return [
        {
            "chunk_text": chunk,
            "chunk_index": idx,
            "source_file": source_file,
            "md5_hash": md5_hash,
        }
        for idx, chunk in enumerate(raw_chunks)
    ]


def _preprocess(text: str) -> str:
    return " ".join(text.split())


def _split(text: str, size: int, overlap: int) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += size - overlap
    return chunks


if __name__ == "__main__":
    sample = "안녕하세요. 이것은 청킹 동작을 확인하기 위한 테스트 문장입니다. " * 200
    result = chunk_text(sample, source_file="test.txt", md5_hash="abc123")
    print(f"입력: {len(sample)}자 → {len(result)}개 청크 (CHUNK={CHUNK_SIZE}자, OVERLAP={OVERLAP_SIZE}자)")
    for c in result[:3]:
        print(f"  [{c['chunk_index']}] {len(c['chunk_text'])}자 | {c['chunk_text'][:60]}...")
