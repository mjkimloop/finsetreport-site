import json
from pydantic import ValidationError
from typing import Type, Tuple, Any

def _maybe_json_load(payload: Any):
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return payload
    return payload

def guard_cast(model_cls: Type[Any], payload: Any) -> Tuple[bool, Any]:
    """
    1) payload가 문자열이면 JSON 파싱 시도
    2) 1차 검증 실패 시: key strip / None→"" 보정 후 재검증
    """
    payload = _maybe_json_load(payload)
    try:
        return True, model_cls.model_validate(payload)
    except ValidationError as e:
        if isinstance(payload, dict):
            fix = {str(k).strip(): ("" if v is None else v) for k, v in payload.items()}
            try:
                return True, model_cls.model_validate(fix)
            except ValidationError as e2:
                return False, e2
        return False, e