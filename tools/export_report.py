# tools/export_report.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, webbrowser
from datetime import datetime
from typing import Any, Dict, List

# ========= 공통 유틸 =========
def _as_plain(obj: Any) -> Any:
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
    except Exception:
        pass
    return obj

def _norm_strategy(strategy: Any) -> Dict[str, Any]:
    s = _as_plain(strategy) or {}
    return {
        "title": s.get("title", ""),
        "objectives": s.get("objectives", []) or [],
        "modules": s.get("modules", []) or [],
        "flow": s.get("flow", []) or [],
        "risks": s.get("risks", []) or [],
        "meta": s.get("meta", {}) or {},
    }

def _norm_eval(evaluation: Any) -> Dict[str, Any]:
    e = _as_plain(evaluation) or {}
    try:
        score = float(e.get("score", 0.0))
    except Exception:
        score = 0.0
    return {
        "score": score,
        "findings": e.get("findings", []) or [],
        "recommendations": e.get("recommendations", []) or [],
    }

def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# ========= Markdown =========
def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")

def export_markdown_report(strategy: Any, evaluation: Any, output_dir: str, open_file: bool=False, **kwargs) -> str:
    _ensure_dir(output_dir)
    S, E = _norm_strategy(strategy), _norm_eval(evaluation)
    meta = S["meta"] or {}

    lines: List[str] = []
    lines.append(f"# 전략 리포트  \n`STRATOS {E['score']}`")
    lines.append(f"*생성 시각(UTC): {meta.get('timestamp','')} · 모델: {meta.get('model','')} · 버전: {meta.get('version','')}*")
    lines.append("\n## 제목\n" + S["title"])

    lines.append("\n## 평가 요약 (STRATOS)")
    for f in E["findings"]:
        lines.append(f"- {f}")
    if E["recommendations"]:
        lines.append("\n**권장 사항**")
        for r in E["recommendations"]:
            lines.append(f"- {r}")

    lines.append("\n## 목표 (Objectives)")
    for o in S["objectives"]:
        lines.append(f"- {o}")

    lines.append("\n## 모듈 구성")
    lines += ["| 모듈 | 역할 | 선행모듈 |", "|---|---|---|"]
    for m in S["modules"]:
        lines.append(f"| {_md_escape(m.get('name',''))} | {_md_escape(m.get('role',''))} | {_md_escape(m.get('deps',''))} |")

    lines.append("\n## 실행 흐름 (Flow)")
    if S["flow"]:
        lines.append("1. " + " → ".join(S["flow"]))

    if S["risks"]:
        lines.append("\n## 주요 리스크")
        for r in S["risks"]:
            lines.append(f"- {r}")

    lines.append("\n## 메타")
    lines.append(f"- version: {meta.get('version','')}")
    lines.append(f"- model: {meta.get('model','')}")
    lines.append(f"- timestamp: {meta.get('timestamp','')}")

    path = os.path.join(output_dir, f"report_domain_{_ts()}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[export] Markdown -> {path}")
    if open_file:
        webbrowser.open(f"file://{os.path.abspath(path)}")
    return path

