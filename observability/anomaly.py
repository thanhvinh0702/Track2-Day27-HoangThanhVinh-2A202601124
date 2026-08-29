"""Anomaly detection starter.

Z-score is deliberately the default baseline. Students should improve `auto`
mode for seasonality/outliers rather than deleting the simple implementation.
"""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def zscore_detector(current: float, history: Iterable[float], threshold: float = 3.0) -> dict[str, Any]:
    values = np.asarray(list(history), dtype=float)
    if values.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "zscore", "reason": "insufficient_history"}
    mean = float(np.mean(values))
    std = float(np.std(values))
    if std == 0:
        score = float("inf") if float(current) != mean else 0.0
    else:
        score = abs(float(current) - mean) / std
    return {
        "is_anomaly": bool(score > threshold),
        "score": float(score),
        "method": "zscore",
        "reason": f"mean={mean:.3f}, std={std:.3f}, threshold={threshold}",
    }


def mad_detector(current: float, history: Iterable[float], threshold: float = 3.5) -> dict[str, Any]:
    """Robust example, intentionally incomplete around zero-MAD edge cases.

    Students may improve this function and/or use it from auto mode.
    """
    values = np.asarray(list(history), dtype=float)
    if values.size < 5:
        return {"is_anomaly": False, "score": 0.0, "method": "mad", "reason": "insufficient_history"}
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad == 0:
        score = float("inf") if float(current) != median else 0.0
        return {"is_anomaly": score > threshold, "score": score, "method": "mad",
                "reason": f"median={median:.3f}, mad=0; threshold={threshold}"}
    modified_z = 0.6745 * abs(float(current) - median) / mad
    return {
        "is_anomaly": bool(modified_z > threshold),
        "score": float(modified_z),
        "method": "mad",
        "reason": f"median={median:.3f}, mad={mad:.3f}, threshold={threshold}",
    }


def detect_anomaly(
    current: float,
    history: Iterable[float],
    *,
    method: str = "auto",
    threshold: float = 3.0,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stable lab API.

    Current starter behavior:
    - `zscore`: basic z-score.
    - `mad`: MAD example.
    - `auto`: still uses naive z-score and ignores context.

    TODO(student): make `auto` context-aware. Useful context keys used by the
    instructor may include `day_of_week`, `same_segment_history`,
    `metric_name`, `known_event`, and `trend`.
    """
    values = list(history)
    if method == "mad":
        return mad_detector(current, history)
    if method == "auto":
        context = context or {}
        segment = context.get("same_segment_history")
        baseline = list(segment) if segment is not None and len(segment) >= 3 else values
        if len(baseline) >= 5:
            result = mad_detector(current, baseline, threshold=max(3.5, threshold))
            result["method"] = "auto:mad"
        else:
            result = zscore_detector(current, baseline, threshold=threshold)
            result["method"] = "auto:zscore"
        if context.get("known_event"):
            result["is_anomaly"] = False
            result["reason"] += "; known_event=true"
        elif segment is not None:
            result["reason"] += "; same_segment_baseline=true"
        return result
    if method == "zscore":
        result = zscore_detector(current, history, threshold=threshold)
        return result
    raise ValueError(f"Unsupported method: {method}")
