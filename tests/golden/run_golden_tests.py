import os
import sys
import json
import hashlib
import argparse
from datetime import datetime

# --- 루트 경로를 PYTHONPATH에 추가 (tests/golden에서 실행해도 import 가능) ---
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core_engine.qmand_engine import run_qmand_pipeline  # noqa: E402


DOMAIN = "finsetreport"
INPUT_DIR = os.path.join("tests", "golden", "inputs")
SNAP_DIR = os.path.join("tests", "golden", "snapshots")
REPORT_DIR = os.path.join("tests", "golden", "reports")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(SNAP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# -----------------------
# 유틸
# -----------------------
def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _dump_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _hash(obj) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_strategy(obj: dict) -> dict:
    """
    스냅샷 비교 전에 비결정 필드(meta.timestamp 등)를 고정/제거해서 해시 드리프트 방지.
    필요 시 여기에 정규화 규칙을 추가.
    """
    if not isinstance(obj, dict):
        return obj
    out = json.loads(json.dumps(obj, ensure_ascii=False))  # deepcopy

    meta = out.get("meta")
    if isinstance(meta, dict):
        # 테스트 중에는 timestamp가 바뀌지 않도록 고정
        meta["timestamp"] = "<fixed-ts>"
        # 모델명을 고정하고 싶다면:
        # meta["model"] = "<fixed-model>"

    # 리스트 구조가 set/순서불안정할 수 있으면 여기서 정렬하거나 정형화 가능
    # out["objectives"] = sorted(out["objectives"])  # 필요시
    # out["flow"] = sorted(out["flow"])              # 필요시

    return out


def _hash_norm(obj) -> str:
    norm = _normalize_strategy(obj)
    payload = json.dumps(norm, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _snap_paths(case_name: str):
    case_dir = os.path.join(SNAP_DIR, case_name)
    snap_s = os.path.join(case_dir, "strategy.json")
    snap_e = os.path.join(case_dir, "evaluation.json")
    return case_dir, snap_s, snap_e


def _ensure_sample_inputs():
    cases = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")])
    if cases:
        return cases
    samples = {
        "case1.txt": "핀셋리포트 가입 온보딩을 최적화해줘",
        "case2.txt": "대출 중개 플랫폼의 리텐션 퍼널을 설계해줘",
        "case3.txt": "대출 상담 챗봇의 KPI를 정의해줘",
        "case4.txt": "핀셋리포트 유입부터 전환까지 A/B 테스트 계획을 수립해줘",
        "case5.txt": "대출 상품 추천 알고리즘을 위한 데이터 파이프라인 전략 설계해줘",
    }
    for fn, txt in samples.items():
        with open(os.path.join(INPUT_DIR, fn), "w", encoding="utf-8") as f:
            f.write(txt)
    print("[init] 샘플 입력 5개를 생성했습니다.")
    return sorted(samples.keys())


# -----------------------
# 메인
# -----------------------
def main():
    parser = argparse.ArgumentParser(description="Golden tests runner")
    parser.add_argument("--update-baseline", action="store_true",
                        help="현재 결과를 스냅샷으로 덮어쓰기(의도된 변경 반영)")
    parser.add_argument("--case", type=str, default=None,
                        help="특정 케이스만 실행 (예: case3)")
    parser.add_argument("--deterministic", action="store_true",
                        help="결정 모드로 실행(KAI_DETERMINISTIC=1)")
    args = parser.parse_args()

    # 결정 모드: 엔진이 timestamp/seed를 고정하도록 환경변수 설정
    if args.deterministic:
        os.environ["KAI_DETERMINISTIC"] = "1"

    cases = _ensure_sample_inputs()
    if args.case:
        target = f"{args.case}.txt" if not args.case.endswith(".txt") else args.case
        if target in cases:
            cases = [target]
        else:
            print(f"[warn] 입력 케이스를 찾을 수 없습니다: {args.case}")
            return

    summary = []
    for case in cases:
        case_name = os.path.splitext(case)[0]
        user_input = _load_text(os.path.join(INPUT_DIR, case))
        print(f"\n[CASE] {case_name}: {user_input}")

        result = run_qmand_pipeline(domain=DOMAIN, user_input=user_input)
        strategy = result.get("strategy", {})
        evaluation = result.get("evaluation", {})

        case_dir, snap_s, snap_e = _snap_paths(case_name)

        # 스냅샷 없으면 baseline 생성
        if not os.path.exists(case_dir):
            os.makedirs(case_dir, exist_ok=True)
            _dump_json(snap_s, strategy)
            _dump_json(snap_e, evaluation)
            print(f"  → baseline snapshot created: {case_name}")
            summary.append({"case": case_name, "status": "baseline_created"})
            continue

        # 비교 (strategy는 정규화 후 해시 비교)
        base_strategy = _load_json(snap_s)
        base_evaluation = _load_json(snap_e)

        changed = []
        if _hash_norm(strategy) != _hash_norm(base_strategy):
            changed.append("strategy.json")
        if _hash(evaluation) != _hash(base_evaluation):
            changed.append("evaluation.json")

        if changed and args.update_baseline:
            # 의도된 변경 → 스냅샷 덮어쓰기
            _dump_json(snap_s, strategy)
            _dump_json(snap_e, evaluation)
            print(f"  ✓ baseline updated: {', '.join(changed)}")
            summary.append({"case": case_name, "status": "baseline_updated", "files": changed})
        elif changed:
            print(f"  ❗ changed: {', '.join(changed)}")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_case_dir = os.path.join(REPORT_DIR, f"{case_name}_{ts}")
            os.makedirs(out_case_dir, exist_ok=True)
            _dump_json(os.path.join(out_case_dir, "new_strategy.json"), strategy)
            _dump_json(os.path.join(out_case_dir, "new_evaluation.json"), evaluation)
            summary.append({"case": case_name, "status": "changed", "files": changed})
        else:
            print("  ✓ unchanged")
            summary.append({"case": case_name, "status": "unchanged"})

    _dump_json(os.path.join(REPORT_DIR, "summary_last.json"), summary)
    print("\n=== Summary ===")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()