# tools/weight_tuner.py
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import yaml

ROOT = Path(__file__).resolve().parents[1]
FB_PATH = ROOT / "output" / "_feedback" / "feedback.jsonl"
DOMAIN = "finsetreport"
CFG_PATH = ROOT / "domains" / DOMAIN / "config.yaml"
CFG_HIST_DIR = ROOT / "domains" / DOMAIN / "config_history"

DEFAULT_WEIGHTS = {
    "structure": 0.25,
    "coverage":  0.25,
    "feasibility": 0.25,
    "risk": 0.15,
    "clarity": 0.10,
}
ALPHA = 0.03  # 보수적 학습률

# 한글 키(과거 설정) -> 현재 영문 키 매핑
LEGACY_MAP = {
    "전략성": "structure",
    "설명력": "clarity",
    "실행력": "feasibility",
    "리스크대응": "risk",
    "커버리지": "coverage",
}

def _map_legacy_keys(weights: dict | None) -> dict[str, float]:
    if not isinstance(weights, dict):
        return dict(DEFAULT_WEIGHTS)
    out: dict[str, float] = {}
    for k, v in weights.items():
        key = LEGACY_MAP.get(k, k)  # 한글이면 영문으로, 아니면 그대로
        try:
            out[key] = float(v)
        except Exception:
            continue
    # 기본 키 보강
    for k, dv in DEFAULT_WEIGHTS.items():
        out.setdefault(k, dv)
    return out

def load_feedback(limit: int | None = 500) -> list[dict]:
    if not FB_PATH.exists():
        return []
    rows: list[dict] = []
    with FB_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit:
        rows = rows[-limit:]
    return rows

def load_config() -> dict:
    with CFG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg: dict):
    CFG_HIST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = CFG_HIST_DIR / f"config_{stamp}.yaml"
    backup.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    CFG_PATH.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return backup

def normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, v) for v in weights.values()) or 1.0
    return {k: max(0.0, v) / total for k, v in weights.items()}

def propose_new_weights(cfg: dict, fb: list[dict]) -> dict[str, float]:
    current_raw = cfg.get("stratos_weights") or DEFAULT_WEIGHTS
    current = _map_legacy_keys(current_raw)

    if not fb:
        return normalize(current)

    # 아주 단순한 신호: 사용자 점수 평균이 75보다 낮으면 clarity/coverage ↑, structure/risk ↓
    avg = sum(x.get("user_score", 0) for x in fb) / max(1, len(fb))
    delta = (avg - 75.0) / 100.0  # 목표 75점 기준
    upd = current.copy()
    upd["clarity"]     = current["clarity"]     + (-delta) * ALPHA
    upd["coverage"]    = current["coverage"]    + (-delta) * ALPHA * 0.8
    upd["structure"]   = current["structure"]   + ( delta) * ALPHA * 0.5
    upd["risk"]        = current["risk"]        + ( delta) * ALPHA * 0.3
    # feasibility는 유지
    return normalize(upd)

def main():
    ap = argparse.ArgumentParser(description="Tune STRATOS weights from user feedback.")
    ap.add_argument("--dry-run", action="store_true", help="계산만 하고 저장하지 않음")
    args = ap.parse_args()

    if not CFG_PATH.exists():
        print(f"[err] config not found: {CFG_PATH}")
        return

    cfg = load_config()
    fb = load_feedback()
    new_w = propose_new_weights(cfg, fb)
    old_w = _map_legacy_keys(cfg.get("stratos_weights"))

    report = {
        "feedback_count": len(fb),
        "old_weights": old_w,
        "new_weights": new_w,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("[dry-run] not saved")
        return

    cfg["stratos_weights"] = new_w
    backup = save_config(cfg)
    print(f"[ok] weights updated & backed up -> {backup.relative_to(ROOT)}")

if __name__ == "__main__":
    main()