# ========= HTML =========
def export_html_report(strategy: Any, evaluation: Any, output_dir: str, open_file: bool=False, **kwargs) -> str:
    _ensure_dir(output_dir)
    S, E = _norm_strategy(strategy), _norm_eval(evaluation)
    meta = S["meta"] or {}

    def _li(items: List[str]) -> str:
        return "".join(f"<li>{item}</li>" for item in items)

    def _rows(mods: List[Dict[str, str]]) -> str:
        return "".join(
            f"<tr><td>{m.get('name','')}</td><td>{m.get('role','')}</td><td>{m.get('deps','')}</td></tr>"
            for m in mods
        )

    html = f"""<!doctype html><html lang="ko"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Kai 전략 리포트</title>
<style>
body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans KR','Malgun Gothic',sans-serif;line-height:1.5;margin:32px;color:#111}}
h1{{font-size:24px;margin:0 0 12px}}
h2{{font-size:18px;margin:22px 0 8px}}
.badge{{display:inline-block;background:#e8f0ff;color:#1a56db;padding:2px 10px;border-radius:999px;margin-left:8px;font-size:12px;font-weight:700}}
.meta{{color:#555;font-size:14px;margin:0 0 18px}}
.tbl{{border-collapse:collapse;width:100%;margin:8px 0 16px}}
.tbl th,.tbl td{{border:1px solid #ddd;padding:8px;text-align:left}}
.tbl th{{background:#fafafa}}
.flow{{padding:10px 12px;background:#fafafa;border:1px solid #eee;border-radius:8px}}
ul{{margin:6px 0 12px 18px}}
small.muted{{color:#777}}
</style></head><body>
<h1>전략 리포트 <span class='badge'>STRATOS {E['score']}</span></h1>
<div class='meta'>생성 시각(UTC): {meta.get('timestamp','')} · 모델: {meta.get('model','')} · 버전: {meta.get('version','')}</div>

<h2>제목</h2><p>{S['title']}</p>

<h2>평가 요약 (STRATOS)</h2>
<p><b>세부 지표</b></p>
<ul>{_li([str(x) for x in E['findings']])}</ul>
{("<p><b>권장 사항</b></p><ul>"+_li(E['recommendations'])+"</ul>") if E['recommendations'] else ""}

<h2>목표 (Objectives)</h2><ul>{_li(S['objectives'])}</ul>

<h2>모듈 구성</h2>
<table class='tbl'><thead><tr><th>모듈</th><th>역할</th><th>선행모듈</th></tr></thead>
<tbody>{_rows(S['modules'])}</tbody></table>

<h2>실행 흐름 (Flow)</h2>
<div class='flow'>{" → ".join(S['flow'])}</div>

{("<h2>주요 리스크</h2><ul>"+_li(S['risks'])+"</ul>") if S['risks'] else ""}

<h2>메타</h2>
<ul><li>version: {meta.get('version','')}</li><li>model: {meta.get('model','')}</li><li>timestamp: {meta.get('timestamp','')}</li></ul>
<small class="muted">Generated by Kai</small>
</body></html>"""
    path = os.path.join(output_dir, f"report_domain_{_ts()}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[export] HTML -> {path}")
    if open_file:
        webbrowser.open(f"file://{os.path.abspath(path)}")
    return path

# ========= PDF =========
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 레이아웃 상수(일괄 간격 통일)
MARGIN_X = 50
TOP_MARGIN = 60
BOTTOM_MARGIN = 60
SECTION_GAP = 16         # 섹션 간 기본 간격
PARA_GAP = 10            # 단락 간 간격
LIST_GAP = 6             # 리스트 아이템 간 간격
TABLE_GAP = 16

def _register_kr_font(prefer: str = "NotoSansKR") -> str:
    candidates = [
        ("NotoSansKR", "assets/fonts/NotoSansKR-Regular.ttf"),
        ("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"),
        ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),
        ("MalgunGothic", "C:\\Windows\\Fonts\\malgun.ttf"),
    ]
    for name, path in candidates:
        if prefer == name and os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                pass
    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue
    return "Helvetica"

def _new_page_if_needed(c: Canvas, y: float, need: float, font_name: str) -> float:
    if y - need < BOTTOM_MARGIN:
        c.showPage()
        c.setFont(font_name, 11)
        return A4[1] - TOP_MARGIN
    return y

