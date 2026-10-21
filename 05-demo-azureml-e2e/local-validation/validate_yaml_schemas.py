#!/usr/bin/env python3
"""Validate the Azure ML CLI v2 YAML files of this demo against the public JSON schemas.

This is the SECONDARY check. The authoritative one is `validate_with_sdk_loaders.py`, which loads every
file with the real azure-ai-ml SDK (the code behind `az ml`). The published JSON schemas lag the SDK/CLI,
so this script has known false positives (for example a schedule flagged for a root `create_job` key, or
capitalised weekday names) and it cannot see wrong key placement that the SDK loaders do reject.

Why keep it: `yaml.safe_load` only proves the files are YAML. The Azure ML CLI rejects unknown or
mistyped keys, so this script checks each file against the schema named in its own
`$schema:` first line (the same schemas the VS Code Azure ML extension uses).

    python validate_yaml_schemas.py            # needs: pip install pyyaml jsonschema requests
    python validate_yaml_schemas.py --offline  # re-use schemas cached by a previous run

Limits, stated honestly:
* The schemas are public and they move: a new CLI release can add keys that an old cached
  schema rejects. Re-run it online on the day you rehearse.
* `${{...}}` expressions and `azureml:` references are free text for the schema, so the
  asset names and versions are NOT checked here (that is what the dry run in your workspace does).
* Files whose `$schema` is not an https URL (for example the preview schedule for model
  monitoring) are listed as SKIPPED, not as passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(tempfile.gettempdir()) / "aml-yaml-schemas"


def load_schema(url: str, offline: bool):
    import requests

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest()[:12] + ".json")
    if cached.exists() and offline:
        return json.loads(cached.read_text(encoding="utf-8"))
    if offline:
        raise RuntimeError(f"schema {url} is not cached; run once without --offline")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    cached.write_text(response.text, encoding="utf-8")
    return response.json()


def first_schema_line(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("$schema:"):
            return line.split(":", 1)[1].strip()
        if line.strip() and not line.startswith("#"):
            break
    return None


def describe(error) -> str:
    where = "/".join(str(part) for part in error.absolute_path) or "(root)"
    return f"{where}: {error.message.splitlines()[0][:220]}"


def best_errors(validator, instance):
    # The CLI schemas wrap everything in anyOf/oneOf, so report the deepest, most specific errors.
    errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.absolute_path))
    flat = []
    for error in errors:
        stack = [error]
        while stack:
            current = stack.pop()
            if current.context:
                stack.extend(current.context)
            else:
                flat.append(current)
    return flat or errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--offline", action="store_true", help="use cached schemas only")
    parser.add_argument("--verbose", action="store_true", help="print every error, not the first 8 per file")
    args = parser.parse_args()

    import jsonschema
    import yaml

    files = sorted(path for path in DEMO_DIR.rglob("*") if path.suffix in {".yml", ".yaml"} and "out" not in path.parts)
    schema_cache: dict = {}
    failed = skipped = passed = 0
    for path in files:
        label = str(path.relative_to(DEMO_DIR)).replace("\\", "/")
        url = first_schema_line(path)
        if not url:
            continue
        if not url.startswith("https://"):
            print(f"SKIPPED  {label:<52} $schema {url} is not a public URL (check by hand)")
            skipped += 1
            continue
        try:
            if url not in schema_cache:
                schema_cache[url] = load_schema(url, args.offline)
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - network or YAML problems are reported, not hidden
            print(f"ERROR    {label:<52} {exc}")
            failed += 1
            continue
        validator = jsonschema.Draft7Validator(schema_cache[url])
        errors = best_errors(validator, document)
        schema_name = url.rsplit("/", 1)[-1]
        if not errors:
            print(f"OK       {label:<52} {schema_name}")
            passed += 1
            continue
        failed += 1
        print(f"FAIL     {label:<52} {schema_name}")
        shown = errors if args.verbose else errors[:8]
        for error in shown:
            print("           - " + describe(error))
        if len(errors) > len(shown):
            print(f"           ... {len(errors) - len(shown)} more (use --verbose)")

    print(f"\n{passed} ok, {failed} failed, {skipped} skipped, {passed + failed + skipped} files with a $schema line")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
