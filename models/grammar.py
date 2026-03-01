from pydantic import BaseModel, Field
from typing import List, Literal


class GrammarIssue(BaseModel):
    excerpt: str = Field(description="The problematic text excerpt")
    issue: str = Field(description="Description of the grammar or language issue")


class GrammarResult(BaseModel):
    grammar_rating: Literal["High", "Medium", "Low"] = Field(
        description="Overall language quality rating"
    )
    issues: List[GrammarIssue] = Field(default_factory=list)
    reasoning: str = Field(description="Overall assessment of language and tone")
