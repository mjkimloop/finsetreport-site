import os, sys, json, glob
from datetime import datetime

# --- 루트 경로를 PYTHONPATH에 추가 (직접 실행 시 필수) ---
ROOT = os.path.dirname(os.path.abspath(__file__))           # tools/
ROOT = os.path.dirname(ROOT)                                # <project root>
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TRACE_DIR = os.path.join("output", "_trace")

def _latest_qmand_start():
    """모든 trace 파일에서 가장 최근 qmand_start를 찾아 (file, payload, key) 반환"""
    files = glob.glob(os.path.join(TRACE_DIR, "*.jsonl"))
    best = (None, None, -1, None)  # (dt, file, key, payload)
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if rec.get("stage") == "qmand_start":
                        ts = rec.get("time") or rec.get("payload", {}).get("time")
                        try:
                            dt = datetime.fromisoformat(ts.replace("Z","")) if ts else None
                        except Exception:
                            dt = None
                        key = dt.timestamp() if dt else os.path.getmtime(fp)
                        if key > best[2]:
                            best = (dt, fp, key, rec.get("payload"))
        except Exception:
            continue
    return best  # (dt, file, key, payload)

def main():
    dt, fp, _, payload = _latest_qmand_start()
    if not fp or not payload:
        print("No qmand_start record found across traces.")
        return

    domain = payload.get("domain")
    user_input = payload.get("user_input")
    print(f"[replay] file={os.path.basename(fp)}")
    print(f"[replay] domain={domain}, input={user_input}")

    from core_engine.qmand_engine import run_qmand_pipeline
    result = run_qmand_pipeline(domain=domain, user_input=user_input)
    print("[replay] done ->", result.get("out_dir"))

if __name__ == "__main__":
    main()