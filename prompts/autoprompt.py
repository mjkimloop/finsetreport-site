from typing import Dict, List
from schemas.strategy import PromptBundle

DEFAULT_EXAMPLES: List[Dict[str, str]] = [
    {
        "input": "대출 중개 플랫폼을 만들고 싶어",
        "output": "플랫폼 구조, 고객 유입 퍼널, 상담 자동화, 리스크 관리로 전략을 구성한다."
    },
    {
        "input": "핀셋리포트 온보딩 퍼널을 설계해줘",
        "output": "가입 흐름, 인증, 개인정보 최소수집, 이탈 구간 A/B Test 계획을 포함한다."
    }
]

def build_prompt_bundle(
    *,
    system_text: str,
    domain_cfg: Dict,
    user_text: str,
    thinking_combo: Dict
) -> PromptBundle:
    sys_lines = [system_text.strip()]
    goal = (domain_cfg.get("goal") or "").strip()
    if goal:
        sys_lines.append(f"[도메인 목표] {goal}")
    sys_lines.append(f"[사고 프레임] strategy={thinking_combo.get('strategy_frame')}, judgment={thinking_combo.get('judgment')}")
    system = "\n".join(sys_lines)

    user = user_text.strip()
    examples = domain_cfg.get("examples") or DEFAULT_EXAMPLES

    return PromptBundle(system=system, user=user, examples=examples)