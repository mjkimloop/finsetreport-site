# schemas/strategy.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict

class StrategyRequest(BaseModel):
    domain: str
    user_input: str
    constraints: Dict[str, str] = Field(default_factory=dict)
    meta: Dict[str, str] = Field(default_factory=dict)

class ModuleMeta(BaseModel):
    version: str
    model: str
    timestamp: str

class StructuredStrategy(BaseModel):
    title: str
    objectives: List[str]
    modules: List[Dict[str, str]]  # each: {"name","role","deps"}
    flow: List[str]
    risks: List[str]
    meta: ModuleMeta

class PromptBundle(BaseModel):
    system: str
    user: str
    examples: List[Dict[str, str]] = Field(default_factory=list)

class CodeArtifact(BaseModel):
    filename: str
    language: str
    content: str

class EvalReport(BaseModel):
    score: float
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    used_weights: Dict[str, float] = Field(default_factory=dict)