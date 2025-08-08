from datetime import datetime
import os, yaml, json
from typing import Dict, Any

from schemas.strategy import StructuredStrategy
from core_engine.guardian_parser import guard_cast
from core_engine.model_router import router
from core_engine.trace_logger import log_trace
from prompts.autoprompt import build_prompt_bundle

PROMPT_PATH = os.path.join("prompts", "qgen_system.txt")

# LLM 없이도 동작하도록 기본 False
# 실제 연결 시 True로 바꾸고 model_router.call() 바인딩
USE_LLM: bool = False

# QGEN 단계 부분 재시도 횟수(실패 시 보정/재시도)
RETRY_MAX: int = 2


def _load_prompt_text() -> str:
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "SYSTEM: 전략 구조를 JSON 스키마(StructuredStrategy)에 맞게 생성하라."


def _load_domain_cfg(domain: str) -> dict:
    cfg_path = os.path.join("domains", domain, "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _fallback_strategy(request, combo, domain_cfg) -> Dict[str, Any]:
    """LLM을 사용하지 않을 때의 결정적 더미 전략(도메인 설정/사고조합 반영)"""
    goal = (domain_cfg.get("goal") or "").strip()
    title = f"[{request.domain}] 전략: {request.user_input[:60]}"
    if goal:
        title = f"[{request.domain}] 전략: {goal} / {request.user_input[:40]}"

    raw = {
        "title": title,
        "objectives": [
            "문제정의 명확화",
            f"도메인 목표 반영: {goal or '기본 목표'}",
            f"사고 프레임 적용: {combo.get('strategy_frame')} / {combo.get('judgment')}",
        ],
        "modules": [
            {"name": "InputAnalyzer", "role": "분류"},
            {"name": "FunnelDesigner", "role": "전략"},
            {"name": "RiskAssessor", "role": "평가"},
        ],
        "flow": ["InputAnalyzer -> FunnelDesigner -> RiskAssessor"],
        "risks": ["요구사항 변동", "데이터 부족"],
        "meta": {
            "version": "0.3.0",
            "model": "router_dummy",
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    # === 도메인 config의 kpis / flow_patterns / mitigations 반영 ===
    kpis = domain_cfg.get("kpis") or []
    if kpis:
        raw["objectives"].append(f"KPI 설정: {', '.join(kpis[:3])}")

    flow_patterns = domain_cfg.get("flow_patterns") or []
    if flow_patterns:
        raw["flow"] = flow_patterns  # 기존 flow 대체 (의존관계 가점 목적)

    mitigs = domain_cfg.get("mitigations") or []
    if mitigs:
        if not raw.get("risks"):
            raw["risks"] = ["운영 리스크 정의 필요"]
        raw["risks"] += [f"(대응){m}" for m in mitigs]

    return raw


def _call_llm(prompt_bundle) -> Any:
    """실제 API 연결 시 model_router.call() 사용. 현 단계는 더미 응답."""
    payload = {
        "system": prompt_bundle.system,
        "user": prompt_bundle.user,
        "examples": prompt_bundle.examples,
    }
    log_trace(stage="qgen_prompt", payload=payload)

    # ↓↓↓ 실제 바인딩 시:
    # resp = router.call(model="gpt4o", prompt=payload, max_tokens=1800)
    # return resp["content"]  # 문자열(JSON) 기대

    # 더미 응답(JSON 문자열)
    return json.dumps({
        "title": f"[AI] {prompt_bundle.user[:60]}",
        "objectives": ["문제정의", "솔루션설계", "실행계획"],
        "modules": [
            {"name": "Analyzer", "role": "분석"},
            {"name": "Designer", "role": "설계"},
            {"name": "Assessor", "role": "평가"},
        ],
        "flow": ["Analyzer -> Designer -> Assessor"],
        "risks": ["리스크 미정의"],
        "meta": {
            "version": "0.3.0",
            "model": "router_dummy",
            "timestamp": datetime.utcnow().isoformat()
        }
    }, ensure_ascii=False)


def generate_strategy(request, combo) -> dict:
    """오토프롬프트 → (LLM or Fallback) → Guardian 검증 → 부분 재시도"""
    system_prompt = _load_prompt_text()
    domain_cfg = _load_domain_cfg(request.domain)

    bundle = build_prompt_bundle(
        system_text=system_prompt,
        domain_cfg=domain_cfg,
        user_text=request.user_input,
        thinking_combo=combo,
    )

    attempt = 0
    last_raw = None

    while attempt <= RETRY_MAX:
        attempt += 1

        if USE_LLM:
            raw = _call_llm(bundle)  # 문자열(JSON) 가정
        else:
            raw = _fallback_strategy(request, combo, domain_cfg)  # dict

        ok, model = guard_cast(StructuredStrategy, raw)
        if ok:
            result = model.model_dump()
            log_trace(stage=f"qgen_parsed_ok_try{attempt}", payload=result)
            return result

        # 실패 시 Trace 남기고 재시도
        log_trace(stage=f"qgen_parse_fail_try{attempt}", payload=str(model))
        last_raw = raw

    # 모두 실패 → 마지막 raw 반환(파이프라인 유지)
    if isinstance(last_raw, dict):
        log_trace(stage="qgen_fallback_raw", payload=last_raw)
        return last_raw
    else:
        # 문자열이었으면 최소 안전 dict로 감쌈
        safe = {
            "title": "[Fallback] 전략",
            "objectives": [],
            "modules": [],
            "flow": [],
            "risks": [],
            "meta": {
                "version": "0.0",
                "model": "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        log_trace(stage="qgen_fallback_safe", payload=safe)
        return safe