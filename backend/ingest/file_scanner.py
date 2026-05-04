import hashlib
import json
from pathlib import Path
from typing import List, Dict

SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".xlsx"}
_HASH_STORE_PATH = Path("data/vectordb/hash_store.json")


def compute_md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _load_hash_store() -> dict:
    if _HASH_STORE_PATH.exists():
        return json.loads(_HASH_STORE_PATH.read_text(encoding="utf-8"))
    return {}


def mark_as_ingested(file_path: str, md5_hash: str) -> None:
    store = _load_hash_store()
    store[file_path] = md5_hash
    _HASH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _HASH_STORE_PATH.write_text(
        json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def scan_folder(folder_path: str) -> List[Dict]:
    """
    지정 폴더를 재귀 스캔하여 처리 대상 파일 목록을 반환한다.
    이미 동일 MD5로 처리된 파일은 스킵한다.

    Returns:
        List[Dict]: file_path, file_type, md5_hash
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")

    hash_store = _load_hash_store()
    results: List[Dict] = []

    for file in sorted(folder.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        path_str = str(file.resolve())
        md5 = compute_md5(path_str)

        if hash_store.get(path_str) == md5:
            print(f"  [SKIP] {file.name} (변경 없음)")
            continue

        results.append({
            "file_path": path_str,
            "file_type": file.suffix.lstrip(".").lower(),
            "md5_hash": md5,
        })
        print(f"  [SCAN] {file.name} ({file.suffix.upper()})")

    return results


if __name__ == "__main__":
    import sys

    folder = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    found = scan_folder(folder)
    print(f"\n처리 대상 파일: {len(found)}개")
    for f in found:
        print(f"  {f['file_type'].upper()} | {f['file_path']}")
