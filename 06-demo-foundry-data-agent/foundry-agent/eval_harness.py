from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from b4_fleet_demo import create_local_session, load_eval_cases, score_structured_result
from config import Settings, load_settings

DATA_AGENT_DIR = Path(__file__).resolve().parents[1] / "data-agent"
EXAMPLE_QUERIES_PATH = DATA_AGENT_DIR / "example-queries.json"


@dataclass
class AgentTurnResult:
    answer: str
    structured: dict[str, Any]
    refused: bool = False
    sql: str | None = None


class OracleAgent:
    def __init__(self) -> None:
        sys.path.insert(0, str(DATA_AGENT_DIR))
        from validate_examples import (  # type: ignore
            dataframe_to_records,
            load_examples,
            structure_result,
            transpile_tsql,
        )

        self._load_examples = load_examples
        self._structure_result = structure_result
        self._transpile_tsql = transpile_tsql
        self._dataframe_to_records = dataframe_to_records
        self._examples = {item["id"]: item for item in self._load_examples()}
        self._connection = create_local_session()

    def answer(self, case) -> AgentTurnResult:
        example = self._examples[case.case_id]
        if example["mode"] == "refuse":
            return AgentTurnResult(answer=case.expected_answer, structured={"answerable": False, "refused": True}, refused=True)
        sql_text = self._transpile_tsql(example["tsql"])
        rows = self._dataframe_to_records(self._connection, sql_text)
        structured = self._structure_result(case.case_id, rows, example["mode"])
        return AgentTurnResult(answer=case.expected_answer, structured=structured, sql=sql_text)

    def close(self) -> None:
        self._connection.close()


class NaiveAgent:
    def answer(self, case) -> AgentTurnResult:
        if not case.answerable:
            return AgentTurnResult(answer="Yes, I can do that.", structured={"answerable": True, "refused": False})
        return AgentTurnResult(answer="0", structured={"wrong": True})


class LiveAgent:
    def __init__(self, settings: Settings, *, dry_run: bool = False) -> None:
        self.settings = settings
        self.dry_run = dry_run

    def answer(self, case) -> AgentTurnResult:
        if self.dry_run:
            return AgentTurnResult(
                answer="DRY RUN: live Foundry invocation not executed.",
                structured={"answerable": False, "refused": True},
                refused=True,
            )
        raise NotImplementedError(
            "Live agent execution is environment-specific in this preview stack. "
            "Use --dry-run locally and wire the tenant-specific execution path before Friday."
        )


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = Counter()
    by_type_pass = Counter()
    by_difficulty = Counter()
    by_difficulty_pass = Counter()
    for result in results:
        by_type[result["type"]] += 1
        by_difficulty[result["difficulty"]] += 1
        if result["passed"]:
            by_type_pass[result["type"]] += 1
            by_difficulty_pass[result["difficulty"]] += 1
    return {
        "pass_rate": sum(result["passed"] for result in results) / len(results),
        "by_type": {
            key: {"passed": by_type_pass[key], "total": by_type[key]}
            for key in sorted(by_type)
        },
        "by_difficulty": {
            key: {"passed": by_difficulty_pass[key], "total": by_difficulty[key]}
            for key in sorted(by_difficulty)
        },
    }


def render_markdown(results: list[dict[str, Any]], summary: dict[str, Any], agent_name: str) -> str:
    lines = [
        f"# Eval report: {agent_name}",
        "",
        f"- Pass rate: {summary['pass_rate'] * 100:.1f}%",
        "",
        "## By type",
        "",
        "| Type | Passed | Total |",
        "| --- | ---: | ---: |",
    ]
    for key, counts in summary["by_type"].items():
        lines.append(f"| {key} | {counts['passed']} | {counts['total']} |")
    lines.extend(["", "## By difficulty", "", "| Difficulty | Passed | Total |", "| --- | ---: | ---: |"])
    for key, counts in summary["by_difficulty"].items():
        lines.append(f"| {key} | {counts['passed']} | {counts['total']} |")
    failures = [result for result in results if not result["passed"]]
    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- **{failure['id']}** {failure['question']}: {'; '.join(failure['details'])}")
    return "\n".join(lines) + "\n"


def run_harness(agent_name: str, *, dry_run: bool = False) -> dict[str, Any]:
    cases = load_eval_cases()
    settings = load_settings()
    if agent_name == "oracle":
        agent = OracleAgent()
    elif agent_name == "naive":
        agent = NaiveAgent()
    elif agent_name == "live":
        agent = LiveAgent(settings, dry_run=dry_run)
    else:
        raise ValueError(f"Unknown agent {agent_name}")

    results: list[dict[str, Any]] = []
    for case in cases:
        turn = agent.answer(case)
        score = score_structured_result(case, turn.structured)
        results.append(
            {
                "id": case.case_id,
                "question": case.question,
                "type": case.case_type,
                "difficulty": case.difficulty,
                "passed": score.passed,
                "details": score.details,
                "sql": turn.sql,
                "refused": turn.refused,
                "answer": turn.answer,
                "structured": turn.structured,
            }
        )
    if hasattr(agent, "close"):
        agent.close()
    summary = summarize(results)
    return {"agent": agent_name, "results": results, "summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the fleet-recon evaluation harness.")
    parser.add_argument("--agent", choices=["live", "oracle", "naive"], default="oracle")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", default=str(Path(__file__).with_name("reports")))
    args = parser.parse_args()

    payload = run_harness(args.agent, dry_run=args.dry_run)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.agent}-eval.json"
    md_path = out_dir / f"{args.agent}-eval.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload["results"], payload["summary"], args.agent), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if payload["summary"]["pass_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
