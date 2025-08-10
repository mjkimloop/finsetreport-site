# core_engine/model_router.py
from __future__ import annotations
import os
from typing import List, Dict, Any, Optional

class ProviderBase:
    def call(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        raise NotImplementedError

class OpenAIProvider(ProviderBase):
    def call(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        # 실제 API 키 없으면 모의응답
        if not os.getenv("OPENAI_API_KEY"):
            # 가장 최근 user 메시지 에코 기반 모의 JSON (간단)
            last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "[]")
            return f'{{"title":"[openai] draft","objectives":["echo"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"mock","model":"{model}","timestamp":"N/A"}}}}'
        # TODO: 실제 API 바인딩(원하면 이후에 붙이자)
        return f'{{"title":"[openai LIVE]","objectives":["tbd"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"live","model":"{model}","timestamp":"N/A"}}}}'

class AnthropicProvider(ProviderBase):
    def call(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        if not os.getenv("ANTHROPIC_API_KEY"):
            last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "[]")
            return f'{{"title":"[anthropic] draft","objectives":["echo"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"mock","model":"{model}","timestamp":"N/A"}}}}'
        return f'{{"title":"[anthropic LIVE]","objectives":["tbd"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"live","model":"{model}","timestamp":"N/A"}}}}'

class GeminiProvider(ProviderBase):
    def call(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        if not os.getenv("GOOGLE_API_KEY"):
            last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "[]")
            return f'{{"title":"[gemini] draft","objectives":["echo"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"mock","model":"{model}","timestamp":"N/A"}}}}'
        return f'{{"title":"[gemini LIVE]","objectives":["tbd"],"modules":[],"flow":[],"risks":[],"meta":{{"version":"live","model":"{model}","timestamp":"N/A"}}}}'

PROVIDERS: Dict[str, ProviderBase] = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini": GeminiProvider(),
}

def model_call(provider: str, name: str, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    p = PROVIDERS.get(provider)
    if not p:
        raise ValueError(f"Unknown provider: {provider}")
    return p.call(name, messages, temperature)