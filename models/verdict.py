from pydantic import BaseModel, Field
from typing import Literal


class PeerReviewVerdict(BaseModel):
    recommendation: Literal["Accept", "Minor Revision", "Major Revision", "Reject"] = Field(
        description="Final peer-review recommendation"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the recommendation (0.0–1.0)"
    )
    justification: str = Field(
        description="One concise paragraph synthesising all agent findings into a final verdict"
    )
