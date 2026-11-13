"""Persistent self-evolving memory system for the quality-gate pipeline.

Tracks failures across runs, identifies recurring patterns, and synthesizes
dynamic negative constraints to sharpen generator prompts over time.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from src.config import DATA_DIR, AUDIT_LOG_DIR

MEMORY_FILE = DATA_DIR / "memory.json"


class MemoryStore:
    def __init__(self, memory_path: Path = MEMORY_FILE):
        self.memory_path = memory_path
        self._ensure_initialized()

    def _ensure_initialized(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists():
            default_state = {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "recurring_failures": {},
                "learned_negative_constraints": [
                    "Always define technical terms (e.g., RAG, LLM, vectors) immediately in plain English.",
                    "Never write paragraphs exceeding 4 sentences or 60 words.",
                    "Use relatable everyday Indian analogies (kirana shop, open-book exam, school tiffin).",
                    "Keep passive voice strictly below 20% by using direct action verbs."
                ],
                "history": []
            }
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(default_state, f, indent=2)

    def load(self) -> Dict[str, Any]:
        with open(self.memory_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]):
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_evolving_constraints(self) -> List[str]:
        """Returns the dynamic constraints synthesized from historical mistakes."""
        data = self.load()
        return data.get("learned_negative_constraints", [])

    def record_run(
        self,
        topic: str,
        total_score: int,
        passed: bool,
        iterations: int,
        failed_rubrics: List[str],
        rejection_reasons: List[str],
        lesson_markdown: str
    ) -> str:
        """Records a completed run, updates self-evolving constraints, and saves audit logs."""
        data = self.load()
        data["total_runs"] += 1
        if passed:
            data["successful_runs"] += 1
        else:
            data["failed_runs"] += 1

        # Track recurring failures
        for rubric in failed_rubrics:
            count = data["recurring_failures"].get(rubric, 0) + 1
            data["recurring_failures"][rubric] = count

            # Self-evolving mechanism: If a failure recurs 2+ times, synthesize a new negative constraint
            new_rule = f"Strict Warning: Past evaluations frequently failed on '{rubric}'. Ensure strict compliance."
            if count >= 2 and new_rule not in data["learned_negative_constraints"]:
                data["learned_negative_constraints"].append(new_rule)

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_record = {
            "run_id": run_id,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "final_score": total_score,
            "passed": passed,
            "iterations": iterations,
            "failed_rubrics": failed_rubrics,
            "rejection_reasons": rejection_reasons,
        }

        # Keep last 50 runs in history
        data["history"].append(run_record)
        if len(data["history"]) > 50:
            data["history"] = data["history"][-50:]

        self.save(data)

        # Write detailed standalone audit log
        audit_file = AUDIT_LOG_DIR / f"run_{run_id}.json"
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump({**run_record, "lesson_markdown": lesson_markdown}, f, indent=2)

        return run_id


memory_store = MemoryStore()
