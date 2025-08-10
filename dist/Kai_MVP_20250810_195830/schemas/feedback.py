# schemas/feedback.py
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone

class UserFeedback(BaseModel):
    domain: str = "finsetreport"
    strategy_title: str
    user_score: float = Field(ge=0, le=100)
    feedback_text: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("strategy_title")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        v2 = (v or "").strip()
        if not v2:
            raise ValueError("strategy_title is empty")
        return v2