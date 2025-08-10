import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from schemas.domain_config import load_and_validate_config

def main():
    path = os.path.join("domains", "finsetreport", "config.yaml")
    cfg = load_and_validate_config(path)
    print("[OK] config validated:", cfg.domain_name)

if __name__ == "__main__":
    main()