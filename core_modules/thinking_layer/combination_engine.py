# core_modules/thinking_layer/combination_engine.py

def get_thinking_combo(input_type: str) -> dict:
    if input_type == "전략형":
        return {"strategy_frame": "QMAND+QGEN", "judgment": "RiskFirst"}
    if input_type == "아이디어형":
        return {"strategy_frame": "Brainstorm", "judgment": "Feasibility"}
    return {"strategy_frame": "DEFAULT", "judgment": "General"}
