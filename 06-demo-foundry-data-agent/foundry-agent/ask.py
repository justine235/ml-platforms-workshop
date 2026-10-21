from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_settings
from eval_harness import LiveAgent, NaiveAgent, OracleAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the fleet-recon agent questions interactively.")
    parser.add_argument("--agent", choices=["live", "oracle", "naive"], default="oracle")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    if args.agent == "oracle":
        agent = OracleAgent()
    elif args.agent == "naive":
        agent = NaiveAgent()
    else:
        agent = LiveAgent(settings, dry_run=args.dry_run)

    print("Enter workshop questions. Press Ctrl+C to exit.")
    while True:
        question = input("> ").strip()
        if not question:
            continue
        if args.agent == "oracle":
            from b4_fleet_demo import load_eval_cases

            match = next((case for case in load_eval_cases() if case.question == question), None)
            if match is None:
                print("Oracle mode only answers the frozen evaluation questions.")
                continue
            result = agent.answer(match)
        elif args.agent == "naive":
            from b4_fleet_demo import load_eval_cases

            match = next((case for case in load_eval_cases() if case.question == question), None)
            if match is None:
                print("Naive mode only answers the frozen evaluation questions.")
                continue
            result = agent.answer(match)
        else:
            result = agent.answer(type("AdHocCase", (), {"case_id": "adhoc", "question": question, "answerable": False})())
        print(result.answer)
        if result.sql:
            print("\nSQL:\n" + result.sql)


if __name__ == "__main__":
    raise SystemExit(main())
