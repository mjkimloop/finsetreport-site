import os, json
from datetime import datetime
from typing import Optional, Dict, Any

BASE_OUT = "output"
TRACE_DIR = os.path.join(BASE_OUT, "_trace")
os.makedirs(BASE_OUT, exist_ok=True)
os.makedirs(TRACE_DIR, exist_ok=True)

def _tsdir() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _dump(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def save_outputs(*, strategy: Dict[str, Any], evaluation: Dict[str, Any], code_art: Optional[Dict[str, Any]]=None) -> str:
    out_dir = os.path.join(BASE_OUT, _tsdir())
    os.makedirs(out_dir, exist_ok=True)

    _dump(os.path.join(out_dir, "strategy.json"), strategy or {})
    _dump(os.path.join(out_dir, "evaluation.json"), evaluation or {})

    if code_art:
        code_dir = os.path.join(out_dir, "code")
        os.makedirs(code_dir, exist_ok=True)
        _dump(os.path.join(code_dir, "code_artifact.json"), code_art)
        # 실제 파일로도 저장(언어가 python일 때만)
        if code_art.get("language") == "python" and code_art.get("filename") and code_art.get("content"):
            py_path = os.path.join(code_dir, code_art["filename"])
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(code_art["content"])

    return out_dir