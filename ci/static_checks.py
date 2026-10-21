"""Repository checks that need no cloud access and no heavy dependencies.

It parses every YAML, JSON and notebook file, and keeps the repository neutral: no customer name, no absolute local
paths, no secrets, no mojibake. Run it from anywhere:  python ci/static_checks.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Split literals: this file must not contain the words it forbids.
CUSTOMER = "vi" + "nci"
ALIAS = "j" + "charley"
DEMO_TENANT = "cal" + "dova"

TEXT_RULES = {
    "customer name": re.compile(r"\b" + CUSTOMER + r"\b", re.I),
    "personal alias": re.compile(ALIAS, re.I),
    "demo tenant name": re.compile(DEMO_TENANT, re.I),
    "absolute Windows user path": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+\w", re.I),
    "absolute Unix home path": re.compile(r"(?<![\w.])/(?:home|Users)/[a-z][\w.-]*/", re.I),
    "local scratch folder": re.compile(r"\b_(?:scratch|venvs)\b"),
    "mojibake": re.compile("\ufffd|\u00c3[\u00a0-\u00bf]|\u00e2\u20ac"),
    "SAS signature": re.compile(r"[?&]sig=[A-Za-z0-9%/+=]{20,}"),
    "storage account key": re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp_|gho_|ghs_|github_pat_)[A-Za-z0-9_]{20,}"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}"),
}

BINARY_SUFFIXES = {".pptx", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".gz", ".zip", ".parquet", ".pyc", ".ttf", ".woff", ".woff2", ".pdf"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "mlruns", ".pytest_cache", ".ruff_cache"}
SKIP_PREFIXES = (
    "02-demo-data/data/",
    "02-demo-data/truth/",
    "01-slides/out/",
    "01-slides/content/",
)
SKIP_PARTS = ("/local-validation/artifacts/", "/local-validation/out/", "/local-validation/work/")
MAX_BYTES = 6_000_000


def candidate_files() -> list[Path]:
    """Tracked and untracked-but-not-ignored files inside a git repository, otherwise a filtered walk."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout.decode("utf-8", "replace").split("\0")
        files = [ROOT / p for p in listed if p]
        if files:
            return [p for p in files if p.is_file()]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p for p in ROOT.rglob("*") if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS)]


def keep(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith(SKIP_PREFIXES) or any(part in "/" + rel for part in SKIP_PARTS):
        return False
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    return path.stat().st_size <= MAX_BYTES


def main() -> int:
    try:
        import yaml
    except ImportError:
        print("pyyaml is required: python -m pip install pyyaml")
        return 2
    try:
        import nbformat
    except ImportError:
        nbformat = None

    problems: list[str] = []
    counts = {"yaml": 0, "json": 0, "notebook": 0, "text": 0}
    files = [p for p in candidate_files() if keep(p)]

    for path in sorted(files):
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        if b"\0" in raw[:8192]:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel}: not valid UTF-8")
            continue
        counts["text"] += 1

        suffix = path.suffix.lower()
        try:
            if suffix in {".yml", ".yaml"}:
                list(yaml.safe_load_all(text))
                counts["yaml"] += 1
            elif suffix == ".ipynb":
                notebook = json.loads(text)
                counts["notebook"] += 1
                if nbformat is not None:
                    nbformat.validate(nbformat.from_dict(notebook))
            elif suffix in {".json", ".platform"}:
                json.loads(text)
                counts["json"] += 1
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{rel}: cannot parse ({exc.__class__.__name__}: {str(exc).splitlines()[0][:140]})")

        for label, rx in TEXT_RULES.items():
            match = rx.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{rel}:{line}: {label}")

    print(f"checked {counts['text']} text files: {counts['yaml']} YAML, {counts['json']} JSON, {counts['notebook']} notebooks")
    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems[:80]:
            print("  " + problem)
        return 1
    print("static checks: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
