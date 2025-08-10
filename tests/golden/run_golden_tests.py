# tests/golden/run_golden_tests.py
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# --- 프로젝트 루트 / 모듈 경로 설정 ---
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core_engine.qmand_engine import run_qmand_pipeline
from core_engine.qgen_engine import run_qgen_pipeline
from core_engine.stratos_evaluator import evaluate_strategy

# (옵션) generate_strategy가 있는 경우 폴백으로 사용
try:
    from core_engine.qgen_engine import generate_strategy as _qgen_generate_strategy  # type: ignore
except Exception:
    _qgen_generate_strategy = None  # type: ignore

INPUT_DIR = ROOT / "tests" / "golden" / "inputs"
SNAP_DIR  = ROOT / "tests" / "golden" / "snapshots"

# -----------------------
# 정규화 유틸
# -----------------------
def _norm_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x)
    return " ".join(s.replace("\r\n", "\n").replace("\r", "\n").split())

def _sort_list_str(xs: List[str]) -> List[str]:
    return sorted((_norm_text(x) for x in xs), key=lambda z: z.lower())

def canonicalize_strategy(s: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    out["title"] = _norm_text(s.get("title", ""))

    objs = s.get("objectives") or []
    out["objectives"] = _sort_list_str(objs)

    mods = []
    for m in (s.get("modules") or []):
        mods.append({
            "name": _norm_text(m.get("name", "")),
            "role": _norm_text(m.get("role", "")),
            "deps": _norm_text(m.get("deps", "")),
        })
    mods.sort(key=lambda m: m["name"].lower())
    out["modules"] = mods

    flow = s.get("flow") or []
    out["flow"] = _sort_list_str(flow)

    risks = s.get("risks") or []
    out["risks"] = _sort_list_str(risks)

    meta = dict(s.get("meta") or {})
    if "timestamp" in meta:
        meta["timestamp"] = "<ts>"  # 비결정 값 제거
    out["meta"] = {
        "version": _norm_text(meta.get("version", "")),
        "model": _norm_text(meta.get("model", "")),
        "timestamp": _norm_text(meta.get("timestamp", "")),
    }
    return out

def canonicalize_evaluation(e: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        out["score"] = round(float(e.get("score", 0.0)), 1)
    except Exception:
        out["score"] = 0.0

    findings = []
    for item in (e.get("findings") or []):
        s = _norm_text(item)
        if s.lower().startswith("weights="):
            findings.append("weights=<omitted>")
        else:
            findings.append(s)
    findings.sort(key=lambda z: z.lower())
    out["findings"] = findings

    recs = _sort_list_str(e.get("recommendations") or [])
    out["recommendations"] = recs
    return out

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

# -----------------------
# QGEN 호출 호환 래퍼
# -----------------------
def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    # pydantic BaseModel 대응
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()  # type: ignore
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return obj.dict()  # type: ignore
        except Exception:
            pass
    return {}

def _call_qgen(domain: str, qmand: Any, fallback_text: str) -> Dict[str, Any]:
    """
    다양한 시그니처에 대응:
      1) run_qgen_pipeline(domain, qmand_dict)
      2) run_qgen_pipeline(domain, input_text)
      3) run_qgen_pipeline(domain, payload_dict)
      4) (폴백) _qgen_generate_strategy(payload_dict)
    """
    qmand_d = _to_dict(qmand)
    user_input = qmand_d.get("user_input", fallback_text)
    constraints = qmand_d.get("constraints", {})

    # 1) dict 전달
    try:
        return _to_dict(run_qgen_pipeline(domain, qmand_d))
    except TypeError:
        pass
    except Exception:
        # 다른 예외는 다음 시도
        pass

    # 2) 텍스트 전달
    try:
        return _to_dict(run_qgen_pipeline(domain, user_input))
    except TypeError:
        pass
    except Exception:
        pass

    # 3) payload dict 전달
    payload = {
        "domain": domain,
        "user_input": user_input,
        "constraints": constraints,
    }
    try:
        return _to_dict(run_qgen_pipeline(domain, payload))
    except TypeError:
        pass
    except Exception:
        pass

    # 4) 폴백: generate_strategy(payload)
    if _qgen_generate_strategy is not None:
        try:
            return _to_dict(_qgen_generate_strategy(payload))  # type: ignore
        except Exception:
            pass

    raise RuntimeError("run_qgen_pipeline 호출에 실패했습니다. 시그니처를 확인하세요.")

# -----------------------
# 테스트 실행
# -----------------------
def run_case(name: str, text: str, update: bool) -> str:
    """단일 케이스 실행/비교. 결과: 'unchanged' | 'changed' | 'created' | 'updated'."""
    domain = "finsetreport"

    # QMAND
    qmand = run_qmand_pipeline(domain=domain, user_input=text)
    qmand_d = _to_dict(qmand)

    # QGEN (호환 래퍼)
    draft = _call_qgen(domain, qmand_d, text)

    # STRATOS
    evalr = evaluate_strategy(domain, draft)
    eval_d = _to_dict(evalr) or (evalr if isinstance(evalr, dict) else {})

    # 정규화
    strat_norm = canonicalize_strategy(draft)
    eval_norm  = canonicalize_evaluation(eval_d)

    # 스냅샷 경로
    case_dir = SNAP_DIR / name
    s_path   = case_dir / "strategy.json"
    e_path   = case_dir / "evaluation.json"

    if not s_path.exists() or not e_path.exists():
        if update:
            save_json(s_path, strat_norm)
            save_json(e_path, eval_norm)
            print("  ✓ created")
            return "created"
        else:
            print("  ✗ missing snapshot (run with --update-baseline)")
            return "changed"

    s_base = load_json(s_path)
    e_base = load_json(e_path)

    if s_base == strat_norm and e_base == eval_norm:
        print("  ✓ unchanged")
        return "unchanged"

    if update:
        save_json(s_path, strat_norm)
        save_json(e_path, eval_norm)
        print("  ✓ updated")
        return "updated"
    else:
        print("  ✓ changed")
        return "changed"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="", help="특정 케이스만 실행 (예: case3)")
    ap.add_argument("--update-baseline", action="store_true", help="스냅샷 갱신")
    args = ap.parse_args()

    cases = []
    for p in sorted(INPUT_DIR.glob("*.txt")):
        name = p.stem
        if args.case and name != args.case:
            continue
        text = p.read_text(encoding="utf-8").strip()
        cases.append((name, text))

    if not cases:
        print("No cases found.")
        sys.exit(0)

    changed_any = False
    summary = []
    for name, text in cases:
        print(f"\n[CASE] {name}: {text}")
        status = run_case(name, text, update=args.update_baseline)
        summary.append({"case": name, "status": status})
        if status in ("changed",):
            changed_any = True

    print("\n=== Summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 업데이트 모드가 아니고 변경이 있으면 실패 코드
    if (not args.update_baseline) and changed_any:
        sys.exit(1)

if __name__ == "__main__":
    main()
