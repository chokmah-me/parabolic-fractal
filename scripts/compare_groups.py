"""
compare_groups.py

Mann-Whitney U tests comparing baseline vs agentic repo fan-in metrics.
Reads summary.csv produced by fit_distributions.py.

Usage:
    python compare_groups.py --summary ../data/summary.csv
"""

import csv
import argparse
import numpy as np
from pathlib import Path


def mannwhitney_u(a: list[float], b: list[float]):
    """Two-sided Mann-Whitney U. Returns (U, p, rank_biserial_r)."""
    na, nb = len(a), len(b)
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    # assign ranks (mid-rank for ties)
    ranks = [0.0] * (na + nb)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        mid = (i + 1 + j) / 2  # mid-rank (1-indexed)
        for k in range(i, j):
            ranks[k] = mid
        i = j
    rank_sum_a = sum(ranks[k] for k in range(na + nb) if combined[k][1] == 0)
    U = rank_sum_a - na * (na + 1) / 2
    # normal approximation (good for n > 8)
    mu = na * nb / 2
    sigma = np.sqrt(na * nb * (na + nb + 1) / 12)
    z = (U - mu) / sigma if sigma > 0 else 0.0
    # two-sided p via normal CDF approximation
    p = 2 * (1 - _norm_cdf(abs(z)))
    r = 1 - 2 * U / (na * nb)  # rank-biserial effect size
    return U, p, r


def _norm_cdf(z: float) -> float:
    """Abramowitz & Stegun approximation for standard normal CDF."""
    t = 1 / (1 + 0.2316419 * abs(z))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937
           + t * (-1.821255978 + t * 1.330274429))))
    cdf = 1 - (1 / np.sqrt(2 * np.pi)) * np.exp(-z * z / 2) * poly
    return cdf if z >= 0 else 1 - cdf


def load(summary_path: Path) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    with open(summary_path) as f:
        for row in csv.DictReader(f):
            groups.setdefault(row["group"], []).append(row)
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="../data/summary.csv")
    args = parser.parse_args()

    groups = load(Path(args.summary))

    if "baseline" not in groups:
        print("No baseline group in summary.csv"); return
    if "agentic" not in groups:
        print("No agentic group yet — populate AGENTIC_REPOS and re-run pipeline."); return

    bl = groups["baseline"]
    ag = groups["agentic"]

    metrics = [
        ("gini",       "Gini coefficient"),
        ("delta_aic",  "Delta AIC (log-normal advantage)"),
        ("frac_leaves","Fraction zero-fanin files"),
        ("entropy_norm","Normalized entropy"),
    ]

    print(f"\nn(baseline)={len(bl)}, n(agentic)={len(ag)}\n")
    print(f"{'Metric':<28} {'BL mean':>9} {'AG mean':>9} {'U':>8} {'p':>8} {'r':>6}")
    print("-" * 72)

    for key, label in metrics:
        a = [float(r[key]) for r in bl]
        b = [float(r[key]) for r in ag]
        U, p, r = mannwhitney_u(a, b)
        sig = "**" if p < 0.01 else ("*" if p < 0.05 else "")
        print(f"{label:<28} {np.mean(a):>9.3f} {np.mean(b):>9.3f} {U:>8.1f} {p:>7.4f}{sig:1s} {r:>6.3f}")

    bl_wins = sum(1 for r in bl if r["lognormal_wins"] == "True")
    ag_wins = sum(1 for r in ag if r["lognormal_wins"] == "True")
    print(f"\nLog-normal wins: baseline {bl_wins}/{len(bl)}, agentic {ag_wins}/{len(ag)}")


if __name__ == "__main__":
    main()
