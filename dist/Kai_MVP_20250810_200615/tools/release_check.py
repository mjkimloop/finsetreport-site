# tools/release_check.py
from __future__ import annotations
import os, sys, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY   = sys.executable

def run(cmd: list[str], cwd: Path | None = None, env_extra: dict | None = None):
    """
    UTF-8로 안전하게 하위 프로세스 실행.
    Windows 콘솔(cp949)에서도 깨지지 않도록 encoding='utf-8', errors='replace' 사용.
    """
    env = os.environ.copy()
    # 하위 프로세스에 UTF-8 강제
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)

    p = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    # p.stdout / p.stderr 가 None 이면 빈 문자열로 대체
    out = p.stdout or ""
    err = p.stderr or ""
    return p.returncode, out.strip(), err.strip()

def latest_dir(base: Path) -> Path | None:
    dirs = [d for d in base.iterdir() if d.is_dir()]
    return max(dirs, key=lambda d: d.stat().st_mtime) if dirs else None

def have_files(d: Path, patterns: list[str]) -> dict[str, bool]:
    return {pat: any(d.glob(pat)) for pat in patterns}

def main():
    print("[ReleaseCheck] start")
    print("Project:", ROOT)

    # 1) Preflight
    print("\n[1/3] Preflight…")
    rc, out, err = run([PY, "tools/preflight_check.py"])
    if out: print(out)
    if err: print(err)
    preflight_ok = (rc == 0) and ("ALL GREEN" in (out + err))

    # 2) Golden tests
    print("\n[2/3] Golden tests…")
    rc2, out2, err2 = run(
        [PY, "-X", "utf8", "tests/golden/run_golden_tests.py"],
        env_extra={"PYTHONPATH": str(ROOT)},
    )
    if out2: print(out2)
    if err2: print(err2)
    # run_golden_tests.py 는 changed/error 시 exit 1 이므로 rc2==0 이면 통과
    golden_ok = (rc2 == 0)

    # 3) Sample run + export(all)
    print("\n[3/3] Sample run & export(all)…")
    rc3, out3, err3 = run(
        [PY, "run_kai.py", "--domain", "finsetreport", "--input", "릴리스 체크 전략", "--export", "all", "--quiet"]
    )
    if out3: print(out3)
    if err3: print(err3)

    out_dir = latest_dir(ROOT / "output")
    files = {"strategy.json": False, "evaluation.json": False, "*.md": False, "*.html": False, "*.pdf": False}
    export_ok = False
    if out_dir:
        files = have_files(out_dir, list(files.keys()))
        export_ok = all(files.values())

    summary = {
        "preflight_ok": preflight_ok,
        "golden_ok": golden_ok,
        "export_ok": export_ok,
        "output_dir": str(out_dir) if out_dir else None,
        "files": files,
    }
    print("\n=== Release Summary ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if all([preflight_ok, golden_ok, export_ok]):
        print("\n✅ Ready to release")
        sys.exit(0)
    else:
        print("\n❌ Not ready. Fix items above.")
        sys.exit(1)

if __name__ == "__main__":
    main()