"""
fit_distributions.py

For each repo JSON (from compute_fanin.py), fit log-normal vs. power-law to the
fan-in distribution. Compute Gini coefficient, entropy, and AIC/BIC for both fits.
Output: summary CSV + per-repo JSON.

Usage:
    python fit_distributions.py --results-dir ../data/results --out ../data/summary.csv
"""

import json
import csv
import argparse
import numpy as np
from pathlib import Path


def gini(values: np.ndarray) -> float:
    """Gini coefficient of an array of non-negative values."""
    v = np.sort(values.astype(float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * v) / (n * v.sum())) - (n + 1) / n


def entropy_norm(values: np.ndarray) -> float:
    """Normalized Shannon entropy (0=uniform, 1=concentrated on one item)."""
    v = values[values > 0].astype(float)
    if len(v) == 0:
        return 0.0
    p = v / v.sum()
    h = -np.sum(p * np.log(p + 1e-12))
    h_max = np.log(len(v))
    return h / h_max if h_max > 0 else 0.0


def fit_powerlaw_ols(log_rank: np.ndarray, log_val: np.ndarray):
    """Fit log(val) = a + b*log(rank) via OLS. Returns (a, b, r2, aic, bic, residuals)."""
    A = np.column_stack([np.ones_like(log_rank), log_rank])
    result = np.linalg.lstsq(A, log_val, rcond=None)
    coeffs = result[0]
    residuals = log_val - (coeffs[0] + coeffs[1] * log_rank)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((log_val - log_val.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    n = len(log_val)
    k = 2
    aic = n * np.log(ss_res / n + 1e-12) + 2 * k
    bic = n * np.log(ss_res / n + 1e-12) + k * np.log(n)
    return coeffs[0], coeffs[1], r2, aic, bic, residuals


def fit_lognormal_ols(log_rank: np.ndarray, log_val: np.ndarray):
    """Fit log(val) = a + b*log(rank) + c*log(rank)^2 via OLS (parabolic). Returns (coeffs, r2, aic, bic, residuals)."""
    A = np.column_stack([np.ones_like(log_rank), log_rank, log_rank ** 2])
    result = np.linalg.lstsq(A, log_val, rcond=None)
    coeffs = result[0]
    residuals = log_val - (coeffs[0] + coeffs[1] * log_rank + coeffs[2] * log_rank ** 2)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((log_val - log_val.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    n = len(log_val)
    k = 3
    aic = n * np.log(ss_res / n + 1e-12) + 2 * k
    bic = n * np.log(ss_res / n + 1e-12) + k * np.log(n)
    return coeffs, r2, aic, bic, residuals


def vuong_z(res_pl: np.ndarray, res_ln: np.ndarray) -> tuple[float, float]:
    """Vuong's closeness test (Gaussian log-likelihoods in log-log space).

    Computes per-observation log-likelihood ratio LR_i = ll_LN_i - ll_PL_i.
    Returns (z, p_two_sided). z > 0 favors log-normal.
    """
    n = len(res_pl)
    sigma2_pl = np.sum(res_pl ** 2) / n
    sigma2_ln = np.sum(res_ln ** 2) / n
    # per-observation log-likelihood under each Gaussian model
    ll_pl = -0.5 * (res_pl ** 2 / (sigma2_pl + 1e-30)) - 0.5 * np.log(2 * np.pi * (sigma2_pl + 1e-30))
    ll_ln = -0.5 * (res_ln ** 2 / (sigma2_ln + 1e-30)) - 0.5 * np.log(2 * np.pi * (sigma2_ln + 1e-30))
    lr = ll_ln - ll_pl
    z = np.sqrt(n) * lr.mean() / (lr.std(ddof=1) + 1e-30)
    # two-sided p via normal approximation
    p = 2 * (1 - _norm_cdf(abs(z)))
    return float(z), float(p)


def _norm_cdf(z: float) -> float:
    t = 1 / (1 + 0.2316419 * abs(z))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937
           + t * (-1.821255978 + t * 1.330274429))))
    cdf = 1 - (1 / np.sqrt(2 * np.pi)) * np.exp(-z * z / 2) * poly
    return cdf if z >= 0 else 1 - cdf


def metrics_from_fanin(fanin_dict: dict, repo_name: str, group: str) -> dict | None:
    """Compute distribution metrics from a fanin dict {filepath: count}.
    Callable directly (e.g. from longitudinal pipeline) without touching disk.
    """
    fanin = np.array(list(fanin_dict.values()), dtype=float)
    fanin_all = fanin.copy()
    fanin_pos = fanin[fanin > 0]

    if len(fanin_pos) < 10:
        return None

    sorted_vals = np.sort(fanin_pos)[::-1]
    ranks = np.arange(1, len(sorted_vals) + 1)
    log_rank = np.log(ranks)
    log_val = np.log(sorted_vals + 1e-9)

    a_pl, b_pl, r2_pl, aic_pl, bic_pl, res_pl = fit_powerlaw_ols(log_rank, log_val)
    coeffs_ln, r2_ln, aic_ln, bic_ln, res_ln = fit_lognormal_ols(log_rank, log_val)

    delta_aic = aic_pl - aic_ln
    vuong_z_stat, vuong_p_val = vuong_z(res_pl, res_ln)

    return {
        "repo": repo_name,
        "group": group,
        "n_files": len(fanin_all),
        "n_files_pos_fanin": len(fanin_pos),
        "frac_leaves": float(np.mean(fanin_all == 0)),
        "max_fanin": float(fanin_all.max()),
        "mean_fanin": float(fanin_all.mean()),
        "gini": float(gini(fanin_all)),
        "entropy_norm": float(entropy_norm(fanin_all)),
        "r2_powerlaw": float(r2_pl),
        "r2_lognormal": float(r2_ln),
        "aic_powerlaw": float(aic_pl),
        "aic_lognormal": float(aic_ln),
        "bic_powerlaw": float(bic_pl),
        "bic_lognormal": float(bic_ln),
        "delta_aic": float(delta_aic),
        "lognormal_wins": delta_aic > 2,
        "vuong_z": float(vuong_z_stat),
        "vuong_p": float(vuong_p_val),
        "lognormal_coeff_c": float(coeffs_ln[2]),
    }


def analyze_repo(json_path: Path, group: str) -> dict | None:
    data = json.loads(json_path.read_text())
    return metrics_from_fanin(data, json_path.stem, group)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--out", default="../data/summary.csv")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    rows = []

    for group_dir in sorted(results_dir.iterdir()):
        if not group_dir.is_dir():
            continue
        group = group_dir.name
        for json_file in sorted(group_dir.glob("*.json")):
            row = analyze_repo(json_file, group)
            if row:
                rows.append(row)
                lnw = "YES" if row["lognormal_wins"] else "no"
                print(f"  {group}/{row['repo']}: gini={row['gini']:.3f}  delta_aic={row['delta_aic']:+.1f}  vuong_z={row['vuong_z']:+.2f}  ln_wins={lnw}")

    if not rows:
        print("No results found.")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nSummary written to {out_path} ({len(rows)} repos)")

    # Quick group summary
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)

    print("\nGroup summary:")
    for g, rs in groups.items():
        ginis = [r["gini"] for r in rs]
        ln_wins = sum(1 for r in rs if r["lognormal_wins"])
        print(f"  {g}: n={len(rs)}  gini_mean={np.mean(ginis):.3f}±{np.std(ginis):.3f}  "
              f"log-normal wins={ln_wins}/{len(rs)}")


if __name__ == "__main__":
    main()
