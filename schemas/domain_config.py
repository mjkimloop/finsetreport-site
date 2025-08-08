from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict

class DomainConfig(BaseModel):
    domain_name: str
    goal: str
    constraints: Dict[str, str] = Field(default_factory=dict)
    examples: List[Dict[str, str]] = Field(default_factory=list)
    kpis: List[str] = Field(default_factory=list)
    flow_patterns: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)

def load_and_validate_config(path: str) -> DomainConfig:
    import yaml, json
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    try:
        return DomainConfig.model_validate(raw)
    except ValidationError as e:
        raise RuntimeError(f"[config invalid] {path}\n{e}")