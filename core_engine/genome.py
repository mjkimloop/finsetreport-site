# core_engine/genome.py
from typing import Dict, Any, List, Tuple, Callable
import os, json, random, time

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def get_genome(domain: str) -> Dict[str, Any]:
    """
    도메인 유전자(초기 패턴/제약/선호 흐름) 정보.
    지금은 더미 반환. 필요시 domains/<domain>/config.yaml 등과 연동.
    """
    return {
        "domain": domain,
        "preferred_flow": ["requirements_ingest", "funnel_design", "kpi_define", "execution_plan"],
        "constraints": {"max_modules": 8},
    }


def evolve_once(
    *,
    seed_population: List[Dict[str, Any]],
    score_fn: Callable[[Dict[str, Any]], float],
    out_root: str,
    domain: str,
    survivors: int = 3,
    offspring: int = 4,
    mutation_rate: float = 0.3,
    generation: int = 1,
    discard_threshold: float = 60.0,
) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], float]]]:
    """
    단일 세대 진화:
    1) 점수화 -> 상위 survivors 생존
    2) crossover로 offspring 생성
    3) mutation_rate로 돌연변이
    4) discard_threshold 미만은 버림 (단, 엘리트는 보존)

    반환:
      - next_population (List[strategy])
      - scored (List[(strategy, score)])
    """
    scored = [(s, _safe_score(score_fn, s)) for s in seed_population]
    scored.sort(key=lambda x: x[1], reverse=True)

    elites = [s for s, _ in scored[: max(1, survivors)]]

    children: List[Dict[str, Any]] = []
    parents = [s for s, sc in scored if sc >= discard_threshold]
    if len(parents) < 2:
        parents = [s for s, _ in scored[:2]] if len(scored) >= 2 else [scored[0][0]]

    for _ in range(max(0, offspring)):
        a, b = random.choice(parents), random.choice(parents)
        child = crossover(a, b)
        child = mutate_strategy(child, mutation_rate)
        children.append(child)

    # 다음 세대
    next_population = elites + children

    # 결과 요약 저장 (선택적)
    _save_generation_summary(out_root, domain, generation, scored, next_population)

    # 점수 재계산(리턴용 표시)
    rescored = [(s, _safe_score(score_fn, s)) for s in next_population]
    rescored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in rescored], rescored


# ---------------------------------------------------------------------
# Genetic ops
# ---------------------------------------------------------------------

def crossover(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    두 전략을 병합. 문자열 리스트/모듈 딕셔너리 리스트 각각에 맞게 처리.
    """
    title = _mix_title(a.get("title", ""), b.get("title", ""))

    objectives = _mix_strings(
        a.get("objectives", []) or [],
        b.get("objectives", []) or []
    )

    modules = _mix_modules(
        a.get("modules", []) or [],
        b.get("modules", []) or []
    )

    flow = _mix_strings(
        a.get("flow", []) or [],
        b.get("flow", []) or []
    )
    # flow는 modules에 존재하는 name만 허용
    mod_names = {m.get("name") for m in modules if isinstance(m, dict)}
    flow = [f for f in flow if f in mod_names]

    risks = _mix_strings(
        a.get("risks", []) or [],
        b.get("risks", []) or []
    )

    meta = {
        "domain": a.get("meta", {}).get("domain") or b.get("meta", {}).get("domain"),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "genome_op": "crossover",
        "parents": [a.get("meta", {}).get("qgen_version", "na"),
                    b.get("meta", {}).get("qgen_version", "na")],
    }

    return {
        "title": title,
        "objectives": objectives,
        "modules": modules,
        "flow": flow if flow else [m.get("name") for m in modules if isinstance(m, dict)],
        "risks": risks,
        "meta": meta,
    }


def mutate_strategy(s: Dict[str, Any], rate: float) -> Dict[str, Any]:
    """
    간단한 변이: 제목 꼬리표, objectives 순서/삽입, risks 추가 등.
    """
    if random.random() < rate:
        s["title"] = _mutate_title(s.get("title", ""))

    if isinstance(s.get("objectives"), list) and s["objectives"]:
        if random.random() < rate:
            random.shuffle(s["objectives"])
        if random.random() < rate * 0.5:
            s["objectives"].append("실험 설계 강화")

    if isinstance(s.get("risks"), list) and random.random() < rate * 0.6:
        s["risks"].append("가설 검증 실패 가능성")

    # flow 재정렬(가끔)
    if isinstance(s.get("flow"), list) and random.random() < rate * 0.4:
        random.shuffle(s["flow"])

    s.setdefault("meta", {})
    s["meta"]["genome_op"] = "mutated"
    s["meta"]["mutated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    s["meta"]["mutation_rate"] = rate
    return s


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_score(score_fn, strategy: Dict[str, Any]) -> float:
    try:
        sc = score_fn(strategy)
        return float(sc) if sc is not None else 0.0
    except Exception:
        return 0.0


def _mix_title(t1: str, t2: str) -> str:
    t1 = t1 or ""; t2 = t2 or ""
    if t1 and t2 and t1 != t2:
        return f"{t1} / {t2}"
    return t1 or t2 or "전략"


def _mix_strings(x: List[str], y: List[str]) -> List[str]:
    """
    문자열 리스트 병합 + 중복 제거 (순서 보존)
    """
    x = x or []; y = y or []
    cx = random.randint(0, len(x)) if x else 0
    cy = random.randint(0, len(y)) if y else 0
    merged = x[:cx] + y[cy:]
    out, seen = [], set()
    for item in merged:
        if not isinstance(item, str):
            continue
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _mix_modules(x: List[Dict[str, Any]], y: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    모듈(dict) 리스트 병합. 'name'을 키로 중복제거. 없으면 JSON 서명으로 dedupe.
    """
    x = x or []; y = y or []
    cx = random.randint(0, len(x)) if x else 0
    cy = random.randint(0, len(y)) if y else 0
    merged = x[:cx] + y[cy:]

    result: List[Dict[str, Any]] = []
    seen_keys = set()

    for m in merged:
        if not isinstance(m, dict):
            continue
        key = m.get("name")
        if not key:
            try:
                key = json.dumps(m, ensure_ascii=False, sort_keys=True)
            except Exception:
                key = repr(m)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(m)

    # 너무 비면 기본 모듈 넣기
    if not result:
        result = [{"name": "requirements_ingest", "role": "요구사항 수집"}]
    return result


def _mutate_title(t: str) -> str:
    tags = ["(개선안)", "(A/B)", "(실험)", "(v2)", "(강화)"]
    tag = random.choice(tags)
    if tag not in t:
        return f"{t} {tag}".strip()
    return t


def _save_generation_summary(out_root: str, domain: str, gen: int,
                             scored: List[Tuple[Dict[str, Any], float]],
                             population: List[Dict[str, Any]]) -> None:
    try:
        root = os.path.join(out_root, domain, "genome")
        os.makedirs(root, exist_ok=True)
        summary = {
            "generation": gen,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "top": [
                {
                    "title": s.get("title"),
                    "score": sc,
                    "objectives": s.get("objectives"),
                    "flow": s.get("flow"),
                }
                for s, sc in sorted(scored, key=lambda x: x[1], reverse=True)[:5]
            ],
            "population_size": len(population),
        }
        with open(os.path.join(root, f"gen_{gen:03d}.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception:
        # 저장 실패는 진화 자체를 막지 않음
        pass