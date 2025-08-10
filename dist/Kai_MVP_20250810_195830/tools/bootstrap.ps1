param(
  [string]$Venv = ".venv",
  [string]$Py   = "python",
  [switch]$Preflight
)

# 프로젝트 루트 = tools 상위 폴더
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath    = Join-Path $ProjectRoot $Venv
$VenvPy      = Join-Path $VenvPath "Scripts\python.exe"
$Activate    = Join-Path $VenvPath "Scripts\Activate.ps1"
$Req         = Join-Path $ProjectRoot "requirements.txt"

Write-Host "[bootstrap] project root: $ProjectRoot"

if (!(Test-Path $VenvPy)) {
  Write-Host "[bootstrap] create venv: $VenvPath"
  & $Py -m venv $VenvPath
}

# venv 활성화
. $Activate

Write-Host "[bootstrap] upgrade pip"
python -m pip install -U pip

if (Test-Path $Req) {
  Write-Host "[bootstrap] install requirements"
  pip install -r $Req
} else {
  Write-Host "[bootstrap] requirements.txt not found (skip)"
}

if ($Preflight) {
  Write-Host "[bootstrap] run preflight"
  python (Join-Path $ProjectRoot "tools\preflight_check.py")
}

Write-Host "`n[done] Activate next time with: .\$Venv\Scripts\Activate.ps1"