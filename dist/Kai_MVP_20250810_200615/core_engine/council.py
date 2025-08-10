# core_engine/council.py
from __future__ import annotations
import json
from typing import List, Dict, Any

def pick_first_valid_json(candidates: List[str]) -> str:
    for t in candidates:
        try:
            obj = json.loads(t)
            if isinstance(obj, dict) and "title" in obj:
                return t
        except Exception:
            continue
    return ""

def simple_council_merge(texts: List[str]) -> str:
    # 지금은 "첫 유효 JSON" 규칙. 필요하면 다수결/평균 등으로 고도화
    return pick_first_valid_json(texts) or (texts[0] if texts else "")