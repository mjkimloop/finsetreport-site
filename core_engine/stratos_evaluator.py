from schemas.strategy import EvalReport, StratosScore
from core_engine.guardian_parser import guard_cast

KPI_HINTS = ["kpi", "지표", "전환", "conversion", "%", "dau", "mau", "리텐션", "retention", "ltv", "cac"]
MITI_HINTS = ["대응", "완화", "mitigation", "plan", "대책", "백업", "fallback", "우회"]
DEP_KEYS   = ["deps", "depends", "dependencies"]

def _has_kpi(objectives):
    txt = " ".join([str(o) for o in (objectives or [])]).lower()
    return any(h in txt for h in KPI_HINTS)

def _has_dependencies(mods, flow):
    # 1) 모듈에 deps 유무
    if isinstance(mods, list):
        for m in mods:
            if isinstance(m, dict) and any(k in m for k in DEP_KEYS):
                return True
    # 2) flow에 화살표가 2개 이상(3노드 이상)
    if isinstance(flow, list):
        arrows = " ".join(flow).count("->")
        if arrows >= 2:
            return True
    return False

def _has_mitigation(risks):
    txt = " ".join([str(r) for r in (risks or [])]).lower()
    return any(h in txt for h in MITI_HINTS)

def evaluate_strategy(strategy: dict) -> dict:
    """
    기본 평가 함수: EvalReport 스키마 유지(파이프라인 호환).
    """
    title = str(strategy.get("title", "")) if isinstance(strategy, dict) else ""
    objs  = strategy.get("objectives", []) if isinstance(strategy, dict) else []
    mods  = strategy.get("modules", []) if isinstance(strategy, dict) else []
    flow  = strategy.get("flow", []) if isinstance(strategy, dict) else []
    risks = strategy.get("risks", []) if isinstance(strategy, dict) else []

    # 가산 점수(구조적 충실도)
    s_title = 10 if len(title) >= 8 else 5
    s_obj   = min(30, len(objs) * 10)                  # 목표 수 *10 (최대 30)
    s_mod   = min(30, len(mods) * 7)                   # 모듈 수 *7  (대략 4~5개면 만점 근접)
    roles   = {m.get("role") for m in mods if isinstance(m, dict)}
    s_role  = 15 if len(roles) >= 3 else (8 if len(roles) >= 2 else 3)
    s_flow  = 15 if (isinstance(flow, list) and len(" ".join(flow)) >= 20) else 8
    s_risk  = 10 if len(risks) >= 2 else 5
    base_score = s_title + s_obj + s_mod + s_role + s_flow + s_risk

    # 감점 규칙
    penalties = []
    if not _has_kpi(objs):
        penalties.append(("KPI 미기재", 15))
    if not _has_dependencies(mods, flow):
        penalties.append(("모듈 의존관계/흐름 불충분", 10))
    if not _has_mitigation(risks):
        penalties.append(("리스크 대응전략 미기재", 10))
    penalty_total = sum(p for _, p in penalties)

    score = base_score - penalty_total
    score = max(0, min(100, score))

    findings = [
        f"title_len:{len(title)}",
        f"objectives:{len(objs)}",
        f"modules:{len(mods)}",
        f"roles:{len(roles)}",
        f"flow_tokens:{len(' '.join(flow))}",
        f"risks:{len(risks)}",
    ] + [f"penalty:{name}:{pts}" for name, pts in penalties]

    recs = []
    if any("KPI" in name for name, _ in penalties):
        recs.append("목표(Objectives)에 정량 KPI(예: 전환율 %, DAU, 리텐션)를 1개 이상 포함하세요.")
    if any("의존관계" in name for name, _ in penalties):
        recs.append("modules에 deps/depends를 명시하거나 flow에 3개 이상 노드 흐름을 작성하세요.")
    if any("리스크 대응전략" in name for name, _ in penalties):
        recs.append("각 리스크에 대한 대응책(완화/우회/백업)을 1줄 이상 기술하세요.")
    if not recs:
        recs.append("세부 KPI와 RACI, 일정·리소스 가정치를 보강하면 더 높게 평가됩니다.")

    raw = {
        "score": float(score),
        "findings": findings,
        "recommendations": recs,
    }
    ok, model = guard_cast(EvalReport, raw)
    return model.model_dump() if ok else raw


# (선택) 항목별 점수로도 보고 싶으면 아래 보조 함수를 사용
def evaluate_strategy_scored(strategy: dict) -> dict:
    """
    StratosScore 스키마 반환(선택). 필요 시 별도 사용.
    """
    # 간단 매핑 예시(실전이면 항목별 점수 계산을 따로 구성)
    eval_report = evaluate_strategy(strategy)
    total = float(eval_report.get("score", 0))
    # 대충 가중 분배 예시
    detail = {
        "전략성": min(100.0, total * 0.4),
        "설명력": min(100.0, total * 0.3),
        "리스크_대응력": min(100.0, total * 0.3),
        "총점": float(total),
    }
    ok, model = guard_cast(StratosScore, detail)
    return model.model_dump() if ok else detail