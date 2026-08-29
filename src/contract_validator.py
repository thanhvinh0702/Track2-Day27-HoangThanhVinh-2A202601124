"""Simple contract validator used as the starter baseline.

The implementation intentionally covers only common deterministic checks.
Students are expected to extend it with:
- stronger type validation/coercion rules,
- freshness checks,
- cross-field/cross-table assertions,
- severity-aware actions (block/quarantine/warn),
- richer observability metadata.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import pandas as pd
import yaml


def _issue(
    check: str,
    *,
    column: str | None,
    severity: str,
    passed: bool,
    details: str,
    action: str | None = None,
) -> dict[str, Any]:
    return {
        "check": check,
        "column": column,
        "severity": severity,
        "passed": bool(passed),
        "details": details,
        "action": action or {"critical": "block", "warning": "quarantine", "info": "warn"}.get(severity, "warn"),
    }


def load_contract(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_dataframe(df: pd.DataFrame, contract: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    columns = contract.get("columns", contract.get("fields", {}))

    for column, rules in columns.items():
        severity = rules.get("severity", "warning")
        required = bool(rules.get("required", False))

        if column not in df.columns:
            if required:
                issues.append(
                    _issue(
                        "required_column",
                        column=column,
                        severity=severity,
                        passed=False,
                        details=f"Missing required column: {column}",
                    )
                )
            continue

        series = df[column]

        declared_type = rules.get("type")
        type_invalid = pd.Series(False, index=series.index)
        if declared_type == "integer":
            numeric = pd.to_numeric(series, errors="coerce")
            type_invalid = numeric.isna() | (numeric % 1 != 0)
        elif declared_type == "number":
            type_invalid = pd.to_numeric(series, errors="coerce").isna()
        elif declared_type == "datetime":
            type_invalid = pd.to_datetime(series, utc=True, errors="coerce").isna()
        elif declared_type == "string":
            type_invalid = series.isna() | series.map(lambda value: not isinstance(value, str))
        if declared_type:
            invalid_count = int(type_invalid.sum())
            issues.append(_issue("type", column=column, severity=severity,
                                 passed=invalid_count == 0,
                                 details=f"type={declared_type}; invalid_count={invalid_count}"))

        if required:
            null_count = int(series.isna().sum())
            issues.append(
                _issue(
                    "not_null",
                    column=column,
                    severity=severity,
                    passed=(null_count == 0),
                    details=f"null_count={null_count}",
                )
            )

        if rules.get("unique"):
            duplicate_count = int(series.duplicated(keep=False).sum())
            issues.append(
                _issue(
                    "unique",
                    column=column,
                    severity=severity,
                    passed=(duplicate_count == 0),
                    details=f"duplicate_rows={duplicate_count}",
                    action=rules.get("action"),
                )
            )

        accepted = rules.get("accepted_values")
        if accepted is not None:
            invalid_mask = series.notna() & ~series.isin(accepted)
            invalid_count = int(invalid_mask.sum())
            issues.append(
                _issue(
                    "accepted_values",
                    column=column,
                    severity=severity,
                    passed=(invalid_count == 0),
                    details=f"invalid_count={invalid_count}; accepted={accepted}",
                    action=rules.get("action"),
                )
            )

        # Starter numeric range support. Type validation is intentionally minimal.
        if "min" in rules or "max" in rules:
            numeric = pd.to_numeric(series, errors="coerce")
            invalid = pd.Series(False, index=series.index)
            if "min" in rules:
                invalid |= numeric < rules["min"]
            if "max" in rules:
                invalid |= numeric > rules["max"]
            invalid_count = int(invalid.fillna(False).sum())
            issues.append(
                _issue(
                    "range",
                    column=column,
                    severity=severity,
                    passed=(invalid_count == 0),
                    details=f"invalid_count={invalid_count}",
                    action=rules.get("action"),
                )
            )

        if "min_length" in rules:
            lengths = series.astype("string").str.len()
            invalid_count = int((lengths < int(rules["min_length"])).fillna(True).sum())
            issues.append(_issue("min_length", column=column, severity=severity,
                                 passed=invalid_count == 0,
                                 details=f"invalid_count={invalid_count}; min_length={rules['min_length']}"))

    freshness = contract.get("freshness") or {}
    freshness_column = freshness.get("column")
    if freshness_column:
        max_delay = float(freshness.get("max_delay_minutes", 0))
        severity = freshness.get("severity", "warning")
        if freshness_column not in df.columns:
            issues.append(_issue("freshness", column=freshness_column, severity=severity,
                                 passed=False, details="freshness column is missing"))
        else:
            timestamps = pd.to_datetime(df[freshness_column], utc=True, errors="coerce")
            latest = timestamps.max()
            if pd.isna(latest):
                issues.append(_issue("freshness", column=freshness_column, severity=severity,
                                     passed=False, details="no valid freshness timestamp"))
            else:
                reference_time = freshness.get("reference_time")
                now = (pd.to_datetime(reference_time, utc=True)
                       if reference_time else pd.Timestamp(datetime.now(timezone.utc)))
                delay = max(0.0, (now - latest).total_seconds() / 60)
                issues.append(_issue("freshness", column=freshness_column, severity=severity,
                                     passed=delay <= max_delay,
                                     details=f"delay_minutes={delay:.2f}; max_delay_minutes={max_delay:g}"))

    return issues


def failed_issues(issues: list[dict[str, Any]], min_severity: str | None = None) -> list[dict[str, Any]]:
    failed = [i for i in issues if not i.get("passed", False)]
    if min_severity is None:
        return failed
    order = {"info": 0, "warning": 1, "critical": 2}
    threshold = order[min_severity]
    return [i for i in failed if order.get(i.get("severity", "warning"), 1) >= threshold]
