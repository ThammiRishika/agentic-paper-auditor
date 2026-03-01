from pydantic import BaseModel, Field
from typing import List, Optional


class RelatedPaper(BaseModel):
    title: str
    authors: str
    year: Optional[int] = None
    similarity: str = Field(description="Brief description of overlap with the paper under review")


class NoveltyResult(BaseModel):
    novelty_index: str = Field(
        description="Qualitative novelty assessment: e.g. High, Moderate, Low"
    )
    related_papers: List[RelatedPaper] = Field(default_factory=list)
    reasoning: str = Field(description="Explanation of the novelty assessment")
