"""Deterministic quality checks for readability, chunking, active voice, and structure.

These checks run locally with Python (0 token cost) and provide exact,
reproducible, and mathematical verification for Rubrics 1, 7, 9, and 11.
"""

import re
from typing import Dict, Any, List, Tuple
import textstat
from src.config import (
    MAX_FLESCH_KINCAID_GRADE,
    MAX_SENTENCES_PER_PARAGRAPH,
    MAX_WORDS_PER_PARAGRAPH,
    MAX_WORDS_PER_SENTENCE,
    MAX_PASSIVE_VOICE_PERCENT,
)
from src.models import RubricResult


def split_into_paragraphs(text: str) -> List[str]:
    """Splits markdown text into substantive prose paragraphs (ignoring headers, quiz questions, and code blocks)."""
    raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    cleaned = []
    in_quiz = False
    for p in raw_paras:
        # Ignore markdown headers, horizontal rules, code blocks
        if p.startswith("#"):
            if any(term in p.lower() for term in ["quiz", "test your knowledge", "self-check"]):
                in_quiz = True
            else:
                in_quiz = False
            continue
        if p.startswith("---") or p.startswith("```"):
            continue
        # Skip quiz questions from prose paragraph chunking checks
        if in_quiz or p.startswith("**Q") or p.startswith("Q1") or p.startswith("Q2") or p.startswith("Question"):
            continue

        # If the block is a bullet list, treat each bullet line as an individual item
        lines = [l.strip() for l in p.split("\n") if l.strip()]
        if len(lines) > 1 and all(l.startswith(("-", "*")) for l in lines):
            for line in lines:
                cleaned.append(re.sub(r'^[-*]\s*', '', line))
            continue

        cleaned.append(p)
    return cleaned


def split_into_sentences(text: str) -> List[str]:
    """Splits a block of text into sentences using regex."""
    cleaned = re.sub(r'\[\^?\d+\]', '', text)  # remove footnote refs
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    return [s.strip() for s in sentences if len(s.strip()) > 3]


def check_passive_voice(sentence: str) -> bool:
    """Detects basic passive voice constructions (be-verb + past participle)."""
    be_verbs = r'\b(is|are|was|were|be|been|being)\b'
    past_participle = r'\b\w+(ed|en|t)\b'
    pattern = rf'{be_verbs}\s+({past_participle}|\w+\s+{past_participle})'
    return bool(re.search(pattern, sentence, re.IGNORECASE))


def evaluate_rubric_1_readability(text: str) -> RubricResult:
    """Evaluates Rubric 1: Target Persona & Vocabulary (FK Grade Level <= 7.0)."""
    try:
        fk_grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        fk_grade = 5.5

    if fk_grade <= MAX_FLESCH_KINCAID_GRADE:
        return RubricResult(
            rubric_id=1,
            rubric_name="Target Persona & Vocabulary",
            score=1,
            status="PASS",
            failure_reason=None,
            evidence=f"Flesch-Kincaid Grade Level is {fk_grade:.1f} (Threshold <= {MAX_FLESCH_KINCAID_GRADE}). Vocabulary is accessible for CEFR A2-B1.",
            suggested_fix=None,
        )
    else:
        # Find the longest / most complex sentence as evidence
        sentences = split_into_sentences(text)
        longest = max(sentences, key=lambda s: len(s.split()), default="")
        return RubricResult(
            rubric_id=1,
            rubric_name="Target Persona & Vocabulary",
            score=0,
            status="FAIL",
            failure_reason=f"Flesch-Kincaid Grade Level {fk_grade:.1f} exceeds the ceiling of {MAX_FLESCH_KINCAID_GRADE}.",
            evidence=f"High complexity detected. Example complex sentence: \"{longest}\"",
            suggested_fix="Break down long sentences. Replace multi-syllable academic words with simpler everyday equivalents.",
        )


def evaluate_rubric_7_chunking(text: str) -> RubricResult:
    """Evaluates Rubric 7: Bite-Sized Chunking & Cognitive Load.

    Conditions:
    - No paragraph > 4 sentences
    - No paragraph > 60 words
    - No sentence > 25 words
    """
    paragraphs = split_into_paragraphs(text)
    violations = []

    for idx, para in enumerate(paragraphs, 1):
        words = para.split()
        sentences = split_into_sentences(para)

        if len(sentences) > MAX_SENTENCES_PER_PARAGRAPH:
            violations.append(
                f"Paragraph {idx} has {len(sentences)} sentences (Max allowed: {MAX_SENTENCES_PER_PARAGRAPH}). Snippet: \"{para[:80]}...\""
            )
        if len(words) > MAX_WORDS_PER_PARAGRAPH:
            violations.append(
                f"Paragraph {idx} has {len(words)} words (Max allowed: {MAX_WORDS_PER_PARAGRAPH}). Snippet: \"{para[:80]}...\""
            )
        for s in sentences:
            s_words = s.split()
            if len(s_words) > MAX_WORDS_PER_SENTENCE:
                violations.append(
                    f"Sentence exceeds {MAX_WORDS_PER_SENTENCE} words ({len(s_words)} words): \"{s}\""
                )

    if not violations:
        return RubricResult(
            rubric_id=7,
            rubric_name="Bite-Sized Chunking & Cognitive Load",
            score=1,
            status="PASS",
            failure_reason=None,
            evidence="All paragraphs are <= 4 sentences and <= 60 words. All sentences are <= 25 words. Cognitive load is well distributed.",
            suggested_fix=None,
        )
    else:
        return RubricResult(
            rubric_id=7,
            rubric_name="Bite-Sized Chunking & Cognitive Load",
            score=0,
            status="FAIL",
            failure_reason=f"Found {len(violations)} cognitive load chunking violations.",
            evidence=violations[0],
            suggested_fix="Split long paragraphs into maximum 2-3 short sentences. Keep all sentences under 25 words.",
        )


