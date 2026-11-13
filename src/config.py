"""Configuration settings for the AI Lesson Quality-Gate System."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIT_LOG_DIR = DATA_DIR / "audit_logs"
FINAL_OUTPUT_DIR = BASE_DIR / "final_output"
DOCS_DIR = BASE_DIR / "docs"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "openai/gpt-oss-20b")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
APPROVAL_THRESHOLD = int(os.getenv("APPROVAL_THRESHOLD", "11"))
TOTAL_RUBRICS = 11

# Readability & Cognitive Load Thresholds
MAX_FLESCH_KINCAID_GRADE = 7.0
MAX_SENTENCES_PER_PARAGRAPH = 4
MAX_WORDS_PER_PARAGRAPH = 60
MAX_WORDS_PER_SENTENCE = 25
MAX_PASSIVE_VOICE_PERCENT = 20.0


def call_groq_with_fallback(client, messages, temperature=0.2, json_mode=False, max_tokens=850):
    """Executes a Groq chat completion with automatic token bounding to prevent OTPM rate limits."""
    import groq
    import logging

    log = logging.getLogger(__name__)
    params = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        params["response_format"] = {"type": "json_object"}

    try:
        return client.chat.completions.create(model=GROQ_MODEL, **params)
    except groq.RateLimitError as e:
        log.warning(f"Rate limit on {GROQ_MODEL} ({e}). Retrying with fallback model {FALLBACK_MODEL}...")
        return client.chat.completions.create(model=FALLBACK_MODEL, **params)
