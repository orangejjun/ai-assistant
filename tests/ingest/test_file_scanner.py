import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def patch_hash_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.ingest.file_scanner as fs
    monkeypatch.setattr(fs, "_HASH_STORE_PATH", tmp_path / "hash_store.json")


@pytest.fixture
def scan_dir(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "report.txt").write_text("보고서 내용입니다.", encoding="utf-8")
    (d / "readme.md").write_text("마크다운 파일 — 스캔 대상 아님", encoding="utf-8")
    return d


class TestScanFolder:
    def test_returns_supported_file(self, scan_dir: Path) -> None:
        from backend.ingest.file_scanner import scan_folder

        result = scan_folder(str(scan_dir))

        assert len(result) == 1
        assert result[0]["file_type"] == "txt"

    def test_result_contains_required_keys(self, scan_dir: Path) -> None:
        from backend.ingest.file_scanner import scan_folder

        result = scan_folder(str(scan_dir))

        assert "file_path" in result[0]
        assert "file_type" in result[0]
        assert "md5_hash" in result[0]

    def test_ignores_unsupported_extensions(self, scan_dir: Path) -> None:
        from backend.ingest.file_scanner import scan_folder

        result = scan_folder(str(scan_dir))

        extensions = [r["file_type"] for r in result]
        assert "md" not in extensions

    def test_scans_subdirectories_recursively(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import scan_folder

        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("중첩 폴더 파일", encoding="utf-8")

        result = scan_folder(str(tmp_path))

        assert len(result) == 1
        assert "nested.txt" in result[0]["file_path"]

    def test_raises_for_nonexistent_folder(self) -> None:
        from backend.ingest.file_scanner import scan_folder

        with pytest.raises(FileNotFoundError):
            scan_folder("/nonexistent/path/12345")

    def test_skips_already_ingested_file(
        self, scan_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import backend.ingest.file_scanner as fs
        from backend.ingest.file_scanner import scan_folder, compute_md5, mark_as_ingested

        txt_path = str((scan_dir / "report.txt").resolve())
        md5 = compute_md5(txt_path)
        mark_as_ingested(txt_path, md5)

        result = scan_folder(str(scan_dir))

        assert result == []

    def test_includes_file_after_content_change(
        self, scan_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from backend.ingest.file_scanner import scan_folder, compute_md5, mark_as_ingested

        txt_file = scan_dir / "report.txt"
        txt_path = str(txt_file.resolve())
        old_md5 = compute_md5(txt_path)
        mark_as_ingested(txt_path, old_md5)

        # 파일 내용 변경
        txt_file.write_text("완전히 바뀐 내용", encoding="utf-8")

        result = scan_folder(str(scan_dir))

        assert len(result) == 1
        assert result[0]["md5_hash"] != old_md5

    def test_returns_empty_for_empty_folder(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import scan_folder

        result = scan_folder(str(tmp_path))

        assert result == []


class TestComputeMd5:
    def test_deterministic_for_same_file(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import compute_md5

        f = tmp_path / "a.txt"
        f.write_text("동일한 내용", encoding="utf-8")

        assert compute_md5(str(f)) == compute_md5(str(f))

    def test_different_for_different_content(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import compute_md5

        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("내용 A", encoding="utf-8")
        f2.write_text("내용 B", encoding="utf-8")

        assert compute_md5(str(f1)) != compute_md5(str(f2))

    def test_returns_32_char_hex_string(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import compute_md5

        f = tmp_path / "a.txt"
        f.write_bytes(b"test")

        result = compute_md5(str(f))

        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)


class TestMarkAsIngested:
    def test_persists_to_json(self, tmp_path: Path) -> None:
        import backend.ingest.file_scanner as fs
        from backend.ingest.file_scanner import mark_as_ingested

        hash_store_path = tmp_path / "hash_store.json"

        mark_as_ingested("/some/file.txt", "abc123")

        assert hash_store_path.exists()
        data = json.loads(hash_store_path.read_text())
        assert data["/some/file.txt"] == "abc123"

    def test_overwrites_existing_entry(self, tmp_path: Path) -> None:
        from backend.ingest.file_scanner import mark_as_ingested
        import backend.ingest.file_scanner as fs

        mark_as_ingested("/file.txt", "old_hash")
        mark_as_ingested("/file.txt", "new_hash")

        data = json.loads(fs._HASH_STORE_PATH.read_text())
        assert data["/file.txt"] == "new_hash"
