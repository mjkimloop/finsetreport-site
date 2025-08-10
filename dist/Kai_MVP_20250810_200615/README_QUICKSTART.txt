# Kai MVP Quickstart (Windows, PowerShell)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python run_kai.py --domain finsetreport --input "가입 온보딩 최적화 전략" --export all --open
