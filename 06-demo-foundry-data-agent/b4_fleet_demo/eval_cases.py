from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .reference_data import REFERENCE_OUT_DIR

AGENT_EVAL_PATH = REFERENCE_OUT_DIR / "agent_eval.jsonl"


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    question: str
    case_type: str
    difficulty: str
    expected_answer: str
    expected_values: dict[str, Any]
    tables: tuple[str, ...]
    depends_on_frozen_scores: bool

    @property
    def answerable(self) -> bool:
        return self.expected_values.get("answerable", True)


def load_eval_cases(path: Path = AGENT_EVAL_PATH) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(raw_line)
        cases.append(
            EvalCase(
                case_id=payload["id"],
                question=payload["question"],
                case_type=payload["type"],
                difficulty=payload["difficulty"],
                expected_answer=payload["expected_answer"],
                expected_values=payload["expected_values"],
                tables=tuple(payload["tables"]),
                depends_on_frozen_scores=bool(payload["depends_on_frozen_scores"]),
            )
        )
    return cases
