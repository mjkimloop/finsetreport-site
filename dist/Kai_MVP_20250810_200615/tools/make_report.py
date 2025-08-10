# tools/make_report.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import argparse
import sys


def _find_last_output_dir(base: Path) -> Path | None:
    if not base.exists():
        return None
    # output/ 하위에서 타임스탬프 폴더만 골라서 최신 순 정렬
    dirs = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("20")]
    if not dirs:
        return None
    return sorted(dirs)[-1]


def _load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _render_report_md(strategy: dict, evaluation: dict | None) -> str:
    title = strategy.get("title", "Untitled Strategy")
    objectives = strategy.get("objectives") or []
    modules = strategy.get("modules") or []
    flow = strategy.get("flow") or []
    risks = strategy.get("risks") or []
    meta = strategy.get("meta") or {}

    md = []
    md.append(f"# 📑 전략 리포트")
    md.append("")
    md.append(f"**제목:** {title}")
    md.append(f"**버전:** {meta.get('version','-')}  |  **모델:** {meta.get('model','-')}  |  **생성시각(UTC):** {meta.get('timestamp','-')}")
    md.append("")

    md.append("## 🎯 목표(Objectives)")
    if objectives:
        for i, o in enumerate(objectives, 1):
            md.append(f"- {i}. {o}")
    else:
        md.append("- (없음)")
    md.append("")

    md.append("## 🧩 모듈(Modules)")
    if modules:
        for m in modules:
            name = m.get("name", "-")
            role = m.get("role", "-")
            md.append(f"- **{name}** — {role}")
    else:
        md.append("- (없음)")
    md.append("")

    md.append("## 🔁 흐름(Flow)")
    md.append(" → ".join(flow) if flow else "- (없음)")
    md.append("")

    md.append("## ⚠️ 리스크 & 대응")
    if risks:
        for r in risks:
            md.append(f"- {r}")
    else:
        md.append("- (없음)")
    md.append("")

    if evaluation:
        md.append("## 📊 STRATOS 평가")
        # 숫자/문자 혼합 dict를 깔끔히 나열
        for k, v in evaluation.items():
            md.append(f"- **{k}**: {v}")
        md.append("")

    md.append("> 자동 생성 리포트 • Kai")
    md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Make human-readable report.md from last output.")
    parser.add_argument("--output-root", default="output", help="output 루트 (기본: output)")
    parser.add_argument("--outname", default="report.md", help="생성할 파일명 (기본: report.md)")
    args = parser.parse_args()

    base = Path(args.output_root)
    last_dir = _find_last_output_dir(base)
    if not last_dir:
        print("❌ output/* 하위에 생성된 결과 폴더가 없습니다.")
        sys.exit(1)

    strat_p = last_dir / "strategy.json"
    eval_p = last_dir / "evaluation.json"

    strategy = _load_json(strat_p)
    evaluation = _load_json(eval_p)

    if not strategy:
        print(f"❌ strategy.json을 찾을 수 없거나 파싱 실패: {strat_p}")
        sys.exit(2)

    md = _render_report_md(strategy, evaluation)
    out_path = last_dir / args.outname
    out_path.write_text(md, encoding="utf-8")

    print(f"✅ report 생성 완료: {out_path}")


if __name__ == "__main__":
    main()