from pydantic import BaseModel, Field
from typing import List


class Contradiction(BaseModel):
    location: str = Field(description="Section or claim where the contradiction appears")
    description: str = Field(description="What the contradiction is")


class ConsistencyResult(BaseModel):
    consistency_score: int = Field(ge=0, le=100, description="0–100 internal consistency score")
    contradictions: List[Contradiction] = Field(default_factory=list)
    reasoning: str = Field(description="Overall reasoning behind the score")
