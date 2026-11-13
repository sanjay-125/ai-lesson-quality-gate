"""Data models and schemas for the Quality-Gate system."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RubricResult(BaseModel):
    rubric_id: int = Field(..., description="ID from 1 to 11")
    rubric_name: str = Field(..., description="Official rubric name")
    score: int = Field(default=1, description="Strict binary score: 0 (FAIL) or 1 (PASS)")
    status: str = Field(default="PASS", description="PASS or FAIL status")
    failure_reason: Optional[str] = Field(None, description="Specific explanation if failed, or concise rationale if passed")
    evidence: str = Field(default="N/A", description="Exact quoted text from the lesson as evidence")
    suggested_fix: Optional[str] = Field(None, description="Actionable correction guidance if failed")


class EvaluationOutput(BaseModel):
    lesson_title: str
    overall_status: Literal["PASS", "FAIL"]
    total_score: int = Field(..., ge=0, le=11)
    maximum_score: int = 11
    approval_threshold: int = 11
    rubric_results: List[RubricResult]
    critical_issues: List[str] = Field(default_factory=list)
    correction_instructions: List[str] = Field(default_factory=list)
    final_recommendation: Literal["APPROVE", "REJECT"]


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    question_type: Literal["reasoning_application", "concept_comprehension"]


class LessonContent(BaseModel):
    title: str
    target_audience: str = "Class 12 pass-out from India, non-English background, starting AI from zero"
    mental_experiment: str
    what_is_it: str
    why_it_matters: str
    how_it_works: str
    indian_analogy: str
    real_world_use_case: str
    key_takeaways: List[str]
    quiz: List[QuizQuestion]
    raw_markdown: str


class RejectionLogEntry(BaseModel):
    iteration: int
    total_score: int
    failed_rubrics: List[str]
    critical_issues: List[str]
    action_taken: str
    timestamp: str


class GenerationState(BaseModel):
    topic: str
    iteration: int = 0
    max_retries: int = 2
    current_lesson: Optional[LessonContent] = None
    current_markdown: str = ""
    latest_evaluation: Optional[EvaluationOutput] = None
    rejection_log: List[RejectionLogEntry] = Field(default_factory=list)
    is_approved: bool = False
    deliberate_flaw_type: Optional[str] = None  # e.g., "unexplained_jargon", "missing_analogy"
