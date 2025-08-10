from pathlib import Path
BASE = Path("prompts")

def load_prompt(name: str, default: str="") -> str:
    p = BASE / f"{name}.system.txt"
    return p.read_text(encoding="utf-8") if p.exists() else default