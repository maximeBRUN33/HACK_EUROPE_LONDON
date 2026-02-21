from __future__ import annotations

from fastapi import HTTPException


def api_error(status_code: int, detail_code: str, message: str, **extra: object) -> HTTPException:
    detail = {
        "detail_code": detail_code,
        "message": message,
    }
    if extra:
        detail.update(extra)
    return HTTPException(status_code=status_code, detail=detail)
