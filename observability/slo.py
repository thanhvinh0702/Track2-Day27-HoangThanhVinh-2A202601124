from __future__ import annotations

from typing import Any


def calculate_slo(target: float, bad_events: int, total_events: int) -> dict[str, Any]:
    if not 0 < target < 1:
        raise ValueError("target must be between 0 and 1 (exclusive)")
    if bad_events < 0 or total_events < 0 or bad_events > total_events:
        raise ValueError("invalid event counts")
    allowed_bad_rate = 1.0 - target
    if total_events == 0:
        return {
            "target": target,
            "actual_bad_rate": 0.0,
            "allowed_bad_rate": allowed_bad_rate,
            "burn_rate": 0.0,
            "remaining_error_budget_fraction": 1.0,
            "breached": False,
        }
    actual_bad_rate = bad_events / total_events
    burn_rate = actual_bad_rate / allowed_bad_rate
    consumed_fraction = min(1.0, actual_bad_rate / allowed_bad_rate)
    return {
        "target": target,
        "actual_bad_rate": actual_bad_rate,
        "allowed_bad_rate": allowed_bad_rate,
        "burn_rate": burn_rate,
        "remaining_error_budget_fraction": max(0.0, 1.0 - consumed_fraction),
        "breached": bool(actual_bad_rate > allowed_bad_rate),
    }


def evaluate_multiwindow_burn(
    *,
    short_window_burn: float,
    long_window_burn: float,
    policy: str = "starter",
) -> dict[str, Any]:
    """TODO(student): implement a real multi-window burn-rate policy.

    Starter intentionally never pages. Hidden evaluation contains cases that
    require distinguishing sustained fast burn from a transient spike.
    """
    if min(short_window_burn, long_window_burn) < 0:
        raise ValueError("burn rates cannot be negative")
    fast_sustained = short_window_burn >= 14.4 and long_window_burn >= 2.0
    moderate_sustained = short_window_burn >= 6.0 and long_window_burn >= 1.0
    page = fast_sustained or moderate_sustained
    return {
        "page": page,
        "severity": "critical" if fast_sustained else ("warning" if moderate_sustained else "info"),
        "reason": ("sustained_fast_burn" if fast_sustained else
                   "sustained_moderate_burn" if moderate_sustained else
                   "transient_spike_or_healthy"),
        "short_window_burn": short_window_burn,
        "long_window_burn": long_window_burn,
    }
