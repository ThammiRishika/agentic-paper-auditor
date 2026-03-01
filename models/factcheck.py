from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ClaimsOnly(BaseModel):
    """Intermediate model for Pass 1 — raw claim extraction only."""
    claims: List[str] = Field(description="Top factual claims extracted before verification")


class Claim(BaseModel):
    claim: str = Field(description="The factual claim being evaluated")
    status: Literal["verified", "unverified", "incorrect"] = Field(
        description="Verification outcome"
    )
    source: Optional[str] = Field(default=None, description="Source used to verify or refute")
    note: Optional[str] = Field(default=None, description="Any additional context")


class FactCheckResult(BaseModel):
    fact_check_log: List[Claim] = Field(default_factory=list)
    verified_count: int = Field(default=0)
    unverified_count: int = Field(default=0)
    incorrect_count: int = Field(default=0)
