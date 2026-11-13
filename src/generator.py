"""Lesson Generator and Surgical Regenerator Agent powered by Groq.

Designed specifically for an Indian Class 12 learner with limited English vocabulary,
featuring pedagogical scaffolding, everyday Indian analogies, and deliberate error injection.
"""

import json
import logging
from typing import Optional, List
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL, call_groq_with_fallback
from src.models import EvaluationOutput
from src.memory import memory_store

logger = logging.getLogger(__name__)

GENERATOR_SYSTEM_PROMPT = """You are an elite Educational Content Creator and Instructional Designer at an Indian EdTech platform.
You create beginner-friendly, crystal-clear technology lessons for high school graduates in India.

### TARGET LEARNER PERSONA:
- Completed Class 12 in India from a non-English-medium school.
- Limited English vocabulary (CEFR A2-B1 level).
- Starting technology and AI from absolute zero (no coding, no math, no CS background).
- Learns best through everyday Indian situations (kirana stores, open-book exams, railway reservations, school tiffin, libraries).

### CRITICAL PEDAGOGICAL & STRUCTURAL RULES:
0. Concise Lesson Length: Keep the entire lesson between 350 and 450 words total. Every word must count.
1. Short, Bite-Sized Sentences: Keep sentences simple (under 20 words).
2. Cognitive Chunking: Never write more than 3-4 sentences per paragraph. Keep paragraphs under 60 words.
3. Active Voice: Use direct, clear verbs (e.g. "The AI searches the document" instead of "The document is searched by the AI").
4. Zero Unexplained Jargon: Every single technical term MUST be explained immediately in plain, friendly English on its very first appearance:
   - "RAG": State clearly that "RAG stands for Retrieval-Augmented Generation. 'Retrieval' means looking up facts in a document. 'Augmented' means helping or improving. 'Generation' means writing the answer. So, RAG means helping the AI write accurate answers by looking up facts first."
   - "LLM / Large Language Model": State clearly: "Large Language Models (LLMs) are smart computer programs trained on millions of texts to understand language."
   - "Hallucination": State clearly: "When an AI makes up false facts with total confidence, this mistake is called a 'hallucination'."
   - "Database": State clearly: "A database is a digital library of organized facts and information."
5. Grounded Indian Analogy: Use an everyday Indian analogy (e.g., A kirana store owner who does not guess spice prices from memory, but checks his stock ledger before telling the customer / A student writing an open-book exam who checks the textbook before writing the answer).
6. Mandatory Structural Sections:
   - # Lesson Title
   - ## 1. Mental Experiment: Imagine This... (A relatable scenario introducing the problem)
   - ## 2. What is [Topic]? (Simple definition and meaning)
   - ## 3. Why Does It Matter? (What problem does it solve?)
   - ## 4. How Does It Work? (Simple 3-step breakdown)
   - ## 5. Everyday Indian Analogy (Kirana shopkeeper / Open-book exam)
   - ## 6. Real-World Use Case in Action (Practical real-world application like UPI fraud check, bank chatbot, or hospital desk)
   - ## 7. Key Takeaways (Bullet points)
   - ## 8. Test Your Knowledge
     Format exactly with two distinct questions:
     **Question 1:** [Recall question testing the meaning of RAG or its steps]
     A) [Option A]
     B) [Option B]
     **Answer:** [Option] – [Brief explanation]

     **Question 2:** [Practical application/reasoning scenario, e.g., A student asks a college chatbot about hostel admission fees / A customer asks a bank chatbot about new interest rates. Ask how RAG ensures accuracy.]
     A) [Option A]
     B) [Option B]
     **Answer:** [Option] – [Brief explanation showing why retrieving the document first gives the right answer]
"""


def generate_initial_lesson(topic: str, deliberate_flaw: Optional[str] = None) -> str:
    """Generates an initial lesson draft for the given topic.

    If deliberate_flaw is specified, injects a deliberate error to demonstrate
    the evaluator's rejection capability on camera.
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please set your key in .env.")

    client = Groq(api_key=GROQ_API_KEY)
    evolving_rules = memory_store.get_evolving_constraints()
    rules_text = "\n".join([f"- {rule}" for rule in evolving_rules])

    user_prompt = f"""Create a beginner lesson teaching the topic: "{topic}".

HISTORICAL LESSONS LEARNED FROM PAST RUNS (Avoid repeating these mistakes):
{rules_text}