def _draw_badge_right(c: Canvas, y_baseline: float, text: str):
    pad_x, pad_y = 8, 3
    c.setFont(c._fontname, 10)
    w = c.stringWidth(text, c._fontname, 10) + pad_x * 2
    h = 14
    x = A4[0] - MARGIN_X - w  # 오른쪽 끝 정렬
    c.setFillColorRGB(0.10, 0.34, 0.86)
    c.roundRect(x, y_baseline - h + 3, w, h, 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.drawString(x + pad_x, y_baseline - h + 6, text)
    c.setFillColor(colors.black)

def _h1(c: Canvas, y: float, text: str) -> float:
    c.setFont(c._fontname, 16)
    c.drawString(MARGIN_X, y, text)
    return y - 26

def _h2(c: Canvas, y: float, text: str) -> float:
    c.setFont(c._fontname, 12)
    y = _new_page_if_needed(c, y, 20, c._fontname)
    c.drawString(MARGIN_X, y, text)
    return y - SECTION_GAP

def _paragraph(c: Canvas, y: float, text: str, width: float, style: ParagraphStyle) -> float:
    p = Paragraph(text, style)
    w, h = p.wrapOn(c, width, 0)
    y = _new_page_if_needed(c, y, h, style.fontName)
    p.drawOn(c, MARGIN_X, y - h)
    return y - h - PARA_GAP

def _list(c: Canvas, y: float, items: List[str], width: float, style: ParagraphStyle) -> float:
    for it in items:
        y = _paragraph(c, y, f"&bull; {it}", width, style)
        y -= (LIST_GAP - 2)
    return y + (LIST_GAP - 2)

def _table(c: Canvas, y: float, data: List[List[str]], col_w: List[float], font_name: str) -> float:
    tbl = Table(data, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    w, h = tbl.wrapOn(c, A4[0] - MARGIN_X*2, 0)
    y = _new_page_if_needed(c, y, h, font_name)
    tbl.drawOn(c, MARGIN_X, y - h)
    return y - h - TABLE_GAP

def export_pdf_report(strategy: Any, evaluation: Any, output_dir: str,
                      open_file: bool=False, font_name: str="NotoSansKR",
                      logo_path: str|None=None, debug: bool=False, quiet: bool=False, **kwargs) -> str:
    _ensure_dir(output_dir)
    S, E = _norm_strategy(strategy), _norm_eval(evaluation)
    meta = S["meta"] or {}

    kr_font = _register_kr_font(font_name)
    path = os.path.join(output_dir, f"report_domain_{_ts()}.pdf")
    c = Canvas(path, pagesize=A4)
    c.setFont(kr_font, 11)
    c._fontname = kr_font  # keep for helpers

    width, height = A4
    y = height - TOP_MARGIN

    # 제목 + 배지(우측 고정)
    y_title_base = y
    y = _h1(c, y, "전략 리포트")
    _draw_badge_right(c, y_title_base, f"STRATOS {E['score']}")

    # 메타 (제목 아래로 확실히 내림)
    meta_line = f"생성 시각(UTC): {meta.get('timestamp','')} · 모델: {meta.get('model','')} · 버전: {meta.get('version','')}"
    c.setFont(kr_font, 9); c.setFillColor(colors.grey)
    c.drawString(MARGIN_X, y_title_base - 14, meta_line)
    c.setFillColor(colors.black)
    y = y - 8  # 제목과 다음 섹션 사이 추가 여백

    # 로고(선택)
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, width - 140, height - 80, width=90, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    pstyle = ParagraphStyle("KR", fontName=kr_font, fontSize=11, leading=15)

    # 제목 섹션
    y = _h2(c, y, "제목")
    y = _paragraph(c, y, S["title"], width - MARGIN_X*2, pstyle)

    # 평가 요약
    y = _h2(c, y, "평가 요약 (STRATOS)")
    y = _list(c, y, [str(f) for f in E["findings"]], width - MARGIN_X*2, pstyle)
    if E["recommendations"]:
        y = _paragraph(c, y, "<b>권장 사항</b>", width - MARGIN_X*2, pstyle)
        y = _list(c, y, E["recommendations"], width - MARGIN_X*2, pstyle)
    y -= 4  # 리스트와 다음 섹션 사이 살짝 더 띄움

    # 목표
    y = _h2(c, y, "목표 (Objectives)")
    if S["objectives"]:
        y = _list(c, y, S["objectives"], width - MARGIN_X*2, pstyle)
    y -= 4

    # 모듈 구성
    y = _h2(c, y, "모듈 구성")
    data = [["모듈", "역할", "선행모듈"]]
    for m in S["modules"]:
        data.append([m.get("name",""), m.get("role",""), m.get("deps","")])
    y = _table(c, y, data, [110, 280, 110], kr_font)

    # 실행 흐름
    y = _h2(c, y, "실행 흐름 (Flow)")
    flow_text = " → ".join(S["flow"]) if S["flow"] else ""
    y = _paragraph(c, y, flow_text, width - MARGIN_X*2, pstyle)

    # 리스크
    if S["risks"]:
        y = _h2(c, y, "주요 리스크")
        y = _list(c, y, S["risks"], width - MARGIN_X*2, pstyle)
        y -= 6  # 리스크와 메타 사이 간격 확장

    # 메타
    y = _h2(c, y, "메타")
    meta_items = [
        f"version: {meta.get('version','')}",
        f"model: {meta.get('model','')}",
        f"timestamp: {meta.get('timestamp','')}",
    ]
    y = _list(c, y, meta_items, width - MARGIN_X*2, pstyle)

    c.showPage(); c.save()
    if not quiet:
        print(f"[export] PDF -> {path}")
    if open_file:
        webbrowser.open(f"file://{os.path.abspath(path)}")
    return path