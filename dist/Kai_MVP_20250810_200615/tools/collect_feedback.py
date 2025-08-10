# tools/collect_feedback.py
from __future__ import annotations
import argparse
import json
from pathlib import Path
from schemas.feedback import UserFeedback

ROOT = Path(__file__).resolve().parents[1]
FB_DIR = ROOT / "output" / "_feedback"
FB_PATH = FB_DIR / "feedback.jsonl"

def is_valid_feedback(fb: UserFeedback) -> bool:
    # 스팸/극단값 가벼운 필터: 0/100인데 텍스트 10자 미만이면 제외
    if fb.user_score in (0, 100) and len(fb.feedback_text.strip()) < 10:
        return False
    return True

def main():
    p = argparse.ArgumentParser(description="Append user feedback for strategy evaluation.")
    p.add_argument("--domain", default="finsetreport")
    p.add_argument("--title", required=True, help="strategy title shown in output/xxxx/strategy.json")
    p.add_argument("--score", type=float, required=True, help="0~100")
    p.add_argument("--text", default="", help="free-form feedback")
    args = p.parse_args()

    FB_DIR.mkdir(parents=True, exist_ok=True)
    fb = UserFeedback(domain=args.domain, strategy_title=args.title, user_score=args.score, feedback_text=args.text)

    if not is_valid_feedback(fb):
        print("[skip] feedback filtered by heuristic")
        return

    with FB_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fb.model_dump(), ensure_ascii=False) + "\n")

    print(f"[ok] appended -> {FB_PATH.relative_to(ROOT)}")

if __name__ == "__main__":
    main()