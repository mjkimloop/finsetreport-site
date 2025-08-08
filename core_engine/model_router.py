import os
from typing import Dict, Any, Literal, Optional

ModelName = Literal["openai:gpt-4o-mini", "openai:gpt-4o", "openai:gpt-4.1", "dummy"]

class ModelRouter:
    def __init__(self, default: ModelName = "dummy"):
        self.default = default
        self._openai_client = None

        # 환경변수에 OPENAI_API_KEY가 있으면 클라이언트 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                # pip install openai >= 1.0
                from openai import OpenAI  # type: ignore
                self._openai_client = OpenAI(api_key=api_key)
            except Exception:
                # 라이브러리 없거나 버전 이슈면 LLM 미사용(더미 폴백)
                self._openai_client = None

    def _call_openai(self, model_name: str, prompt: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """
        prompt 예시:
        {
          "system": "...",
          "user": "...",
          "examples": [{"input":"...","output":"..."}, ...]
        }
        반환: {"content": "<string response>"}
        """
        if not self._openai_client:
            return {"content": "[DUMMY] OPENAI_CLIENT_NOT_AVAILABLE"}

        # 메시지 구성 (system / examples / user)
        messages = []
        sys_txt = (prompt.get("system") or "").strip()
        if sys_txt:
            messages.append({"role": "system", "content": sys_txt})

        # few-shot 예시(선택)
        for ex in (prompt.get("examples") or []):
            inp = (ex.get("input") or "").strip()
            out = (ex.get("output") or "").strip()
            if inp:
                messages.append({"role": "user", "content": f"[example-input]\n{inp}"})
            if out:
                messages.append({"role": "assistant", "content": f"[example-output]\n{out}"})

        user_txt = (prompt.get("user") or "").strip()
        if user_txt:
            messages.append({"role": "user", "content": user_txt})

        # Responses API (Responses.create) 또는 Chat.completions.create 중 택1
        # 최신 SDK에서는 client.chat.completions.create 사용 가능
        try:
            resp = self._openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content if resp and resp.choices else ""
            return {"content": content or ""}
        except Exception as e:
            return {"content": f"[DUMMY] OPENAI_CALL_FAILED: {e}"}

    def call(
        self,
        *,
        model: Optional[ModelName] = None,
        prompt: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1800
    ) -> Dict[str, Any]:
        m = model or self.default
        prompt = prompt or {}

        if m.startswith("openai:"):
            return self._call_openai(m.replace("openai:", ""), prompt, max_tokens)

        # 기본 더미 라우트
        return {"content": "[DUMMY] ROUTER_OK"}
        

router = ModelRouter()