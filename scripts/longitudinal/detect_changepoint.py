"""
detect_changepoint.py

Detect the structural change-point in a repo's Gini or delta_AIC time series.
Uses PELT (via ruptures library) if available; falls back to a sliding-window
mean-difference scan.

Usage:
    python detect_changepoint.py --timeline ../../data/longitudinal/my_repo/timeline.csv
    python detect_changepoint.py --timeline ... --metric vuong_z
"""

import csv
import argparse
from pathlib import Path
from datetime import date


def load_series(timeline_path: Path, metric: str) -> tuple[list[date], list[float], list[bool]]:
    dates, values, is_post = [], [], []
    with open(timeline_path) as f:
        for row in csv.DictReader(f):
            if row[metric] == "":
                continue
            dates.append(date.fromisoformat(row["date"]))
            values.append(float(row[metric]))
            is_post.append(row["is_post"].lower() == "true")
    return dates, values, is_post


def pelt_changepoint(values: list[float]) -> int | None:
    try:
        import ruptures as rpt
        signal = [[v] for v in values]
        algo = rpt.Pelt(model="rbf").fit(signal)
        result = algo.predict(pen=3)
        # result is list of breakpoint indices (1-indexed, last = len(signal))
        inner = [i for i in result if 0 < i < len(values)]
        return inner[0] if inner else None
    except ImportError:
        return None


def sliding_window_changepoint(values: list[float], min_window: int = 3) -> int | None:
    n = len(values)
    if n < 2 * min_window:
        return None
    best_idx, best_diff = None, 0.0
    for i in range(min_window, n - min_window + 1):
        left_mean = sum(values[:i]) / i
        right_mean = sum(values[i:]) / (n - i)
        diff = abs(right_mean - left_mean)
        if diff > best_diff:
            best_diff = diff
            best_idx = i
    return best_idx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--metric", default="gini",
                        choices=["gini", "delta_aic", "vuong_z", "entropy_norm"])
    args = parser.parse_args()

    dates, values, is_post = load_series(Path(args.timeline), args.metric)
    if len(values) < 6:
        print(f"Too few data points ({len(values)}) to detect change-point.")
        return

    repo_name = Path(args.timeline).parent.name
    print(f"\nRepo: {repo_name}  metric: {args.metric}  n={len(values)}")

    # Try PELT first, fall back to sliding window
    cp_idx = pelt_changepoint(values)
    method = "PELT"
    if cp_idx is None:
        cp_idx = sliding_window_changepoint(values)
        method = "sliding-window"

    if cp_idx is None:
        print("No change-point detected.")
        return

    cp_date = dates[cp_idx]
    pre_mean = sum(values[:cp_idx]) / cp_idx
    post_mean = sum(values[cp_idx:]) / (len(values) - cp_idx)
    delta = post_mean - pre_mean

    # Find actual adoption date from the is_post flags
    adoption_indices = [i for i, p in enumerate(is_post) if p]
    adoption_date = dates[adoption_indices[0]] if adoption_indices else None

    print(f"Method:         {method}")
    print(f"Change-point:   {cp_date}  (index {cp_idx})")
    if adoption_date:
        lag_days = (cp_date - adoption_date).days
        print(f"Adoption date:  {adoption_date}  (lag: {lag_days:+d} days)")
    print(f"Pre-mean:       {pre_mean:.4f}")
    print(f"Post-mean:      {post_mean:.4f}")
    print(f"Delta:          {delta:+.4f}")

    direction = "ATROPHY" if delta < 0 and args.metric == "gini" else (
                "STRENGTHENED" if delta > 0 and args.metric in ("delta_aic", "vuong_z") else
                f"{'increase' if delta > 0 else 'decrease'}")
    print(f"Interpretation: {direction}")


if __name__ == "__main__":
    main()
