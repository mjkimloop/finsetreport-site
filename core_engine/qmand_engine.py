# core_engine/qmand_engine.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import datetime, json

try:
    import yaml
except ImportError:
    yaml = None

# ---------- utils ----------
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def _load_yaml(p: Path) -> Dict[str, Any]:
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    if yaml is None:
        raise RuntimeError("PyYAML is required. pip install pyyaml")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _now_utc_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _normalize_user_input(raw: Any) -> str:
    if isinstance(raw, dict):
        return (raw.get("text", "") or "").strip()
    return (str(raw) if raw is not None else "").strip()

def _detect_intent(text: str, routing_keywords: Dict[str, Any]) -> str:
    tl = text.lower()
    for intent, kws in (routing_keywords or {}).items():
        if isinstance(kws, (list, tuple)):
            for kw in kws:
                if kw and kw.lower() in tl:
                    return intent
    return "strategy"

# ---------- public API ----------
def load_domain_config(domain: str) -> Dict[str, Any]:
    base = _project_root()
    cfg_path = base / "domains" / domain / "config.yaml"
    return _load_yaml(cfg_path)

def run_qmand_pipeline(domain: str, user_input: Any, *, language: str = "ko-KR") -> Dict[str, Any]:
    cfg = load_domain_config(domain)

    text = _normalize_user_input(user_input)
    intent = _detect_intent(text, cfg.get("routing_keywords") or {})

    constraints = dict(cfg.get("constraints") or {})
    constraints.setdefault("language", language)

    meta = {"domain": domain, "intent": intent, "timestamp": _now_utc_iso()}

    qmand_payload = {
        "domain": domain,
        "user_input": text,          # 문자열 보장
        "constraints": constraints,
        "intent": intent,
        "meta": meta,
    }

    # trace (best-effort)
    try:
        trace_dir = _project_root() / "output" / "_trace"
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / f"qmand_{meta['timestamp'].replace(':','')}.json").write_text(
            json.dumps(qmand_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    return qmand_payload

__all__ = ["run_qmand_pipeline", "load_domain_config"]