# core_modules/gatekeeper_layer/input_checker.py

def classify_input_type(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["전략", "설계", "만들", "플랫폼", "앱", "퍼널"]):
        return "전략형"
    if any(k in t for k in ["아이디어", "기획"]):
        return "아이디어형"
    return "기타형"
