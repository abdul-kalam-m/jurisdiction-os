"""Pydantic schema for §5.4's extraction items. Items failing validation
are dropped and counted, never patched by hand (§5.4: "Items failing
schema validation are dropped and counted, never patched by hand")."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ACTIONS = ("approved", "denied", "carried", "heard", "withdrawn")


class SignalItem(BaseModel):
    meeting_date: str = Field(description="YYYY-MM-DD")
    board: str
    case_ref: str | None = None
    applicant_type: str
    project_desc: str
    use_type: str
    action: Literal["approved", "denied", "carried", "heard", "withdrawn"]
    variances_mentioned: list[str] = Field(default_factory=list)
    source_url: str
    confidence: float = Field(ge=0.0, le=1.0)
    municipality: str | None = None  # added at pipeline level, not by the LLM

    @field_validator("meeting_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"meeting_date must be YYYY-MM-DD, got: {v}")
        return v

    @field_validator("project_desc")
    @classmethod
    def must_describe_project_not_person(cls, v: str) -> str:
        # §6.4: "strip personal names of private individuals... project_desc
        # must describe the project" -- a light heuristic check, not a full
        # NER pass: flag suspiciously short/name-shaped descriptions rather
        # than silently accepting them.
        if len(v.strip()) < 8:
            raise ValueError(f"project_desc too short to be a real project description: {v!r}")
        return v
