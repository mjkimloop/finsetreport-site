# run_kai.py
from __future__ import annotations
import argparse
import os
import sys

from core_engine.qgen_engine import run_qgen_pipeline
from core_engine.stratos_evaluator import evaluate_strategy
from core_engine.save_strategy import save_strategy
from tools.export_report import (
    export_markdown_report,
    export_html_report,
    export_pdf_report,
)

def safe_print(*args, quiet=False, **kwargs):
    if not quiet:
        print(*args, **kwargs)

def run_once(domain: str, user_input: str):
    """QGEN → STRATOS → SAVE"""
    strategy = run_qgen_pipeline(domain, user_input)
    evaluation = evaluate_strategy(domain, strategy)
    out_dir = save_strategy(domain, strategy, evaluation)
    return strategy, evaluation, out_dir

def main():
    parser = argparse.ArgumentParser(description="Kai CLI")
    parser.add_argument("--domain", required=True, help="도메인 이름")
    parser.add_argument("--input", required=True, help="사용자 입력")
    parser.add_argument("--export", choices=["md", "html", "pdf", "all"], help="리포트 내보내기 형식")
    parser.add_argument("--open", action="store_true", help="생성 후 열기")
    parser.add_argument("--debug", action="store_true", help="디버그 정보(가중치 등) 노출")
    parser.add_argument("--quiet", action="store_true", help="로그 최소화")
    parser.add_argument("--logo", default=None, help="PDF 헤더 로고 경로 (선택)")
    args = parser.parse_args()

    safe_print("Kai System Initializing...", quiet=args.quiet)
    strategy, evaluation, out_dir = run_once(args.domain, args.input)

    title = getattr(strategy, "title", None) or (
        strategy.get("title") if isinstance(strategy, dict) else ""
    )
    score = getattr(evaluation, "score", None) or (
        evaluation.get("score") if isinstance(evaluation, dict) else 0.0
    )

    safe_print(f"[save] -> {out_dir}\n", quiet=args.quiet)
    safe_print("✅ 최종 결과 요약:", quiet=args.quiet)
    safe_print(f"- 전략 제목: {title}", quiet=args.quiet)
    safe_print(f"- 평가 점수: {score:.1f}", quiet=args.quiet)

    if args.export:
        if args.export in ("md", "all"):
            export_markdown_report(strategy, evaluation, out_dir, open_file=args.open, debug=args.debug, quiet=args.quiet)
        if args.export in ("html", "all"):
            export_html_report(strategy, evaluation, out_dir, open_file=args.open, debug=args.debug, quiet=args.quiet)
        if args.export in ("pdf", "all"):
            export_pdf_report(strategy, evaluation, out_dir, open_file=args.open, debug=args.debug, quiet=args.quiet, logo_path=args.logo)

if __name__ == "__main__":
    main()
