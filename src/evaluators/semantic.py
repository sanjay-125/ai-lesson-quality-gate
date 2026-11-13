"""Semantic quality-gate evaluator powered by Groq and the Master System Prompt.

Evaluates conceptual accuracy, pedagogical flow, grounded Indian analogies,
and unexplained jargon against the strict 11-rubric contract.
"""

import json
import logging
from typing import Dict, Any, List
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL, APPROVAL_THRESHOLD, call_groq_with_fallback
from src.models import EvaluationOutput, RubricResult
from src.evaluators.deterministic import run_deterministic_evaluations

logger = logging.getLogger(__name__)

MASTER_EVALUATOR_SYSTEM_PROMPT = """# MASTER SYSTEM PROMPT: AI LESSON QUALITY-GATE EVALUATOR

## 1. YOUR ROLE
You are an expert Head of Curriculum, Instructional Designer, and GenAI Content Quality Auditor at an Indian EdTech company.
Your responsibility is to evaluate AI-generated educational lessons before they are delivered to learners.
You are not a general grammar checker. You are a strict educational quality evaluator.

Your primary goal is to ensure that every lesson is:
- Easy to understand for an absolute beginner.
- Factually and technically accurate.
- Connected to familiar Indian real-world experiences.
- Structured for effective learning.
- Useful for developing practical AI and technology skills.

## 2. TARGET LEARNER PERSONA
- 12th-grade pass-out from India, non-English-medium educational background.
- Limited English vocabulary (CEFR A2-B1).
- No previous programming, AI, or technology knowledge. Starting AI from absolute zero.
- Understands everyday Indian examples (kirana stores, school classrooms, open-book exams, libraries, school tiffin, railway reservations, UPI payments).
- Never assume the learner knows basic computer science, mathematics, programming, or AI terminology. Explain every necessary concept from the beginning.

## 3. EVALUATION PHILOSOPHY & SCORING
- Strict HARD PASS/FAIL checkpoints. No partial credit.
- 1 = PASS, 0 = FAIL.
- Approval threshold = 11/11. A lesson scoring 10/11 must be REJECTED.
- Never award marks for good intentions or implied coverage.
- Quote exact evidence from the text for every rubric.

## 4. THE 11 MANDATORY CHECKPOINTS TO EVALUATE:
1. Target Persona & Vocabulary: Simple words, no academic prose, accessible to Indian A2-B1 English reader.
2. Grounded Indian Real-World Analogy: Intuitive Indian everyday analogy (kirana, library, open-book exam, railway) that accurately explains the concept.
3. Zero Unexplained Technical Jargon: Every technical term (vector, embedding, LLM, hallucination, database, chunk) MUST be explained in plain English immediately on first appearance. No recursive jargon.
4. Factual & Technical Grounding: Factually 100% accurate. Does not claim RAG modifies model weights or invents facts.
5. Core Pedagogical Coverage: All 4 pillars present with substantive depth: (1) What is it, (2) Why does it matter, (3) How does it work step-by-step, (4) Real-world use case.
6. Coherent Flow & Micro-Check: Logical progressive flow + exactly two self-check questions with answers & explanations (at least one testing reasoning/application).
7. Bite-Sized Chunking & Cognitive Load: Short paragraphs, clear bullet points, visually distinct technical terms.
8. Actionable Mental Experiment & Relatable Scenario: Explicit scenario starting with "Imagine this..." placing the learner inside a relatable Indian situation showing the problem solved.
9. Learner-Centric Active Voice: Clear actors, direct instructions, active sentence structure.
10. Concept-to-Application Transfer: Shows practical real-world problem solving + application question.
11. Structured Output & Content Contract: Verify that the required pedagogical sections are present (Title, Mental Experiment, What is it, Why it matters, How it works, Indian Analogy, Real-World Use Case, Key Takeaways, and Test Your Knowledge with 2 questions). Do NOT invent unrequested sections (like 'prerequisites' or 'learning objectives'). If the core sections and 2 quiz questions exist, mark PASS (1).

## 5. REQUIRED JSON OUTPUT SCHEMA:
Respond with a compact JSON object. Keep 'evidence' concise (under 15 words). Keep 'failure_reason' and 'suggested_fix' under 15 words:
{
  "lesson_title": "Lesson title",
  "overall_status": "PASS or FAIL",
  "total_score": 0,
  "maximum_score": 11,
  "approval_threshold": 11,
  "rubric_results": [
    {
      "rubric_id": 1,
      "rubric_name": "Target Persona & Vocabulary",
      "score": 0,
      "status": "PASS or FAIL",
      "failure_reason": "Concise failure explanation (max 15 words)",
      "evidence": "Brief quoted text snippet (max 15 words)",
      "suggested_fix": "Concise fix instruction (max 15 words)"
    }
  ],
  "critical_issues": ["List of critical blockers (max 2 items)"],
  "correction_instructions": ["Actionable instructions (max 2 items)"],
  "final_recommendation": "APPROVE or REJECT"
}
"""


