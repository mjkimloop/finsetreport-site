from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class StrategyRequest(BaseModel):
    """QMAND → QGEN 입력 계약."""
    domain: str
    user_input: str
    constraints: Dict[str, str] = Field(default_factory=dict)


class ModuleMeta(BaseModel):
    """전략 생성 메타 정보(재현/추적용)."""
    version: str
    model: str
    timestamp: str  # ISO8601 string


class StructuredStrategy(BaseModel):
    """QGEN이 반환해야 하는 전략 구조의 표준 스키마."""
    title: str
    objectives: List[str]
    modules: List[Dict[str, str]]   # 예: {"name": "FunnelDesigner", "role": "전략"}
    flow: List[str]                 # 예: ["Analyzer -> Designer -> Assessor"]
    risks: List[str]
    meta: ModuleMeta


class PromptBundle(BaseModel):
    """오토프롬프트(또는 수동 프롬프트) 표준 스키마."""
    system: str
    user: str
    examples: List[Dict[str, str]] = Field(default_factory=list)


class CodeArtifact(BaseModel):
    """젠키트/코드 생성 산출물 표준 스키마(기존)."""
    filename: str
    language: str
    content: str


class EvalReport(BaseModel):
    """STRATOS 평가 결과 표준 스키마(기존 파이프라인 유지)."""
    score: float
    findings: List[str]
    recommendations: List[str]


# === Guardian 확장용 추가 스키마들 ===

class StratosScore(BaseModel):
    """세부 항목 점수 스키마(선택적: 필요 시 병행 사용)."""
    전략성: float = Field(ge=0, le=100)
    설명력: float = Field(ge=0, le=100)
    리스크_대응력: float = Field(ge=0, le=100)
    총점: float = Field(ge=0, le=100)


class GeneratedCode(BaseModel):
    """코드 생성 산출물의 최소 계약(Guardian 검증용)."""
    filename: str
    language: str
    content: str