Follow the target persona and all structural rules strictly. Output valid Markdown directly.
"""

    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = call_groq_with_fallback(client, messages, temperature=0.3)

    draft = response.choices[0].message.content.strip()

    # Deterministic deliberate flaw injection for reliable video demonstrations
    if deliberate_flaw == "unexplained_jargon":
        jargon_block = (
            "\n\n### Mathematical Vector Retrieval Pipeline\n"
            "The architecture applies high-dimensional cosine similarity across dense vector embeddings "
            "within an ungrounded latent space manifold, utilizing stochastic metric approximations.\n"
        )
        if "## 4. How Does It Work?" in draft:
            draft = draft.replace("## 4. How Does It Work?", "## 4. How Does It Work?" + jargon_block)
        else:
            draft = draft + jargon_block

    elif deliberate_flaw == "missing_analogy":
        import re
        draft = re.sub(r'## 5\.\s*Everyday Indian Analogy[\s\S]*?(?=## 6\.)', '', draft, flags=re.IGNORECASE)

    elif deliberate_flaw == "poor_chunking":
        run_on_block = (
            "\n\nWhen a student is trying to access and study modern artificial intelligence retrieval systems "
            "they often discover that the underlying server must simultaneously query hundreds of distributed documents "
            "across distant cloud databases while attempting to synchronize the real-time information streams without stopping "
            "to check whether the source material contains any outdated facts or contradictory statements that could confuse "
            "the student during their examination preparation or practice tests.\n\n"
        )
        if "## 3. Why Does It Matter?" in draft:
            draft = draft.replace("## 3. Why Does It Matter?", "## 3. Why Does It Matter?" + run_on_block)
        else:
            draft = run_on_block + draft

    return draft


def regenerate_lesson(previous_markdown: str, evaluation: EvaluationOutput) -> str:
    """Surgically regenerates a rejected lesson based on failed rubrics and feedback."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please set your key in .env.")

    client = Groq(api_key=GROQ_API_KEY)

    failed_items = [r for r in evaluation.rubric_results if r.score == 0]
    feedback_blocks = []
    for f in failed_items:
        feedback_blocks.append(
            f"❌ FAILED RUBRIC {f.rubric_id}: {f.rubric_name}\n"
            f"   - Failure Reason: {f.failure_reason}\n"
            f"   - Problematic Evidence Quoted: {f.evidence}\n"
            f"   - Required Action: {f.suggested_fix}\n"
        )

    feedback_text = "\n".join(feedback_blocks)
    critical_issues_text = "\n".join([f"- {issue}" for issue in evaluation.critical_issues])
    instructions_text = "\n".join([f"- {inst}" for inst in evaluation.correction_instructions])

    user_prompt = f"""The previous draft was REJECTED by the Quality-Gate Evaluator.
Total Score: {evaluation.total_score}/11 (Required: 11/11).

EVALUATOR REJECTION AUDIT & SPECIFIC FEEDBACK:
{feedback_text}

CRITICAL ISSUES TO RESOLVE:
{critical_issues_text}

STEP-BY-STEP CORRECTION INSTRUCTIONS:
{instructions_text}

--- PREVIOUS DRAFT START ---
{previous_markdown}
--- PREVIOUS DRAFT END ---

YOUR TASK:
Surgically revise the lesson to fix EVERY single failed rubric noted above.
1. Preserve and keep intact all sections that were already sound and compliant.
2. Directly resolve the quoted problematic evidence.
3. Keep all paragraphs under 4 sentences and 60 words.
4. Keep sentences under 25 words in active voice.
5. Zero Unexplained Jargon: Every technical term must have an immediate plain-English explanation on first mention:
   - RAG: State that 'Retrieval' means finding facts, 'Augmented' means helping or improving, and 'Generation' means writing the answer.
   - LLM: State that Large Language Models are smart computer programs that understand text.
   - Hallucination: State that it means making up false facts.
6. Indian Analogy: Ensure Section 5 uses a familiar Indian analogy (e.g. Kirana store owner checking stock ledger, or student in open-book exam).
7. Micro-Check Quiz: Section 8 must have '**Question 1:**' (concept recall) and '**Question 2:**' (practical application/reasoning scenario, e.g. college hostel fee chatbot or bank interest rate) with answers and explanations.
8. Return the complete, revised, shippable Markdown lesson.
"""

    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = call_groq_with_fallback(client, messages, temperature=0.2)

    return response.choices[0].message.content.strip()
