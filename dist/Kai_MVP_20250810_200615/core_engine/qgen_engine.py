# core_engine/qgen_engine.py  (전체 교체본)

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any, List

import yaml

from schemas.strategy import StrategyRequest, StructuredStrategy, ModuleMeta


# ------------------------------------------------------------
# 내부 유틸
# ------------------------------------------------------------
def _load_domain_config(domain: str) -> Dict[str, Any]:
    path = os.path.join("domains", domain, "config.yaml")
    if not os.path.exists(path):
        # 최소 기본값
        return {
            "domain_name": domain,
            "constraints": {"language": "ko-KR", "max_objectives": "7", "max_modules": "12"},
            "kpis": [],
            "flow_patterns": ["Discovery", "Design", "Delivery"],
            "risks": ["데이터 부족", "리소스 병목"],
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _normalize_constraints(d: Dict[str, Any] | None) -> Dict[str, str]:
    if not d:
        return {}
    out: Dict[str, str] = {}
    for k, v in d.items():
        # 모두 문자열화 (Pydantic 스키마와의 계약 유지)
        out[str(k)] = v if isinstance(v, str) else str(v)
    # 기본값 보강
    out.setdefault("language", "ko-KR")
    out.setdefault("max_objectives", "7")
    out.setdefault("max_modules", "12")
    return out


def _as_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, dict):
        return obj
    return {}


# ------------------------------------------------------------
# 공개 API
# ------------------------------------------------------------
def generate_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    StrategyRequest -> StructuredStrategy 템플릿 생성 (MVP 고정 템플릿)
    """
    domain = payload.get("domain") or ""
    user_input = payload.get("user_input") or ""
    constraints = _normalize_constraints(payload.get("constraints"))

    # 요청 스키마 검증
    _ = StrategyRequest.model_validate(
        {"domain": domain, "user_input": user_input, "constraints": constraints}
    )

    title = f"[{domain}] 전략: {user_input}".strip()

    # 간단 템플릿
    objectives: List[str] = ["핵심 목표 정의", "핵심 KPI 선정", "실행 로드맵 수립"]
    modules: List[Dict[str, str]] = [
        {"name": "Discovery", "role": "문제/사용자 조사", "deps": ""},
        {"name": "Design", "role": "퍼널/프로세스 설계", "deps": "Discovery"},
        {"name": "Delivery", "role": "실행/출시/관측", "deps": "Design"},
    ]
    flow = [m["name"] for m in modules]

    meta = ModuleMeta(
        version="1.0",
        model="template",
        timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    strat = StructuredStrategy(
        title=title,
        objectives=objectives,
        modules=modules,
        flow=flow,
        risks=["데이터 부족", "리소스 병목"],
        meta=meta,
    )

    return _as_dict(strat)


def run_qgen_pipeline(domain: str, qmand_or_text: Dict[str, Any] | str) -> Dict[str, Any]:
    """
    - qmand_or_text 가 dict 이면: QMAND 출력으로 간주 (user_input, constraints 등 포함)
    - qmand_or_text 가 str 이면: 그냥 사용자 입력 텍스트로 간주
    도메인 config와 병합하여 Strategy 템플릿 생성
    """
    cfg = _load_domain_config(domain)

    if isinstance(qmand_or_text, dict):
        user_input = (
            qmand_or_text.get("user_input")
            or qmand_or_text.get("prompt")
            or qmand_or_text.get("text")
            or ""
        )
        qmand_constraints = qmand_or_text.get("constraints") or {}
    else:
        # 문자열 입력
        user_input = str(qmand_or_text)
        qmand_constraints = {}

    base_constraints = (cfg.get("constraints") or {})
    merged_constraints = _normalize_constraints({**base_constraints, **qmand_constraints})

    payload = {
        "domain": domain,
        "user_input": user_input,
        "constraints": merged_constraints,
    }
    return generate_strategy(payload)