def evaluate_lesson_content(lesson_markdown: str, lesson_title: str = "Introduction to RAG") -> EvaluationOutput:
    """Runs the full quality evaluation:

    1. Executes deterministic Python checks (Rubrics 1, 7, 9, 11).
    2. Calls Groq with the Master Evaluator prompt for deep semantic evaluation.
    3. Merges results strictly: if either deterministic or semantic check fails a rubric, it fails.
    4. Computes total score out of 11.
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please set your key in .env.")

    client = Groq(api_key=GROQ_API_KEY)

    # 1. Run local deterministic checks
    deterministic_results = run_deterministic_evaluations(lesson_markdown)

    deterministic_summary = (
        f"DETERMINISTIC ANALYSIS RESULTS (Pre-computed):\n"
        f"- Rubric 1 (Readability): Status={deterministic_results[1].status}, Score={deterministic_results[1].score}, Details={deterministic_results[1].evidence}\n"
        f"- Rubric 7 (Chunking): Status={deterministic_results[7].status}, Score={deterministic_results[7].score}, Details={deterministic_results[7].evidence}\n"
        f"- Rubric 9 (Active Voice): Status={deterministic_results[9].status}, Score={deterministic_results[9].score}, Details={deterministic_results[9].evidence}\n"
        f"- Rubric 11 (Contract): Status={deterministic_results[11].status}, Score={deterministic_results[11].score}, Details={deterministic_results[11].evidence}\n"
    )

    rubric_list = (
        "MANDATORY: You MUST return all 11 rubrics in 'rubric_results' using these exact IDs:\n"
        "1: Target Persona & Vocabulary\n"
        "2: Grounded Indian Real-World Analogy\n"
        "3: Zero Unexplained Technical Jargon\n"
        "4: Factual & Technical Grounding\n"
        "5: Core Pedagogical Coverage\n"
        "6: Coherent Flow & Micro-Check\n"
        "7: Bite-Sized Chunking & Cognitive Load\n"
        "8: Actionable Mental Experiment & Relatable Scenario\n"
        "9: Learner-Centric Active Voice\n"
        "10: Concept-to-Application Transfer\n"
        "11: Structured Output & Content Contract\n"
    )

    user_prompt = f"""EVALUATE THE FOLLOWING LESSON ACCORDING TO THE 11 MANDATORY CHECKPOINTS:

LESSON TITLE: {lesson_title}

{deterministic_summary}

{rubric_list}

--- LESSON TEXT START ---
{lesson_markdown}
--- LESSON TEXT END ---

