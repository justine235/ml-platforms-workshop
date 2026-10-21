#!/usr/bin/env python3
"""Static checker for the Fabric Git folders of the workshop kit.

Needs no network, no Fabric workspace and no third-party package (Python 3.8+).

    python check_fabric_git.py            # check every fabric-git folder under 04-demo-fabric-e2e
    python check_fabric_git.py --list     # also print the item / logicalId table

What it proves: the files have the structure Fabric Git integration expects and the
cross references (pipeline -> notebook logicalId) are consistent.
What it cannot prove: that a real workspace accepts them. Sync them into a scratch
workspace before Friday (see VERIFY-BEFORE-FRIDAY.md).

Reference structure: public sample workspace of microsoft/fabric-cicd
(sample/workspace: Hello World.Notebook, Run Hello World.DataPipeline, Vars.VariableLibrary)
and the Microsoft Learn page "Notebook source control and deployment".
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PLATFORM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
ZERO_GUID = "00000000-0000-0000-0000-000000000000"
GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MARKER_RE = re.compile(r"^# (CELL|MARKDOWN|METADATA) \*{20}$")
PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]{3,}__")
ALLOWED_PLACEHOLDERS = {"__OFFICE365_CONNECTION_ID__", "__ALERT_TO__"}
ITEM_TYPES = {"Notebook", "DataPipeline", "VariableLibrary"}
DEPENDENCY_CONDITIONS = {"Succeeded", "Failed", "Completed", "Skipped"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append("ERROR  %s: %s" % (where, message))

    def warn(self, where: str, message: str) -> None:
        self.warnings.append("WARN   %s: %s" % (where, message))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(KIT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path, report: Report):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        report.error(rel(path), "UTF-8 BOM (write UTF-8 without BOM)")
    if b"\r" in raw:
        report.error(rel(path), "CRLF line endings (write with newline='\\n')")
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError) as exc:
        report.error(rel(path), "invalid JSON: %s" % exc)
        return None


def check_platform(item_dir: Path, item_type: str, report: Report):
    path = item_dir / ".platform"
    if not path.exists():
        report.error(rel(item_dir), "missing .platform")
        return None
    data = load_json(path, report)
    if not isinstance(data, dict):
        return None
    where = rel(path)
    extra = set(data) - {"$schema", "metadata", "config"}
    if extra:
        report.error(where, "unexpected top-level keys %s (real files have $schema, metadata, config only)" % sorted(extra))
    if data.get("$schema") != PLATFORM_SCHEMA:
        report.error(where, "$schema must be %s" % PLATFORM_SCHEMA)
    metadata = data.get("metadata") or {}
    config = data.get("config") or {}
    if metadata.get("type") != item_type:
        report.error(where, "metadata.type is %r, folder suffix says %r" % (metadata.get("type"), item_type))
    stem = item_dir.name[: -(len(item_type) + 1)]
    if metadata.get("displayName") != stem:
        report.error(where, "metadata.displayName %r must equal the folder name stem %r" % (metadata.get("displayName"), stem))
    if "description" in metadata and not isinstance(metadata["description"], str):
        report.error(where, "metadata.description must be a string")
    if config.get("version") != "2.0":
        report.error(where, 'config.version must be "2.0" (it lives inside config, not at the top level)')
    logical_id = config.get("logicalId")
    if not isinstance(logical_id, str) or not GUID_RE.match(logical_id):
        report.error(where, "config.logicalId must be a lowercase GUID, got %r" % (logical_id,))
        return None
    return logical_id


def parse_meta(lines: list[str]):
    body = [line for line in lines if line.strip()]
    if not body or not all(line.startswith("# META") for line in body):
        return None
    text = "\n".join(line[len("# META"):].lstrip(" ") if line != "# META" else "" for line in body)
    try:
        return json.loads(text)
    except ValueError:
        return None


def check_notebook(item_dir: Path, report: Report) -> None:
    path = item_dir / "notebook-content.py"
    where = rel(path)
    if not path.exists():
        report.error(rel(item_dir), "missing notebook-content.py")
        return
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        report.error(where, "UTF-8 BOM")
    if b"\r" in raw:
        report.error(where, "CRLF line endings (write with newline='\\n')")
    lines = raw.decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    if lines[0] != "# Fabric notebook source":
        report.error(where, "first line must be '# Fabric notebook source' (this looks like a plain percent-format .py file)")
        return
    if any(line.startswith("# %%") for line in lines):
        report.error(where, "percent-format cell markers ('# %%') found; Fabric uses '# CELL ********************'")
    sections: list[list] = []
    current = None
    for number, line in enumerate(lines, start=1):
        match = MARKER_RE.match(line)
        if match:
            current = [match.group(1), number, []]
            sections.append(current)
        elif current is not None:
            current[2].append(line)
        elif number > 1 and line.strip():
            report.error(where, "line %d: content before the first marker" % number)
    if not sections or sections[0][0] != "METADATA":
        report.error(where, "the first section must be the notebook-level '# METADATA ********************' block")
        return
    notebook_meta = parse_meta(sections[0][2])
    if not isinstance(notebook_meta, dict):
        report.error(where, "notebook-level META block is not valid JSON")
    else:
        kernel = (notebook_meta.get("kernel_info") or {}).get("name")
        if not kernel:
            report.error(where, "notebook META needs kernel_info.name (e.g. synapse_pyspark)")
        if "dependencies" not in notebook_meta:
            report.error(where, "notebook META needs a dependencies object (may be empty)")
    code_cells = 0
    for index, (kind, number, body) in enumerate(sections):
        if index == 0:
            continue
        if kind == "METADATA":
            previous = sections[index - 1][0]
            if previous != "CELL":
                report.error(where, "line %d: METADATA block must directly follow a CELL" % number)
                continue
            meta = parse_meta(body)
            if not isinstance(meta, dict) or "language" not in meta or "language_group" not in meta:
                report.error(where, "line %d: cell META must be JSON with language and language_group" % number)
            elif "tags" in meta and not (isinstance(meta["tags"], list) and all(isinstance(tag, str) for tag in meta["tags"])):
                report.error(where, "line %d: cell META tags must be a list of strings" % number)
        elif kind == "MARKDOWN":
            for offset, line in enumerate(body):
                if line.strip() and not line.startswith("#"):
                    report.error(where, "line %d: markdown line must start with '# '" % (number + 1 + offset))
                    break
        elif kind == "CELL":
            code_cells += 1
            nxt = sections[index + 1][0] if index + 1 < len(sections) else None
            if nxt != "METADATA":
                report.error(where, "line %d: every CELL must be followed by its METADATA block" % number)
            code = "\n".join(body)
            first = next((line for line in body if line.strip()), "")
            if not first.startswith(("%", "!")):
                try:
                    ast.parse(code)
                except SyntaxError as exc:
                    report.error(where, "line %d: code cell does not parse (%s, cell line %s)" % (number, exc.msg, exc.lineno))
    if code_cells == 0:
        report.error(where, "no code cell")


def scope_activities(activities, where: str, report: Report, names: dict, notebook_ids: set, notebook_refs: set) -> None:
    local = [a.get("name") for a in activities if isinstance(a, dict)]
    for activity in activities:
        if not isinstance(activity, dict):
            report.error(where, "activity is not an object")
            continue
        name = activity.get("name")
        kind = activity.get("type")
        if not name or not kind:
            report.error(where, "activity needs name and type: %r" % (name,))
            continue
        if name in names:
            report.error(where, "duplicate activity name %r" % name)
        names[name] = kind
        for dep in activity.get("dependsOn", []) or []:
            if dep.get("activity") not in local:
                report.error(where, "%s dependsOn unknown activity %r (same-scope siblings only)" % (name, dep.get("activity")))
            for condition in dep.get("dependencyConditions", []) or []:
                if condition not in DEPENDENCY_CONDITIONS:
                    report.error(where, "%s has unknown dependency condition %r" % (name, condition))
        props = activity.get("typeProperties") or {}
        if kind == "TridentNotebook":
            notebook_id = props.get("notebookId")
            notebook_refs.add(notebook_id)
            if notebook_id not in notebook_ids:
                report.error(where, "%s: notebookId %r is not the logicalId of any notebook in the kit" % (name, notebook_id))
            if props.get("workspaceId") != ZERO_GUID:
                report.error(where, "%s: workspaceId must be %s (same workspace)" % (name, ZERO_GUID))
        if kind == "IfCondition":
            expression = props.get("expression") or {}
            if not expression.get("value"):
                report.error(where, "%s: IfCondition needs typeProperties.expression.value" % name)
            for branch in ("ifTrueActivities", "ifFalseActivities"):
                nested = props.get(branch)
                if nested:
                    scope_activities(nested, where, report, names, notebook_ids, notebook_refs)
        for branch in ("activities", "defaultActivities"):
            if kind in {"ForEach", "Until", "Switch"} and props.get(branch):
                scope_activities(props[branch], where, report, names, notebook_ids, notebook_refs)


def check_pipeline(item_dir: Path, notebook_ids: set, notebook_refs: set, report: Report) -> None:
    path = item_dir / "pipeline-content.json"
    where = rel(path)
    if not path.exists():
        report.error(rel(item_dir), "missing pipeline-content.json")
        return
    data = load_json(path, report)
    if not isinstance(data, dict):
        return
    activities = (data.get("properties") or {}).get("activities")
    if not isinstance(activities, list) or not activities:
        report.error(where, "properties.activities must be a non-empty list")
        return
    scope_activities(activities, where, report, {}, notebook_ids, notebook_refs)
    text = path.read_text(encoding="utf-8")
    for token in sorted(set(PLACEHOLDER_RE.findall(text))):
        if token not in ALLOWED_PLACEHOLDERS:
            report.error(where, "unresolved placeholder %s (only %s may stay)" % (token, sorted(ALLOWED_PLACEHOLDERS)))
    description = (data.get("properties") or {}).get("description", "")
    if re.search(r"replace .*(guid|id)", description, re.I):
        report.warn(where, "description still tells the user to replace IDs; adapt it to the logicalId convention")


def check_variable_library(item_dir: Path, report: Report) -> None:
    variables = load_json(item_dir / "variables.json", report) if (item_dir / "variables.json").exists() else None
    settings = load_json(item_dir / "settings.json", report) if (item_dir / "settings.json").exists() else None
    where = rel(item_dir)
    if variables is None or settings is None:
        report.error(where, "variables.json and settings.json are both required")
        return
    names = []
    for entry in variables.get("variables", []):
        if not {"name", "type", "value"} <= set(entry):
            report.error(where, "variable needs name, type, value: %r" % entry)
        names.append(entry.get("name"))
    if len(set(names)) != len(names):
        report.error(where, "duplicate variable names")
    order = settings.get("valueSetsOrder", [])
    for value_set in order:
        path = item_dir / "valueSets" / ("%s.json" % value_set)
        if not path.exists():
            report.error(where, "valueSetsOrder lists %r but valueSets/%s.json is missing" % (value_set, value_set))
            continue
        data = load_json(path, report)
        if not isinstance(data, dict):
            continue
        if data.get("name") != value_set:
            report.error(rel(path), "name must equal the file stem %r" % value_set)
        for override in data.get("variableOverrides", []):
            if override.get("name") not in names:
                report.error(rel(path), "override for unknown variable %r" % override.get("name"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--list", action="store_true", help="print the item / logicalId table")
    parser.add_argument("--root", type=Path, default=KIT, help="folder to scan for fabric-git directories")
    args = parser.parse_args()

    report = Report()
    roots = sorted(path for path in args.root.rglob("fabric-git") if path.is_dir())
    if not roots:
        print("No fabric-git folder found under %s" % args.root)
        return 1

    items = []
    for root in roots:
        for item_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            item_type = item_dir.suffix.lstrip(".")
            if item_type not in ITEM_TYPES:
                report.warn(rel(item_dir), "folder is not a recognised item type (%s)" % ", ".join(sorted(ITEM_TYPES)))
                continue
            logical_id = check_platform(item_dir, item_type, report)
            items.append((root, item_dir, item_type, logical_id))

    seen_ids: dict[str, str] = {}
    seen_names: dict[tuple, str] = {}
    for root, item_dir, item_type, logical_id in items:
        if logical_id:
            if logical_id in seen_ids:
                report.error(rel(item_dir), "logicalId %s already used by %s" % (logical_id, seen_ids[logical_id]))
            seen_ids[logical_id] = rel(item_dir)
        key = (item_type, item_dir.name)
        if key in seen_names:
            report.error(rel(item_dir), "same item also defined in %s (both folders sync into one workspace)" % seen_names[key])
        seen_names[key] = rel(item_dir)

    notebook_ids = {logical_id for _, _, item_type, logical_id in items if item_type == "Notebook" and logical_id}
    notebook_refs: set = set()
    for _, item_dir, item_type, _ in items:
        if item_type == "Notebook":
            check_notebook(item_dir, report)
        elif item_type == "DataPipeline":
            check_pipeline(item_dir, notebook_ids, notebook_refs, report)
        elif item_type == "VariableLibrary":
            check_variable_library(item_dir, report)

    unreferenced = sorted(item_dir.name for _, item_dir, item_type, logical_id in items if item_type == "Notebook" and logical_id not in notebook_refs)
    if unreferenced:
        report.warn("kit", "notebooks not called by any pipeline (fine for interactive-only ones): %s" % ", ".join(unreferenced))

    if args.list:
        print("%-12s %-36s %s" % ("type", "item", "logicalId"))
        for _, item_dir, item_type, logical_id in items:
            print("%-12s %-36s %s" % (item_type, item_dir.name[: -(len(item_type) + 1)], logical_id))
        print()

    for line in report.errors + report.warnings:
        print(line)
    print("%d fabric-git folder(s), %d item(s), %d error(s), %d warning(s)" % (len(roots), len(items), len(report.errors), len(report.warnings)))
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
