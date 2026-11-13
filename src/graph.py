"""Agentic Quality-Gate Workflow Engine.

Executes the Generate -> Evaluate -> Regenerate loop with strict binary gating,
audit logging, deliberate flaw injection for demos, and persistent self-evolving memory.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
from src.config import MAX_RETRIES, APPROVAL_THRESHOLD, FINAL_OUTPUT_DIR
from src.models import EvaluationOutput, RejectionLogEntry
from src.evaluators.semantic import evaluate_lesson_content
from src.generator import generate_initial_lesson, regenerate_lesson
from src.memory import memory_store


class QualityGateWorkflow:
    def __init__(self, topic: str = "Introduction to RAG", max_retries: int = MAX_RETRIES):
        self.topic = topic
        self.max_retries = max_retries
        self.iteration = 0
        self.current_markdown = ""
        self.latest_evaluation: Optional[EvaluationOutput] = None
        self.rejection_log: List[RejectionLogEntry] = []
        self.is_approved = False
        self.run_id: Optional[str] = None
        FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run_step_by_step(
        self, deliberate_flaw: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, Dict[str, Any]]:
        """Yields status updates after each step for real-time visualization in Streamlit or CLI."""
        yield {"step": "START", "message": f"Starting quality-gate workflow for topic: '{self.topic}'"}

        # 1. Retrieval of Memory
        evolving_rules = memory_store.get_evolving_constraints()
        yield {
            "step": "MEMORY_RETRIEVED",
            "message": f"Loaded {len(evolving_rules)} negative constraints from persistent memory.",
            "rules": evolving_rules,
        }

        # 2. Initial Generation
        yield {
            "step": "GENERATING",
            "message": f"Generating initial draft (Deliberate flaw: {deliberate_flaw or 'None'})...",
        }
        self.current_markdown = generate_initial_lesson(self.topic, deliberate_flaw=deliberate_flaw)
        self.iteration = 1

        yield {
            "step": "GENERATED",
            "iteration": self.iteration,
            "markdown": self.current_markdown,
            "message": f"Initial draft generated ({len(self.current_markdown.split())} words).",
        }

        # 3. Cyclic Evaluation & Regeneration Loop
        while True:
            yield {
                "step": "EVALUATING",
                "iteration": self.iteration,
                "message": f"Running 11-rubric quality evaluation on iteration {self.iteration}...",
            }

            self.latest_evaluation = evaluate_lesson_content(self.current_markdown, lesson_title=self.topic)
            passed = self.latest_evaluation.total_score == APPROVAL_THRESHOLD

            yield {
                "step": "EVALUATED",
                "iteration": self.iteration,
                "evaluation": self.latest_evaluation,
                "score": self.latest_evaluation.total_score,
                "passed": passed,
                "message": f"Evaluation complete: Score {self.latest_evaluation.total_score}/11 ({self.latest_evaluation.overall_status})",
            }

            if passed:
                self.is_approved = True
                break

            # If failed, log rejection
            failed_rubric_names = [
                f"R{r.rubric_id}: {r.rubric_name}"
                for r in self.latest_evaluation.rubric_results
                if r.score == 0
            ]
            rejection_entry = RejectionLogEntry(
                iteration=self.iteration,
                total_score=self.latest_evaluation.total_score,
                failed_rubrics=failed_rubric_names,
                critical_issues=self.latest_evaluation.critical_issues,
                action_taken="Regenerating with surgical corrections" if self.iteration <= self.max_retries else "Max retries reached; terminated.",
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )
            self.rejection_log.append(rejection_entry)

            # Check termination boundary
            if self.iteration > self.max_retries:
                yield {
                    "step": "MAX_RETRIES_REACHED",
                    "iteration": self.iteration,
                    "message": f"Reached maximum allowed retries ({self.max_retries}). Terminating loop safely.",
                }
                break

            # 4. Surgical Regeneration
            yield {
                "step": "REGENERATING",
                "iteration": self.iteration,
                "message": f"Feeding back {len(failed_rubric_names)} failure critiques for surgical regeneration...",
            }
            self.current_markdown = regenerate_lesson(self.current_markdown, self.latest_evaluation)
            self.iteration += 1

            yield {
                "step": "REGENERATED",
                "iteration": self.iteration,
                "markdown": self.current_markdown,
                "message": f"Revised draft produced for iteration {self.iteration}.",
            }

        # 5. Persist run and write final deliverables
        self._finalize_deliverables()

        final_summary = {
            "step": "COMPLETE",
            "topic": self.topic,
            "is_approved": self.is_approved,
            "final_score": self.latest_evaluation.total_score if self.latest_evaluation else 0,
            "total_iterations": self.iteration,
            "rejection_log": self.rejection_log,
            "lesson_markdown": self.current_markdown,
            "run_id": self.run_id,
        }
        yield final_summary
        return final_summary

    def run(self, deliberate_flaw: Optional[str] = None) -> Dict[str, Any]:
        """Runs the entire workflow synchronously to completion."""
        final_result = {}
        for update in self.run_step_by_step(deliberate_flaw=deliberate_flaw):
            if update.get("step") == "COMPLETE":
                final_result = update
        return final_result

    def _finalize_deliverables(self):
        failed_rubrics = []
        if self.latest_evaluation and self.latest_evaluation.total_score < APPROVAL_THRESHOLD:
            failed_rubrics = [
                r.rubric_name for r in self.latest_evaluation.rubric_results if r.score == 0
            ]

        self.run_id = memory_store.record_run(
            topic=self.topic,
            total_score=self.latest_evaluation.total_score if self.latest_evaluation else 0,
            passed=self.is_approved,
            iterations=self.iteration,
            failed_rubrics=failed_rubrics,
            rejection_reasons=self.latest_evaluation.critical_issues if self.latest_evaluation else [],
            lesson_markdown=self.current_markdown,
        )

        # Write Shippable Lesson
        lesson_file = FINAL_OUTPUT_DIR / "RAG_Lesson.md"
        with open(lesson_file, "w", encoding="utf-8") as f:
            f.write(self.current_markdown)

        # Write Rejection Log
        rejection_file = FINAL_OUTPUT_DIR / "Rejection_Log.md"
        with open(rejection_file, "w", encoding="utf-8") as f:
            f.write(self._format_rejection_log_markdown())

    def _format_rejection_log_markdown(self) -> str:
        md = f"# 📋 Quality-Gate Rejection & Revision Log\n\n"
        md += f"- **Topic**: {self.topic}\n"
        md += f"- **Target Learner**: Class 12 Pass-out from India (Non-English background, starting AI from zero)\n"
        md += f"- **Final Decision**: {'✅ APPROVED & SHIPPED (11/11)' if self.is_approved else '❌ REJECTED'}\n"
        md += f"- **Total Cycles**: {self.iteration}\n"
        md += f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"---\n\n"

        if not self.rejection_log:
            md += "### ✨ Zero Rejections on Initial Run!\nThe initial draft achieved a perfect 11/11 score on all hard checkpoints.\n"
            return md

        for entry in self.rejection_log:
            md += f"## Cycle {entry.iteration}: Score {entry.total_score}/11 (REJECTED)\n\n"
            md += f"### ❌ Failed Rubric Checkpoints:\n"
            for r in entry.failed_rubrics:
                md += f"- **{r}**\n"
            md += f"\n### 🔍 Evaluator Critical Feedback:\n"
            for issue in entry.critical_issues:
                md += f"- {issue}\n"
            md += f"\n### 🛠️ Action Taken:\n{entry.action_taken}\n\n---\n\n"

        return md
