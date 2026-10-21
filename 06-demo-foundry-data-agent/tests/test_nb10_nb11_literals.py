from __future__ import annotations

import ast
import csv
import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from b4_fleet_demo.notebook_sync import percent_script_to_notebook_text
from b4_fleet_demo.reference_data import (
    GROUND_TRUTH,
    TABLE_SPECS,
    read_csv_header,
    row_count_map,
)

FABRIC_SETUP_DIR = ROOT / "fabric-setup"
NB10_SOURCE = FABRIC_SETUP_DIR / "nb_10_load_gold_break_glass.py"
NB11_SOURCE = FABRIC_SETUP_DIR / "nb_11_recon_walkthrough.py"

FORBIDDEN_SNIPPETS = (
    "b4_fleet_demo",
    "parents[",
    "Path.cwd",
    "duckdb",
    ".save(",
    "Tables/",
    "DROP TABLE",
    "LOCATION",
)
SCHEMA_DESCRIPTIONS = FABRIC_SETUP_DIR / "schema-descriptions.md"
NB10_REQUIRED_SNIPPETS = (
    'spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")',
    '.mode("overwrite")',
    '.format("delta")',
    '.option("overwriteSchema", "true")',
    ".saveAsTable(",
)


def _module_assignments(source_path: Path) -> dict[str, object]:
    """Parse top-level NAME = <literal> assignments out of a percent-script source file."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    continue
    return values


def _expected_ddl() -> dict[str, str]:
    return {
        spec.fq_name: ", ".join(f"{col.name} {col.spark_type}" for col in spec.columns)
        for spec in TABLE_SPECS
    }


def _expected_sources() -> dict[str, str]:
    return {spec.fq_name: spec.source_name for spec in TABLE_SPECS}


def test_nb10_literals_match_reference_data() -> None:
    values = _module_assignments(NB10_SOURCE)
    assert values["TABLE_DDL"] == _expected_ddl()
    assert values["TABLE_SOURCES"] == _expected_sources()

    expected_rows = row_count_map()
    actual_rows = values["EXPECTED_ROW_COUNTS"]
    for table_name, expected in expected_rows.items():
        assert actual_rows[table_name] == expected, table_name


def _code_only(source_path: Path) -> str:
    """Return the source with markdown/comment lines stripped, so prose explaining what the
    notebook does NOT do (e.g. "no b4_fleet_demo imports") cannot trip the forbidden-snippet
    check below."""
    lines = [line for line in source_path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")]
    return "\n".join(lines)


def test_nb10_has_no_forbidden_dependencies() -> None:
    code = _code_only(NB10_SOURCE)
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in code, snippet


def test_nb10_uses_the_saveastable_pattern() -> None:
    code = _code_only(NB10_SOURCE)
    for snippet in NB10_REQUIRED_SNIPPETS:
        assert snippet in code, snippet


def test_nb10_ddl_columns_match_csv_headers() -> None:
    """The DDL schema is applied by position, so names and order must equal the published CSV header."""
    values = _module_assignments(NB10_SOURCE)
    for spec in TABLE_SPECS:
        ddl_columns = [part.strip().split(" ", 1)[0] for part in values["TABLE_DDL"][spec.fq_name].split(",")]
        assert ddl_columns == read_csv_header(values["TABLE_SOURCES"][spec.fq_name]), spec.fq_name


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


VALUE_CHECKS = {
    "INT": lambda value: re.fullmatch(r"-?\d+", value) is not None,
    "DOUBLE": _is_float,
    "BOOLEAN": lambda value: value.lower() in {"true", "false"},
    "DATE": lambda value: re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None,
}


def test_nb10_ddl_types_can_parse_every_csv_value() -> None:
    """Spark's CSV reader turns a value it cannot parse under the declared type into NULL without
    any error (for example "2.0" in an INT column), so every typed column must hold parseable values."""
    values = _module_assignments(NB10_SOURCE)
    for spec in TABLE_SPECS:
        columns = [part.strip().split(" ", 1) for part in values["TABLE_DDL"][spec.fq_name].split(",")]
        checks = {
            index: (name, VALUE_CHECKS[type_name])
            for index, (name, type_name) in enumerate(columns)
            if type_name in VALUE_CHECKS
        }
        opener = gzip.open if spec.source_path.suffix == ".gz" else open
        unparseable: dict[str, str] = {}
        with opener(spec.source_path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            next(reader)
            for row in reader:
                for index, (name, check) in checks.items():
                    if row[index] != "" and name not in unparseable and not check(row[index]):
                        unparseable[name] = row[index]
        assert not unparseable, f"{spec.fq_name}: first unparseable value per column {unparseable}"


def test_schema_descriptions_types_match_the_table_specs() -> None:
    """The column types in schema-descriptions.md (read by the data agent) must equal the DDL types."""
    documented: dict[str, list[tuple[str, str]]] = {}
    current: list[tuple[str, str]] | None = None
    for line in SCHEMA_DESCRIPTIONS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = documented.setdefault(line[3:].strip(), [])
        elif current is not None:
            match = re.match(r"\| `(\w+)` \| `(\w+)` \|", line)
            if match:
                current.append((match.group(1), match.group(2)))
    for spec in TABLE_SPECS:
        expected = [(column.name, column.spark_type) for column in spec.columns]
        assert documented.get(spec.fq_name) == expected, spec.fq_name


def test_nb11_literals_match_ground_truth() -> None:
    values = _module_assignments(NB11_SOURCE)

    silver = GROUND_TRUTH["silver"]
    expected_tiers = {
        "telematics": dict(silver["telematics"]["by_resolution"]),
        "cmms": dict(silver["cmms"]["by_resolution"]),
    }
    assert values["RESOLUTION_TIERS"] == expected_tiers

    expected_quality = GROUND_TRUTH["truth_checks"]["unreported_failures_found"]
    actual_quality = values["UNREPORTED_FAILURES_FOUND"]
    assert actual_quality == expected_quality


def test_nb11_recon_status_literal_matches_ground_truth() -> None:
    values = _module_assignments(NB11_SOURCE)
    reconciliation = GROUND_TRUTH["reconciliation"]
    expected = {
        status: (reconciliation["recon_status"][status], reconciliation["crit_recon_status"][status])
        for status in ("MATCHED", "UNMATCHED", "PENDING")
    }
    assert values["EXPECTED_RECON_STATUS"] == expected


def test_nb11_has_no_forbidden_dependencies() -> None:
    code = _code_only(NB11_SOURCE)
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in code, snippet


def test_notebooks_are_generated_from_the_percent_scripts() -> None:
    """The .ipynb files are build artefacts: they must equal a fresh generation from the .py files."""
    for source in (NB10_SOURCE, NB11_SOURCE):
        expected = percent_script_to_notebook_text(source).encode("utf-8")
        assert source.with_suffix(".ipynb").read_bytes() == expected, f"regenerate {source.stem}.ipynb"
