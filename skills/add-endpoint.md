# Skill: FastAPI 엔드포인트 추가 (add-endpoint)

새로운 API 엔드포인트를 추가할 때 따라야 할 표준 보일러플레이트.

---

## 파일 위치 규칙

| 역할 | 경로 |
|------|------|
| 라우터 파일 | `backend/api/routes/<domain>.py` |
| 라우터 등록 | `backend/api/main.py` |
| 스키마(요청/응답) | `backend/api/schemas/<domain>.py` |

---

## 표준 라우터 템플릿

```python
# backend/api/routes/<domain>.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/<domain>", tags=["<domain>"])


# --- 요청 스키마 ---
class <Domain>Request(BaseModel):
    field_name: str


# --- 응답 스키마 ---
class <Domain>Response(BaseModel):
    success: bool
    data: Any
    error: str | None = None


# --- 엔드포인트 ---
@router.post("/", response_model=<Domain>Response, status_code=status.HTTP_200_OK)
async def handle_<domain>(request: <Domain>Request) -> <Domain>Response:
    try:
        result = _process(request.field_name)
        return <Domain>Response(success=True, data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _process(value: str) -> dict:
    # 실제 비즈니스 로직
    raise NotImplementedError
```

---

## main.py 라우터 등록

```python
# backend/api/main.py

from fastapi import FastAPI
from backend.api.routes.<domain> import router as <domain>_router

app = FastAPI(title="AI Assistant API")

app.include_router(<domain>_router)
```

---

## JSON 응답 구조 규칙

모든 엔드포인트는 아래 구조를 반환한다. 성공/실패 모두 동일한 포맷을 유지한다.

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

실패 시:
```json
{
  "success": false,
  "data": null,
  "error": "에러 메시지"
}
```

---

## 에러 핸들링 규칙

| 상황 | HTTP 코드 | 처리 방법 |
|------|-----------|-----------|
| 잘못된 입력값 | `400` | `ValueError` → `HTTPException(400)` |
| 리소스 없음 | `404` | `KeyError` → `HTTPException(404)` |
| 서버 내부 오류 | `500` | `Exception` → `HTTPException(500)` |

- 예외 메시지에 내부 스택 트레이스를 그대로 노출하지 않는다.
- 로깅은 서버 측에서 처리하고, 클라이언트에는 간결한 메시지만 반환한다.

---

## 체크리스트 (엔드포인트 추가 시)

- [ ] `backend/api/routes/<domain>.py` 파일 생성
- [ ] 요청/응답 스키마를 `BaseModel`로 정의
- [ ] `success / data / error` 응답 구조 준수
- [ ] `try/except`로 에러 핸들링 적용
- [ ] `backend/api/main.py`에 `include_router` 등록
- [ ] 환경변수 하드코딩 없음 확인
