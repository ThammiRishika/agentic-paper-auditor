from pydantic import BaseModel, Field
from typing import List, Literal


class AuthenticityResult(BaseModel):
    fabrication_probability: float = Field(
        ge=0.0, le=100.0, description="Estimated % probability of fabrication or significant error"
    )
    risk_level: Literal["Low", "Medium", "High"] = Field(
        description="Overall fabrication risk level"
    )
    reasoning: str = Field(description="Detailed reasoning behind the fabrication assessment")
    red_flags: List[str] = Field(
        default_factory=list,
        description="Specific anomalies or logical leaps identified",
    )
