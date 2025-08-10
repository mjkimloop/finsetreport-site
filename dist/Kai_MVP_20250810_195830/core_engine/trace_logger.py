# core_engine/trace_logger.py
from __future__ import annotations

import json
import os
from datetime import datetime
from uuid import uuid4
from typing import Any, Optional

_TRACE_DIR = os.path.join("output", "_trace")
_CURRENT_TRACE_PATH: Optional[str] = None

def _ensure_trace_dir() -> None:
    os.makedirs(_TRACE_DIR, exist_ok=True)

def new_trace() -> str:
    """
    새로운 트레이스 세션 시작. jsonl 파일 경로를 반환.
    """
    global _CURRENT_TRACE_PATH
    _ensure_trace_dir()
    name = f"{uuid4().hex}.jsonl"
    _CURRENT_TRACE_PATH = os.path.join(_TRACE_DIR, name)
    # 헤더 라인(옵션)
    with open(_CURRENT_TRACE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"_event": "trace_start", "ts": _ts() }, ensure_ascii=False) + "\n")
    return _CURRENT_TRACE_PATH

def get_trace_path() -> Optional[str]:
    return _CURRENT_TRACE_PATH

def trace_log(payload: Any) -> None:
    """
    현재 트레이스 파일에 한 줄(jsonl) 추가.
    """
    if not _CURRENT_TRACE_PATH:
        # 안전장치: 없으면 자동으로 하나 만들기
        new_trace()
    rec = {
        "ts": _ts(),
        "payload": _to_dict(payload),
    }
    with open(_CURRENT_TRACE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _to_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x

def _ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")