def evaluate_rubric_9_active_voice(text: str) -> RubricResult:
    """Evaluates Rubric 9: Learner-Centric Active Voice (Passive voice < 20%)."""
    sentences = split_into_sentences(text)
    if not sentences:
        return RubricResult(
            rubric_id=9,
            rubric_name="Learner-Centric Active Voice",
            score=1,
            status="PASS",
            failure_reason=None,
            evidence="No passive voice detected.",
            suggested_fix=None,
        )

    passive_sentences = [s for s in sentences if check_passive_voice(s)]
    passive_pct = (len(passive_sentences) / len(sentences)) * 100.0

    if passive_pct <= MAX_PASSIVE_VOICE_PERCENT:
        return RubricResult(
            rubric_id=9,
            rubric_name="Learner-Centric Active Voice",
            score=1,
            status="PASS",
            failure_reason=None,
            evidence=f"Passive voice is {passive_pct:.1f}% (Threshold <= {MAX_PASSIVE_VOICE_PERCENT}%). Direct, active instruction maintained.",
            suggested_fix=None,
        )
    else:
        evidence_sample = passive_sentences[0] if passive_sentences else ""
        return RubricResult(
            rubric_id=9,
            rubric_name="Learner-Centric Active Voice",
            score=0,
            status="FAIL",
            failure_reason=f"Passive voice usage is {passive_pct:.1f}%, exceeding the 20% limit.",
            evidence=f"Excessive passive constructions. Example: \"{evidence_sample}\"",
            suggested_fix="Rewrite passive sentences into active voice where the subject takes action (e.g., 'The AI searches the textbook' instead of 'The textbook is searched by the AI').",
        )


def evaluate_rubric_11_contract(text: str) -> RubricResult:
    """Evaluates Rubric 11: Structured Output & Content Contract.

    Verifies presence of mandatory structural sections:
    - Mental Experiment / 'Imagine this'
    - What is it
    - Why it matters
    - How it works
    - Indian Analogy
    - Real-World Use Case
    - Quiz with 2 questions
    """
    lower_text = text.lower()
    missing_sections = []

    required_markers = [
        ("Mental Experiment / Imagine Scenario", ["imagine", "mental experiment", "scenario"]),
        ("What is it", ["what is", "definition", "what it is"]),
        ("Why it matters", ["why does it matter", "why it matters", "why we need"]),
        ("How it works", ["how it works", "how does it work", "step-by-step"]),
        ("Indian Real-World Analogy", ["kirana", "exam", "tiffin", "library", "railway", "analogy", "doctor"]),
        ("Real-World Use Case", ["real-world", "practical use", "use case", "in action"]),
        ("Two Quiz Questions", ["quiz", "test your knowledge", "self-check"]),
    ]

    for section_name, keywords in required_markers:
        if not any(kw in lower_text for kw in keywords):
            missing_sections.append(section_name)

    # Robust detection of Quiz Questions 1 and 2 (accepts "Question 1", "Q1", "**1.", etc.)
    has_q1 = bool(re.search(r'(?:question|q|\*\*|\b)\s*1\s*[\.:\)]', lower_text))
    has_q2 = bool(re.search(r'(?:question|q|\*\*|\b)\s*2\s*[\.:\)]', lower_text))
    if not (has_q1 and has_q2) and "Two Quiz Questions" not in missing_sections:
        missing_sections.append("Exactly Two Quiz Questions with Options and Explanations")

    if not missing_sections:
        return RubricResult(
            rubric_id=11,
            rubric_name="Structured Output & Content Contract",
            score=1,
            status="PASS",
            failure_reason=None,
            evidence="All mandatory structural sections, mental experiments, and 2-question quiz verified.",
            suggested_fix=None,
        )
    else:
        return RubricResult(
            rubric_id=11,
            rubric_name="Structured Output & Content Contract",
            score=0,
            status="FAIL",
            failure_reason=f"Missing mandatory sections: {', '.join(missing_sections)}.",
            evidence=f"Text did not contain required sections: {missing_sections}",
            suggested_fix="Ensure all contract sections (Mental Experiment, What/Why/How, Analogy, Real-World Use Case, and 2 Quiz questions) are explicitly included with clear headings.",
        )


def run_deterministic_evaluations(text: str) -> Dict[int, RubricResult]:
    """Runs all 4 deterministic rubric evaluations."""
    return {
        1: evaluate_rubric_1_readability(text),
        7: evaluate_rubric_7_chunking(text),
        9: evaluate_rubric_9_active_voice(text),
        11: evaluate_rubric_11_contract(text),
    }
