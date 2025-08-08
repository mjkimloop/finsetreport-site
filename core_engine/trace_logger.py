import os, json, uuid
from datetime import datetime

TRACE_DIR = "output/_trace"
os.makedirs(TRACE_DIR, exist_ok=True)
SESSION = uuid.uuid4().hex

def log_trace(stage: str, payload):
    rec = {
        "session": SESSION,
        "time": datetime.utcnow().isoformat(),
        "stage": stage,
        "payload": payload,
    }
    path = os.path.join(TRACE_DIR, f"{SESSION}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")