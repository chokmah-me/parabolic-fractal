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
from scipy.stats import mannwhitneyu
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
    parser.add_argument("--exclude-repos", default="",
                         help="Comma-separated repo names to drop before comparing "
                              "(e.g. repos flagged in data/contamination-baseline.csv)")
    parser.add_argument("--out", default="",
                         help="Optional path to also write results as CSV "
                              "(p = normal approximation, p_exact = exact test)")
    args = parser.parse_args()

    groups = load(Path(args.summary))
    excluded = {r.strip() for r in args.exclude_repos.split(",") if r.strip()}

    if "baseline" not in groups:
        print("No baseline group in summary.csv"); return
    if "agentic" not in groups:
        print("No agentic group yet — populate AGENTIC_REPOS and re-run pipeline."); return

    bl = [r for r in groups["baseline"] if r["repo"] not in excluded]
    ag = [r for r in groups["agentic"] if r["repo"] not in excluded]
    if excluded:
        dropped = sorted(excluded)
        print(f"Excluding {len(dropped)} repo(s): {', '.join(dropped)}\n")

    metrics = [
        ("gini",       "Gini coefficient"),
        ("delta_aic",  "Delta AIC (log-normal advantage)"),
        ("frac_leaves","Fraction zero-fanin files"),
        ("entropy_norm","Normalized entropy"),
        ("vuong_z",    "z_lr (log-normal preference)"),
    ]

    print(f"\nn(baseline)={len(bl)}, n(agentic)={len(ag)}\n")
    print(f"{'Metric':<28} {'BL mean':>9} {'AG mean':>9} {'U':>8} {'p':>8} {'r':>6}")
    print("-" * 72)

    out_rows = []
    for key, label in metrics:
        a = [float(r[key]) for r in bl]
        b = [float(r[key]) for r in ag]
        U, p, r = mannwhitney_u(a, b)
        sig = "**" if p < 0.01 else ("*" if p < 0.05 else "")
        print(f"{label:<28} {np.mean(a):>9.3f} {np.mean(b):>9.3f} {U:>8.1f} {p:>7.4f}{sig:1s} {r:>6.3f}")
        out_rows.append({
            "metric": key, "bl_mean": np.mean(a), "ag_mean": np.mean(b),
            "U": U, "p": p, "p_exact": mannwhitneyu(a, b, alternative="two-sided", method="exact").pvalue, "r": r,
            "n_baseline": len(bl), "n_agentic": len(ag),
            "excluded_repos": ";".join(sorted(excluded)),
        })

    bl_wins = sum(1 for r in bl if r["lognormal_wins"] == "True")
    ag_wins = sum(1 for r in ag if r["lognormal_wins"] == "True")
    print(f"\nLog-normal wins: baseline {bl_wins}/{len(bl)}, agentic {ag_wins}/{len(ag)}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["metric", "bl_mean", "ag_mean", "U", "p", "p_exact", "r",
                  "n_baseline", "n_agentic", "excluded_repos"]
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
