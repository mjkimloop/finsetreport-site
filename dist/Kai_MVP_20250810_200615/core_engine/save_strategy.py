# core_engine/save_strategy.py
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Any, Dict
try:
    from pydantic import BaseModel  # pydantic v2
except Exception:  # pydantic이 없어도 동작하도록
    class BaseModel:  # type: ignore
        pass


def _to_jsonable(obj: Any) -> Any:
    """
    어떤 타입이 와도 JSON 직렬화 가능하게 변환:
    - Pydantic BaseModel: .model_dump()
    - dict/list/tuple/set: 재귀 변환
    - 그 외: json이 가능하면 그대로, 아니면 str()로 폴백
    """
    # Pydantic 모델
    if isinstance(obj, BaseModel):
        # v2 기준
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # v1 대비
        if hasattr(obj, "dict"):
            return obj.dict()

    # 사전
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}

    # 리스트/튜플/셋
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]

    # 기본형 혹은 JSON으로 바로 가능한 경우
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        # 마지막 폴백
        return str(obj)


def _timestamp_dir(base_dir: str = "output") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(base_dir, ts)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_to_jsonable(data), f, ensure_ascii=False, indent=2)


def save_strategy(domain: str, strategy: Any, evaluation: Any, base_dir: str = "output") -> str:
    """
    전략과 평가 결과를 timestamp 디렉토리에 저장.
    - strategy.json
    - evaluation.json
    """
    out_dir = _timestamp_dir(base_dir)

    # 파일 경로
    strategy_path = os.path.join(out_dir, "strategy.json")
    eval_path = os.path.join(out_dir, "evaluation.json")

    # 저장
    save_json(strategy_path, strategy)
    save_json(eval_path, evaluation)

    print(f"[save] -> {out_dir}")
    return out_dir