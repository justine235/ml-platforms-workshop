from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PIPELINE = ROOT / "02-demo-data" / "fleet_reference_pipeline.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the shared pandas reference pipeline from AML for small-data demos only.")
    parser.add_argument("--data", required=True, help="Raw data folder")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--truth", required=True, help="Truth folder")
    parser.add_argument("--with-drift", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [
        sys.executable,
        str(REFERENCE_PIPELINE),
        "--data",
        args.data,
        "--out",
        args.out,
        "--truth",
        args.truth,
    ]
    if args.with_drift:
        command.append("--with-drift")
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
