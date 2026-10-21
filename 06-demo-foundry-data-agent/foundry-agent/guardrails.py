from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {
    "gold.dim_asset",
    "gold.dim_site",
    "gold.fact_fault_episode",
    "gold.fact_recon_exception",
    "gold.fact_recon_match",
    "gold.fact_telemetry_daily",
    "gold.fact_work_order",
    "gold.agg_recon_monthly",
    "ml.asset_day_features",
    "ml.failure_risk_score",
    "ml.drift_report",
}


@dataclass(frozen=True)
class GuardrailResult:
    approved: bool
    sanitized_sql: str
    reason: str | None = None


class GuardrailViolation(ValueError):
    pass


def _normalize_table(table: exp.Table) -> str:
    parts = [part for part in (table.db, table.name) if part]
    return ".".join(parts)


def _has_comments(sql_text: str) -> bool:
    return "--" in sql_text or "/*" in sql_text or "*/" in sql_text


def _is_select_like(expression: exp.Expression) -> bool:
    return isinstance(expression, (exp.Select, exp.Union, exp.With, exp.Subquery, exp.CTE))


def _final_query(expression: exp.Expression) -> exp.Expression:
    current = expression
    while isinstance(current, exp.With):
        current = current.this
    return current


def enforce_readonly_sql(
    sql_text: str,
    *,
    allowed_tables: Iterable[str] = ALLOWED_TABLES,
    max_rows: int = 200,
) -> GuardrailResult:
    if not sql_text.strip():
        raise GuardrailViolation("SQL is empty.")
    if _has_comments(sql_text):
        raise GuardrailViolation("SQL comments are not allowed.")

    parsed = sqlglot.parse(sql_text, read="tsql")
    if len(parsed) != 1:
        raise GuardrailViolation("Exactly one SQL statement is allowed.")

    expression = parsed[0]
    final_query = _final_query(expression)
    if not isinstance(final_query, (exp.Select, exp.Union)):
        raise GuardrailViolation("Only SELECT statements are allowed.")

    for node in expression.walk():
        if isinstance(node, (exp.Delete, exp.Insert, exp.Update, exp.Drop, exp.Alter, exp.Create, exp.Command)):
            raise GuardrailViolation(f"Disallowed statement: {node.key}.")
        if isinstance(node, exp.Table):
            normalized = _normalize_table(node)
            if normalized and normalized not in set(allowed_tables):
                raise GuardrailViolation(f"Table not allowed: {normalized}.")

    limited = expression.copy()
    select_nodes = list(limited.find_all(exp.Select))
    if select_nodes:
        top_level = select_nodes[-1]
        current_limit = top_level.args.get("limit")
        if current_limit is None:
            top_level.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
        else:
            try:
                current_value = int(re.sub(r"[^0-9]", "", current_limit.sql()))
            except ValueError as exc:
                raise GuardrailViolation("Unable to parse LIMIT/TOP value.") from exc
            if current_value > max_rows:
                top_level.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))

    sanitized = limited.sql(dialect="tsql")
    return GuardrailResult(approved=True, sanitized_sql=sanitized)