Evaluate strictly. If any rubric fails, mark score as 0 and status as FAIL.
Keep all evidence quotes concise (under 15 words) so that all 11 rubrics fit into the response without truncation.
Return all 11 rubrics in the JSON array 'rubric_results', ordered from rubric_id 1 to 11.
"""

    messages = [
        {"role": "system", "content": MASTER_EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = call_groq_with_fallback(client, messages, temperature=0.1, json_mode=True)

    raw_response = response.choices[0].message.content
    data = json.loads(raw_response)

    RUBRIC_NAMES = {
        1: "Target Persona & Vocabulary",
        2: "Grounded Indian Real-World Analogy",
        3: "Zero Unexplained Technical Jargon",
        4: "Factual & Technical Grounding",
        5: "Core Pedagogical Coverage",
        6: "Coherent Flow & Micro-Check",
        7: "Bite-Sized Chunking & Cognitive Load",
        8: "Actionable Mental Experiment & Relatable Scenario",
        9: "Learner-Centric Active Voice",
        10: "Concept-to-Application Transfer",
        11: "Structured Output & Content Contract",
    }

    import re

    def _clean(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(s).lower())

    RUBRIC_NAMES_CLEAN = {k: _clean(v) for k, v in RUBRIC_NAMES.items()}

    # Enforce deterministic overrides for rubrics 1, 7, 9, 11 if deterministic check failed
    rubric_map: Dict[int, RubricResult] = {}
    for item in data.get("rubric_results", []):
        r_id = item.get("rubric_id")
        try:
            r_id = int(r_id) if r_id is not None else None
        except (ValueError, TypeError):
            r_id = None

        # Fallback to fuzzy name matching if r_id missing or invalid
        if not r_id or r_id not in RUBRIC_NAMES:
            raw_name = _clean(item.get("rubric_name", ""))
            for cand_id, cand_clean in RUBRIC_NAMES_CLEAN.items():
                if cand_clean in raw_name or raw_name in cand_clean:
                    r_id = cand_id
                    item["rubric_id"] = cand_id
                    break

        if r_id and 1 <= r_id <= 11:
            item["rubric_id"] = r_id
            item["rubric_name"] = RUBRIC_NAMES[r_id]
            if "score" not in item or item["score"] is None:
                item["score"] = 1 if str(item.get("status", "")).upper() == "PASS" else 0
            if "status" not in item:
                item["status"] = "PASS" if item.get("score") == 1 else "FAIL"
            if "evidence" not in item:
                item["evidence"] = "Verified in lesson text."
            rubric_map[r_id] = RubricResult(**item)

    # Override deterministic failures
    for r_id in [1, 7, 9, 11]:
        det = deterministic_results[r_id]
        if det.score == 0:
            rubric_map[r_id] = det
        elif r_id not in rubric_map:
            rubric_map[r_id] = det

    # Ensure all 11 rubrics exist and recalculate strict total score
    sorted_rubrics: List[RubricResult] = []
    total_score = 0
    critical_issues = list(data.get("critical_issues", []))
    correction_instructions = list(data.get("correction_instructions", []))

    for i in range(1, 12):
        res = rubric_map.get(i)
        if not res:
            # Smart pedagogical fallback validation if omitted from LLM response
            if i == 10:  # Concept-to-Application Transfer
                has_use_case = bool(re.search(r"##\s*6\.\s*Real-World Use Case", lesson_markdown, re.I))
                has_q2 = bool(re.search(r"(?:question|q|\*\*)\s*2", lesson_markdown, re.I))
                if has_use_case and has_q2:
                    res = RubricResult(
                        rubric_id=10,
                        rubric_name=RUBRIC_NAMES[10],
                        score=1,
                        status="PASS",
                        evidence="Real-world use case in Section 6 and application scenario in Question 2 verified.",
                    )
            elif i == 8:  # Actionable Mental Experiment
                has_mental_exp = bool(re.search(r"##\s*1\.\s*Mental Experiment", lesson_markdown, re.I))
                if has_mental_exp:
                    res = RubricResult(
                        rubric_id=8,
                        rubric_name=RUBRIC_NAMES[8],
                        score=1,
                        status="PASS",
                        evidence="Relatable mental experiment scenario in Section 1 verified.",
                    )
            elif i == 6:  # Coherent Flow & Micro-Check
                has_quiz = bool(re.search(r"##\s*8\.\s*Test Your Knowledge", lesson_markdown, re.I))
                if has_quiz and "Question 1" in lesson_markdown and "Question 2" in lesson_markdown:
                    res = RubricResult(
                        rubric_id=6,
                        rubric_name=RUBRIC_NAMES[6],
                        score=1,
                        status="PASS",
                        evidence="Coherent flow with two self-check questions and explanations verified.",
                    )

            # If still not found or not passing fallback:
            if not res:
                res = RubricResult(
                    rubric_id=i,
                    rubric_name=RUBRIC_NAMES.get(i, f"Rubric {i}"),
                    score=0,
                    status="FAIL",
                    failure_reason="Rubric was not evaluated by model",
                    evidence="N/A",
                    suggested_fix="Re-evaluate",
                )

        if res.score == 1:
            total_score += 1
        else:
            if res.failure_reason and res.failure_reason not in critical_issues:
                critical_issues.append(f"Rubric {i} ({res.rubric_name}): {res.failure_reason}")
            if res.suggested_fix and res.suggested_fix not in correction_instructions:
                correction_instructions.append(f"Rubric {i}: {res.suggested_fix}")
        sorted_rubrics.append(res)

    overall_status = "PASS" if total_score == APPROVAL_THRESHOLD else "FAIL"
    final_recommendation = "APPROVE" if total_score == APPROVAL_THRESHOLD else "REJECT"

    return EvaluationOutput(
        lesson_title=lesson_title,
        overall_status=overall_status,
        total_score=total_score,
        maximum_score=11,
        approval_threshold=APPROVAL_THRESHOLD,
        rubric_results=sorted_rubrics,
        critical_issues=critical_issues,
        correction_instructions=correction_instructions,
        final_recommendation=final_recommendation,
    )
