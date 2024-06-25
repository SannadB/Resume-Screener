# resume_screener_models.py

from typing import List
from pydantic import BaseModel, Field

class CriteriaDecision(BaseModel):
    """The decision made based on a single criteria."""
    decision: bool = Field(description="The decision made based on the criteria")
    reasoning: str = Field(description="The reasoning behind the decision")
    score: int = Field(description="The score behind the decision out of 100")

class ResumeScreenerDecision(BaseModel):
    """The decision made by the resume screener."""
    criteria_decisions: List[CriteriaDecision] = Field(description="The decisions made based on the criteria")
    candidate_name: str = Field(description="Name of Candidate")
    candidate_email: str = Field(description="Email of Candidate")
    candidate_phone: str = Field(description="Contact number of Candidate")
    overall_reasoning: str = Field(description="The reasoning behind the overall decision")
    overall_decision: bool = Field(description="The overall decision made based on the criteria")
    overall_score: int = Field(description="The overall score based on the criteria out of 100")

def _format_criteria_str(criteria: List[str]) -> str:
    criteria_str = ""
    for criterion in criteria:
        criteria_str += f"- {criterion}\n"
    return criteria_str
