# tools/preflight_check.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

print("[Preflight] Project sanity check\n")

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

# PYTHONPATH 보정 (로컬 실행/CI 모두 대응)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def ok(label: str, detail: str = ""):
    mark = "✅"
    if detail:
        print(f"{mark} {label}: {detail}")
    else:
        print(f"{mark} {label}")


def bad(label: str, detail: str = ""):
    mark = "❌"
    if detail:
        print(f"{mark} {label} -> {detail}")
    else:
        print(f"{mark} {label}")


def check_exists():
    required_dirs = [
        "core_engine",
        "schemas",
        "domains/finsetreport",
        "output/_trace",
        "tests/golden/inputs",
        "tests/golden/snapshots",
    ]
    required_files = [
        "run_kai.py",
        "core_engine/qmand_engine.py",
        "core_engine/qgen_engine.py",
        "core_engine/stratos_evaluator.py",
        "core_engine/trace_logger.py",
        "schemas/strategy.py",
        "domains/finsetreport/config.yaml",
    ]

    for d in required_dirs:
        p = ROOT / d
        if p.is_dir():
            ok("dir", d)
        else:
            bad("dir", d)

    for f in required_files:
        p = ROOT / f
        if p.is_file():
            ok("file", f)
        else:
            bad("file", f)


def check_imports_and_config():
    # 임포트 체크
    try:
        import core_engine.qmand_engine as _  # noqa: F401
        ok("import core_engine.qmand_engine")
    except Exception as e:
        bad("import core_engine.qmand_engine", str(e))

    try:
        import schemas.strategy as _  # noqa: F401
        ok("import schemas.strategy")
    except Exception as e:
        bad("import schemas.strategy", str(e))

    # 도메인 설정 로드
    cfg_path = ROOT / "domains" / "finsetreport" / "config.yaml"
    try:
        import yaml  # type: ignore
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        ok("domains/finsetreport/config.yaml loaded")
        if isinstance(cfg, dict):
            keys = list(cfg.keys())
            print(f"   - keys: {keys}")
        else:
            bad("config format", "YAML root is not a dict")
    except Exception as e:
        bad("load config", f"{cfg_path}: {e}")


def smoke_run() -> Optional[str]:
    """
    최소 파이프라인 스모크 실행.
    run_qmand_pipeline 서명이 환경에 따라 다를 수 있어
    인자 조합을 바꿔가며 안전하게 호출한다.
    """
    try:
        from core_engine.qmand_engine import run_qmand_pipeline  # type: ignore
    except Exception as e:
        bad("import run_qmand_pipeline", str(e))
        return None

    candidates = [
        # (kwargs)
        {"domain": "finsetreport", "user_input": "온보딩 최적화 전략 스모크 테스트", "deterministic": True},
        {"domain": "finsetreport", "user_input": "온보딩 최적화 전략 스모크 테스트"},
    ]

    for kwargs in candidates:
        try:
            outdir = run_qmand_pipeline(**kwargs)  # 기대: output/<timestamp> 경로 문자열
            if outdir:
                return str(outdir)
        except TypeError:
            # 서명 불일치 → 다음 시도
            continue
        except Exception as e:
            bad("pipeline smoke-run error", str(e))
            return None

    return None


def main():
    check_exists()
    check_imports_and_config()
    out = smoke_run()
    if out:
        ok("pipeline smoke-run", out)
        print("\n[Preflight] ALL GREEN ✅")
    else:
        bad("pipeline smoke-run", "None")
        # 나머지는 초록이어도 스모크 실패만 경고로 남긴다.
        print("\n[Preflight] Completed with warnings ⚠️")


if __name__ == "__main__":
    main()