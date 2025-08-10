from datetime import datetime
import json
from typing import Dict, Any

from schemas.strategy import GeneratedCode
from core_engine.guardian_parser import guard_cast
from core_engine.trace_logger import log_trace
# from core_engine.model_router import router  # LLM 붙일 때 사용

def _dummy_codegen(idea: str) -> Dict[str, Any]:
    safe_name = "generated_module.py"
    content = f'''"""
Auto-generated module
Idea: {idea}
Generated at: {datetime.utcnow().isoformat()}
"""

def run():
    return "OK"
'''
    return {
        "filename": safe_name,
        "language": "python",
        "content": content
    }

def generate_code(idea: str) -> dict:
    # LLM 붙일 땐 여기서 router.call(...)
    raw = _dummy_codegen(idea)

    ok, model = guard_cast(GeneratedCode, raw)
    if ok:
        payload = model.model_dump()
        log_trace(stage="codegen_valid", payload=payload)
        return payload

    # 실패 시 폴백(최소 안전 계약)
    fallback = {
        "filename": "generated.py",
        "language": "python",
        "content": "def run():\n    return 'OK'\n"
    }
    log_trace(stage="codegen_invalid", payload=str(model))
    return fallback