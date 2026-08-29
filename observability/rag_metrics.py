from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from observability.anomaly import zscore_detector


def approximate_token_lengths(texts: Iterable[str]) -> list[int]:
    # Deliberately simple proxy; no tokenizer/model download needed.
    return [len(str(t).split()) for t in texts]


def detect_text_length_shift(
    current_texts: Iterable[str],
    baseline_batch_means: Iterable[float],
    *,
    threshold: float = 3.0,
) -> dict[str, Any]:
    lengths = approximate_token_lengths(current_texts)
    current_mean = float(np.mean(lengths)) if lengths else 0.0
    result = zscore_detector(current_mean, baseline_batch_means, threshold=threshold)
    result["metric"] = "mean_text_length"
    result["current_mean"] = current_mean
    return result


def detect_embedding_norm_shift(
    current_norms: Iterable[float], baseline_norms: Iterable[float]
) -> dict[str, Any]:
    """TODO(student): implement embedding-space drift signal.

    No embedding model is required for the starter lab. Hidden evaluation can
    feed precomputed norms/similarities through this stable interface.
    """
    cur = np.asarray(list(current_norms), dtype=float)
    base = np.asarray(list(baseline_norms), dtype=float)
    if cur.size == 0 or base.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "zscore", "reason": "insufficient_history"}
    current = float(np.mean(cur))
    mean = float(np.mean(base))
    std = float(np.std(base))
    score = abs(current - mean) / std if std else (float("inf") if current != mean else 0.0)
    return {"is_anomaly": bool(score > 3.0), "score": float(score),
            "method": "embedding_norm_zscore",
            "reason": f"baseline_mean={mean:.4f}, current_mean={current:.4f}, std={std:.4f}"}
