# resume_screener.py

from typing import List
from pathlib import Path
import openai
import fitz  # PyMuPDF
import re
from resume_screener_models import CriteriaDecision, ResumeScreenerDecision, _format_criteria_str
from dotenv import load_dotenv
import os

load_dotenv()
# Set up OpenAI API key
openai.api_key = os.getenv('OPEN_AI_KEY')

QUERY_TEMPLATE = """
You are an expert resume reviewer.
Your job is to decide if the candidate passes the resume screen given the job description and a list of criteria:

### Job Description
{job_description}

### Screening Criteria
{criteria_str}

### Resume
{resume_content}

Please provide your evaluation in the following format:
Candidate Name: [Name]
Candidate Email: [Email]
Candidate Phone: [Phone]
Overall Reasoning: [Reasoning]
Overall Decision: [True/False]
Overall Score: [Score]

Criteria Decisions:
- Criterion: [Criterion]
  Decision: [True/False]
  Reasoning: [Reasoning]
  Score: [Score]
"""

class ResumeScreenerGPT:
    def __init__(self, job_description: str, criteria: List[str]) -> None:
        self.job_description = job_description
        self.criteria_str = _format_criteria_str(criteria)

    def _read_pdf(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def _generate_query(self, resume_content: str) -> str:
        return QUERY_TEMPLATE.format(
            job_description=self.job_description,
            criteria_str=self.criteria_str,
            resume_content=resume_content
        )

    def screen_resume(self, resume_path: str) -> ResumeScreenerDecision:
        resume_content = self._read_pdf(resume_path)
        query = self._generate_query(resume_content)
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": query}]
        )
        
        response_content = response.choices[0].message.content
        return self._parse_response(response_content)

    def _parse_response(self, response_content: str) -> ResumeScreenerDecision:
        # Extract candidate details
        candidate_name = re.search(r"Candidate Name:\s*(.*)", response_content).group(1).strip()
        candidate_email = re.search(r"Candidate Email:\s*(.*)", response_content).group(1).strip()
        candidate_phone = re.search(r"Candidate Phone:\s*(.*)", response_content).group(1).strip()
        overall_reasoning = re.search(r"Overall Reasoning:\s*(.*)", response_content).group(1).strip()
        overall_decision = re.search(r"Overall Decision:\s*(.*)", response_content).group(1).strip() == 'True'
        overall_score = int(re.search(r"Overall Score:\s*(\d+)", response_content).group(1).strip())

        # Extract criteria decisions
        criteria_decisions = []
        criteria_matches = re.findall(r"- Criterion:\s*(.*)\s*Decision:\s*(.*)\s*Reasoning:\s*(.*)\s*Score:\s*(\d+)", response_content)
        for match in criteria_matches:
            criterion, decision, reasoning, score = match
            criteria_decisions.append(CriteriaDecision(
                decision=decision.strip() == 'True',
                reasoning=reasoning.strip(),
                score=int(score.strip())
            ))

        return ResumeScreenerDecision(
            criteria_decisions=criteria_decisions,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            overall_reasoning=overall_reasoning,
            overall_decision=overall_decision,
            overall_score=overall_score
        )
