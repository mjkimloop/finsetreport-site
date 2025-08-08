import os, sys, json, importlib

ROOT = os.path.dirname(os.path.abspath(__file__))  # tools/
ROOT = os.path.dirname(ROOT)                       # project root
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REQUIRED_DIRS = [
    "core_engine",
    "schemas",
    "domains/finsetreport",
    "output/_trace",
    "tests/golden/inputs",
    "tests/golden/snapshots",
]
REQUIRED_FILES = [
    "run_kai.py",
    "core_engine/qmand_engine.py",
    "core_engine/qgen_engine.py",
    "core_engine/stratos_evaluator.py",
    "core_engine/save_strategy.py",
    "core_engine/guardian_parser.py",
    "core_engine/trace_logger.py",
    "schemas/strategy.py",
    "domains/finsetreport/config.yaml",
]

def ok(flag, msg):
    print(("✅" if flag else "❌") + " " + msg)
    return flag

def main():
    print("[Preflight] Project sanity check\n")

    # 1) 디렉토리/파일 존재
    all_ok = True
    for d in REQUIRED_DIRS:
        all_ok &= ok(os.path.isdir(d), f"dir: {d}")
    for f in REQUIRED_FILES:
        all_ok &= ok(os.path.isfile(f), f"file: {f}")

    # 2) import 가능 여부
    try:
        import core_engine.qmand_engine as _; ok(True, "import core_engine.qmand_engine")
    except Exception as e:
        all_ok &= ok(False, f"import core_engine.qmand_engine -> {e}")

    try:
        import schemas.strategy as _; ok(True, "import schemas.strategy")
    except Exception as e:
        all_ok &= ok(False, f"import schemas.strategy -> {e}")

    # 3) 도메인 설정 읽기
    try:
        import yaml
        cfg = yaml.safe_load(open("domains/finsetreport/config.yaml", "r", encoding="utf-8"))
        ok(True, "domains/finsetreport/config.yaml loaded")
        print("   - keys:", list(cfg.keys()))
    except Exception as e:
        all_ok &= ok(False, f"load config.yaml -> {e}")

    # 4) 스모크 실행 (파이프라인 최소 실행)
    try:
        from core_engine.qmand_engine import run_qmand_pipeline
        res = run_qmand_pipeline(domain="finsetreport", user_input="온보딩 최적화 전략을 간단히 생성해줘")
        path = res.get("out_dir")
        ok(bool(path and os.path.isdir(path)), f"pipeline smoke-run -> {path}")
    except Exception as e:
        all_ok &= ok(False, f"pipeline smoke-run -> {e}")

    print("\n[Preflight] " + ("ALL GREEN ✅" if all_ok else "CHECK REQUIRED ❌"))
    if not all_ok:
        print(" - 위 ❌ 항목부터 순서대로 해결하세요.")

if __name__ == "__main__":
    main()