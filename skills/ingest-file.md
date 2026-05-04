# Skill: 새 파일 파서 추가 (ingest-file)

새로운 파일 형식을 지원할 때 따라야 할 표준 구조.
모든 파서는 이 패턴을 준수해야 한다.

---

## 입력 / 출력 계약

```
입력: file_path: str
출력: List[Dict]  # 각 Dict는 chunk 1개를 나타냄
```

### 출력 Dict 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `chunk_text` | `str` | 분할된 텍스트 본문 |
| `metadata` | `dict` | 출처 정보 (아래 참고) |

### metadata 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `source_path` | `str` | 원본 파일 절대 경로 |
| `file_name` | `str` | 파일명 |
| `file_type` | `str` | 확장자 (예: `"pdf"`) |
| `chunk_index` | `int` | 청크 순번 (0부터) |
| `md5_hash` | `str` | 파일 전체의 MD5 해시 |

---

## 표준 파서 템플릿

```python
# backend/ingest/parsers/parse_<filetype>.py

import hashlib
from pathlib import Path
from typing import List, Dict


CHUNK_SIZE = 500      # 청크당 최대 문자 수
CHUNK_OVERLAP = 50    # 청크 간 중복 문자 수


def compute_md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_<filetype>(file_path: str) -> List[Dict]:
    """
    <FileType> 파일을 파싱하여 청크 리스트를 반환한다.

    Args:
        file_path: 파싱할 파일의 절대 경로

    Returns:
        List[Dict]: chunk_text와 metadata를 포함한 청크 리스트
    """
    path = Path(file_path)
    md5 = compute_md5(file_path)

    # --- 1. 파일 읽기 ---
    raw_text = _read_file(path)

    # --- 2. 전처리 ---
    clean_text = _preprocess(raw_text)

    # --- 3. 청크 분할 ---
    chunks = _split_chunks(clean_text, CHUNK_SIZE, CHUNK_OVERLAP)

    # --- 4. 메타데이터 조합 ---
    return [
        {
            "chunk_text": chunk,
            "metadata": {
                "source_path": str(path.resolve()),
                "file_name": path.name,
                "file_type": path.suffix.lstrip(".").lower(),
                "chunk_index": idx,
                "md5_hash": md5,
            },
        }
        for idx, chunk in enumerate(chunks)
    ]


def _read_file(path: Path) -> str:
    # 파일 형식에 맞는 읽기 로직 구현
    raise NotImplementedError


def _preprocess(text: str) -> str:
    # 공백 정규화, 불필요한 문자 제거 등
    return " ".join(text.split())


def _split_chunks(text: str, size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


if __name__ == "__main__":
    import sys
    results = parse_<filetype>(sys.argv[1])
    for r in results:
        print(r["metadata"], "|", r["chunk_text"][:80])
```

---

## MD5 해시 중복 체크 패턴

임베딩 전에 반드시 아래 로직으로 중복 여부를 확인한다.

```python
# backend/ingest/dedup.py

import json
from pathlib import Path

HASH_STORE_PATH = Path("data/vectordb/hash_store.json")


def load_hash_store() -> dict:
    if HASH_STORE_PATH.exists():
        return json.loads(HASH_STORE_PATH.read_text())
    return {}


def save_hash_store(store: dict) -> None:
    HASH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASH_STORE_PATH.write_text(json.dumps(store, indent=2))


def is_already_ingested(file_path: str, md5: str) -> bool:
    store = load_hash_store()
    return store.get(file_path) == md5


def mark_as_ingested(file_path: str, md5: str) -> None:
    store = load_hash_store()
    store[file_path] = md5
    save_hash_store(store)
```

### 사용 예시

```python
from backend.ingest.dedup import is_already_ingested, mark_as_ingested
from backend.ingest.parsers.parse_pdf import parse_pdf, compute_md5

file_path = "data/raw/example.pdf"
md5 = compute_md5(file_path)

if is_already_ingested(file_path, md5):
    print("변경 없음 — 임베딩 스킵")
else:
    chunks = parse_pdf(file_path)
    # ... 임베딩 및 DB 저장 ...
    mark_as_ingested(file_path, md5)
```

---

## 체크리스트 (새 파서 추가 시)

- [ ] `backend/ingest/parsers/parse_<filetype>.py` 파일 생성
- [ ] `parse_<filetype>` 함수가 `List[Dict]` 반환 계약을 준수하는지 확인
- [ ] `compute_md5` 재사용 또는 `dedup.py` 연동 확인
- [ ] `if __name__ == "__main__":` 블록으로 단독 실행 가능 여부 확인
- [ ] `backend/ingest/__init__.py`에 파서 등록
