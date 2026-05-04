# Skill: 모듈 단독 테스트 (test-module)

각 모듈을 독립적으로 테스트하는 표준 패턴.
pytest 기반이며, 환경변수는 반드시 mock으로 처리한다.

---

## 파일 위치 규칙

| 대상 모듈 | 테스트 파일 위치 |
|-----------|-----------------|
| `backend/ingest/parsers/parse_pdf.py` | `tests/ingest/test_parse_pdf.py` |
| `backend/retrieval/search.py` | `tests/retrieval/test_search.py` |
| `backend/agent/ingest_agent.py` | `tests/agent/test_ingest_agent.py` |
| `backend/api/routes/query.py` | `tests/api/test_query.py` |

---

## 표준 테스트 파일 템플릿

```python
# tests/<module>/test_<name>.py

import pytest
from unittest.mock import patch, MagicMock


# --- 환경변수 Mock (모든 테스트 파일 상단에 적용) ---
@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")


# --- 픽스처 ---
@pytest.fixture
def sample_<resource>() -> dict:
    return {
        "field": "value",
    }


# --- 정상 케이스 ---
class Test<ModuleName>:
    def test_<action>_success(self, sample_<resource>: dict) -> None:
        from backend.<module>.<name> import <function>

        result = <function>(sample_<resource>)

        assert result is not None
        assert result["success"] is True

    # --- 외부 의존성 Mock ---
    @patch("backend.<module>.<name>.<ExternalClass>")
    def test_<action>_with_mock(self, mock_external: MagicMock) -> None:
        mock_external.return_value.method.return_value = {"mocked": True}

        from backend.<module>.<name> import <function>

        result = <function>({"input": "test"})

        mock_external.return_value.method.assert_called_once()
        assert result["data"] is not None

    # --- 실패 케이스 ---
    def test_<action>_invalid_input(self) -> None:
        from backend.<module>.<name> import <function>

        result = <function>({"input": ""})

        assert result["success"] is False
        assert result["error"] is not None
```

---

## 환경변수 Mock 규칙

- 실제 API 키를 테스트에 사용하지 않는다.
- `monkeypatch.setenv`를 `autouse=True` 픽스처로 적용하면 파일 내 모든 테스트에 자동 적용된다.
- 외부 API 호출(OpenAI, Anthropic)은 반드시 `unittest.mock.patch`로 차단한다.

```python
# OpenAI 임베딩 호출 Mock 예시
@patch("openai.OpenAI")
def test_embed(self, mock_openai: MagicMock) -> None:
    mock_openai.return_value.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    ...

# Anthropic Claude API 호출 Mock 예시
@patch("anthropic.Anthropic")
def test_answer(self, mock_anthropic: MagicMock) -> None:
    mock_anthropic.return_value.messages.create.return_value = MagicMock(
        content=[MagicMock(text="테스트 답변")]
    )
    ...
```

---

## pytest 실행 명령어

```bash
# 전체 테스트
pytest tests/

# 특정 모듈만
pytest tests/ingest/

# 특정 파일만
pytest tests/ingest/test_parse_pdf.py

# 상세 출력
pytest -v tests/

# 커버리지 포함 (pytest-cov 설치 필요)
pytest --cov=backend tests/
```

---

## conftest.py 패턴 (공통 픽스처 분리)

여러 테스트 파일에서 공통으로 쓰이는 픽스처는 `tests/conftest.py`에 정의한다.

```python
# tests/conftest.py

import pytest


@pytest.fixture(scope="session")
def sample_file_path(tmp_path_factory: pytest.TempPathFactory) -> str:
    tmp = tmp_path_factory.mktemp("data")
    f = tmp / "test.txt"
    f.write_text("테스트 문서 내용입니다.")
    return str(f)
```

---

## 체크리스트 (테스트 파일 추가 시)

- [ ] `tests/<module>/test_<name>.py` 위치에 파일 생성
- [ ] `autouse=True` 픽스처로 환경변수 mock 적용
- [ ] 외부 API 호출을 `@patch`로 차단
- [ ] 정상 케이스 / 실패 케이스 모두 작성
- [ ] `pytest tests/` 로컬 실행 통과 확인
- [ ] `tests/__init__.py` 존재 여부 확인
