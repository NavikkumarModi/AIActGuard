from __future__ import annotations


def bin_index(confidence: float, n_bins: int = 10) -> int:
    """Bucket a `classifier_confidence` value (0-1) into one of `n_bins`
    equal-width bins, clamped to a valid index at either edge."""
    idx = int(confidence * n_bins)
    return max(0, min(n_bins - 1, idx))
