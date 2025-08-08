from __future__ import annotations
import os
from datetime import datetime
from typing import Dict, Any, Tuple

from schemas.strategy import StrategyRequest
from core_engine.trace_logger import log_trace
from core_engine.qgen_engine import generate_strategy  # QGEN은 내부에 자체 재시도 포함
from core_engine.stratos_evaluator import evaluate_strategy
from core_engine.codegen_engine import generate_code
from core_engine.save_strategy import save_outputs


# === 설정 ===
EVAL_RETRY_MAX = 2       # STRATOS 부분 재시도 횟수
CODEGEN_ENABLED = False  # 코드 생성 단계 사용 여부 (원하면 True)
CODEGEN_RETRY_MAX = 1    # 코드 생성 부분 재시도 횟수


# --- 간단 분류 + 사고 조합 (외부 의존 최소화) ---
STRATEGY_KWS = ["전략", "설계", "구축", "플랫폼", "퍼널", "온보딩", "로드맵", "아키텍처"]
IDEA_KWS     = ["아이디어", "기획", "콘텐츠", "브레인스토밍", "무엇을 만들"]
JUDGE_KWS    = ["괜찮", "맞아", "판단", "리스크", "위험", "평가"]

def _classify(user_input: str) -> str:
    t = user_input.lower()
    if any(k in t for k in STRATEGY_KWS): return "전략형"
    if any(k in t for k in JUDGE_KWS):    return "판단형"
    if any(k in t for k in IDEA_KWS):     return "아이디어형"
    return "기타형"

def _thinking_combo(input_type: str) -> Dict[str, str]:
    if input_type == "전략형":
        return {"strategy_frame": "전략적 사고", "judgment": "목표 중심 판단"}
    if input_type == "판단형":
        return {"strategy_frame": "분석적 사고", "judgment": "리스크 평가"}
    if input_type == "아이디어형":
        return {"strategy_frame": "발산적 사고", "judgment": "우선순위 결정"}
    return {"strategy_frame": "일반 사고", "judgment": "기본 판단"}


# --- STRATOS 부분 재시도 ---
def _eval_with_retry(strategy: Dict[str, Any]) -> Dict[str, Any]:
    last = None
    for i in range(1, EVAL_RETRY_MAX + 2):  # 시도 1 + 재시도 N
        try:
            result = evaluate_strategy(strategy)  # EvalReport 스키마 검증 내장
            if isinstance(result, dict) and "score" in result:
                log_trace(stage=f"stratos_ok_try{i}", payload=result)
                return result
            last = result
            log_trace(stage=f"stratos_invalid_try{i}", payload=str(result))
        except Exception as e:
            last = {"error": str(e)}
            log_trace(stage=f"stratos_exception_try{i}", payload=str(e))
    return last or {"score": 0.0, "findings": ["eval_failed"], "recommendations": ["점검 필요"]}


# --- Codegen 부분 재시도 (옵션) ---
def _codegen_with_retry(idea: str) -> Dict[str, Any]:
    last = None
    for i in range(1, CODEGEN_RETRY_MAX + 2):
        try:
            art = generate_code(idea)  # GeneratedCode 스키마 검증 내장
            if all(k in art for k in ("filename", "language", "content")):
                log_trace(stage=f"codegen_ok_try{i}", payload={"filename": art["filename"], "language": art["language"]})
                return art
            last = art
            log_trace(stage=f"codegen_invalid_try{i}", payload=str(art))
        except Exception as e:
            last = {"error": str(e)}
            log_trace(stage=f"codegen_exception_try{i}", payload=str(e))
    return last or {"filename": "generated.py", "language": "python", "content": "def run():\n    return 'OK'\n"}


# --- Public API ---
def run_qmand_pipeline(*, domain: str, user_input: str) -> Dict[str, Any]:
    """QMAND → QGEN → STRATOS(→ CODEGEN) → SAVE 파이프라인"""
    ts = datetime.utcnow().isoformat()
    log_trace(stage="qmand_start", payload={"domain": domain, "user_input": user_input, "time": ts})

    # 1) 분류/사고조합
    input_type = _classify(user_input)
    combo = _thinking_combo(input_type)
    log_trace(stage="thinking_combo", payload={"input_type": input_type, **combo})

    # 2) QGEN (자체 Guardian + 재시도 내장)
    req = StrategyRequest(domain=domain, user_input=user_input, constraints={})
    strategy = generate_strategy(request=req, combo=combo)
    log_trace(stage="qgen_done", payload={"title": strategy.get("title", "")})

    # 3) STRATOS (부분 재시도)
    evaluation = _eval_with_retry(strategy)

    # 4) (옵션) CODEGEN (부분 재시도)
    code_art = None
    if CODEGEN_ENABLED:
        code_art = _codegen_with_retry(user_input)

    # 5) SAVE
    out_dir = save_outputs(strategy=strategy, evaluation=evaluation, code_art=code_art)
    log_trace(stage="saved", payload={"out_dir": out_dir})

    return {"strategy": strategy, "evaluation": evaluation, "code": code_art, "out_dir": out_dir}