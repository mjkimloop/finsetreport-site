# run_kai.py
import argparse
from core_engine.qmand_engine import run_qmand_pipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="finsetreport")
    parser.add_argument("--input", required=False, help="사용자 입력")
    args = parser.parse_args()

    user_input = args.input or input("사용자 입력: ").strip()
    result = run_qmand_pipeline(domain=args.domain, user_input=user_input)
    print("\n✅ 최종 결과 요약:")
    print(f"- 전략 제목: {result['strategy']['title']}")
    print(f"- 평가 점수: {result['evaluation']['score']}")

if __name__ == "__main__":
    print("Kai System Initializing...\n")
    main()
