# tools/print_last_output.py
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

def _safe_print_json(path: Path, title: str):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[warn] 파일이 없습니다: {path}")
        return
    except json.JSONDecodeError as e:
        print(f"[warn] JSON 파싱 실패: {path} ({e})")
        return

    print(f"\n--- {title} ({path.name}) ---")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def list_recent(n: int = 5):
    if not OUTPUT_DIR.exists():
        print("[info] output 폴더가 없습니다.")
        return []
    dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name != "_trace"]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for i, d in enumerate(dirs[:n], 1):
        t = datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i:02d}. {d.name}   (modified: {t})")
    return dirs

def find_latest_dir() -> Path | None:
    dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name != "_trace"]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.stat().st_mtime)

def main():
    # 콘솔 UTF-8 출력 보정 (파워셸에서 모지바케 방지)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(description="Print latest Kai output (strategy/evaluation) in UTF-8.")
    p.add_argument("--list", type=int, metavar="N", help="최근 N개 결과 디렉터리 목록만 출력")
    p.add_argument("--dir", type=str, help="특정 결과 디렉터리 지정(예: output\\20250810_155813)")
    p.add_argument("--file", choices=["strategy", "evaluation", "both"], default="both",
                   help="출력할 파일 선택 (기본 both)")
    args = p.parse_args()

    if args.list:
        list_recent(args.list)
        return

    target_dir: Path | None
    if args.dir:
        target_dir = Path(args.dir)
        if not target_dir.is_absolute():
            target_dir = ROOT / args.dir
    else:
        target_dir = find_latest_dir()

    if not target_dir or not target_dir.exists():
        print("[info] 출력 디렉터리를 찾지 못했습니다. 먼저 run_kai.py를 실행해 결과를 생성하세요.")
        return

    print(f"[view] dir = {target_dir.relative_to(ROOT)}")

    if args.file in ("strategy", "both"):
        _safe_print_json(target_dir / "strategy.json", "Strategy")
    if args.file in ("evaluation", "both"):
        _safe_print_json(target_dir / "evaluation.json", "Evaluation")

if __name__ == "__main__":
    main()