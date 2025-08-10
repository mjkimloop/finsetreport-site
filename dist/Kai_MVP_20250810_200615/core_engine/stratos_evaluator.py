# core_engine/stratos_evaluator.py
from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import yaml

from schemas.strategy import EvalReport, StructuredStrategy

def _load_domain_config(domain: str) -> Dict[str, Any]:
    cfg_path = Path("domains") / domain / "config.yaml"
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def _as_dict(strategy: Any) -> Dict[str, Any]:
    if isinstance(strategy, StructuredStrategy):
        return strategy.model_dump()
    if isinstance(strategy, dict):
        return strategy
    # 문자열/기타가 들어와도 깨지지 않게 최소 구조로 감싸기
    return {"title": str(strategy), "objectives": [], "modules": [], "flow": [], "risks": [], "meta": {}}

def evaluate_strategy(domain: str, strategy: Any) -> EvalReport:
    """
    간단한 휴리스틱 STRATOS 평가 (MVP):
    - 구조(Structure), 커버리지(Coverage), 실행가능성(Feasibility), 리스크(Risk), 명료성(Clarity)
    - 도메인 config의 stratos_weights 사용, 없으면 기본 가중치
    """
    s = _as_dict(strategy)

    title = s.get("title") or ""
    objectives = s.get("objectives") or []
    modules = s.get("modules") or []
    flow = s.get("flow") or []
    risks = s.get("risks") or []

    n_obj = len(objectives) if isinstance(objectives, list) else 0
    n_mod = len(modules) if isinstance(modules, list) else 0
    n_flow = len(flow) if isinstance(flow, list) else 0
    n_risk = len(risks) if isinstance(risks, list) else 0

    # 휴리스틱(이전에 보시던 점수 패턴을 최대한 유지)
    structure = min(100.0, 20.0 + 20.0 * min(n_flow, 3))              # 3단계 흐름이면 80
    coverage = min(100.0, 60.0 + 5.0 * min(n_obj, 3))                 # 목표 3개면 75
    feasibility = min(100.0, 60.0 + 10.0 * min(n_mod, 2))             # 모듈 2개 이상이면 80
    risk = 70.0                                                       # 기본 70 (MVP 고정)
    clarity = 86.7 if title else 70.0                                 # 제목 있으면 86.7

    cfg = _load_domain_config(domain)
    weights = cfg.get("stratos_weights", {
        "structure": 0.25,
        "coverage": 0.25,
        "feasibility": 0.25,
        "risk": 0.15,
        "clarity": 0.10,
    })

    # 정규화 안전장치
    total_w = sum(weights.values()) or 1.0
    norm = {k: float(v) / total_w for k, v in weights.items()}

    score = (
        structure * norm.get("structure", 0.0) +
        coverage * norm.get("coverage", 0.0) +
        feasibility * norm.get("feasibility", 0.0) +
        risk * norm.get("risk", 0.0) +
        clarity * norm.get("clarity", 0.0)
    )

    findings = [
        f"structure={round(structure, 1)}",
        f"coverage={round(coverage, 1) if isinstance(coverage, float) else coverage}",
        f"feasibility={round(feasibility, 1)}",
        f"risk={int(risk)}",
        f"clarity={round(clarity, 1)}",
        f"weights={norm}",
    ]

    recs = []
    if n_mod < 4:
        recs.append("핵심 모듈 수를 4~8개로 늘려 실행 단계를 구체화하세요.")
    if n_obj < 3:
        recs.append("핵심 목표/지표를 최소 3개 이상으로 구체화하세요.")

    return EvalReport(
        score=round(float(score), 1),
        findings=findings,
        recommendations=recs,
        used_weights=norm,
    )
