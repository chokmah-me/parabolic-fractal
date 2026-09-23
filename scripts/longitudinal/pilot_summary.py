"""
pilot_summary.py

Summarize the longitudinal pilot across repos (paper v1.1, Sections 5-6).

Per repo (Gini): last-k pre-adoption mean vs first-k post-adoption mean,
k = min(6, pre, post); paired Wilcoxon signed-rank on those k pairs when
k = 6 (the v1.0.0 rule); pre-period trend; change-point date and lag for
Gini, delta_aic and vuong_z. Change-points use the sliding-window
mean-difference scan from detect_changepoint.py explicitly (not PELT), so
results do not change if the optional `ruptures` package is installed.
Across repos: exact two-sided Wilcoxon signed-rank on the per-repo D.

Usage:
    python scripts/longitudinal/pilot_summary.py [--dir data/longitudinal-v1.1]
"""

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from detect_changepoint import load_series, sliding_window_changepoint

REPOS = ["celery", "numpy", "pandas", "pytest", "fastapi", "scrapy", "django", "pydantic"]
METRICS = ["gini", "delta_aic", "vuong_z"]


def changepoint(timeline: Path, metric: str):
    dates, values, is_post = load_series(timeline, metric)
    idx = sliding_window_changepoint(values)
    if idx is None:
        return None
    first_post = dates[is_post.index(True)]
    pre, post = np.mean(values[:idx]), np.mean(values[idx:])
    return {"cp_date": dates[idx].isoformat(), "lag_days": (dates[idx] - first_post).days,
            "cp_delta": post - pre}


def summarize(timeline: Path) -> dict:
    dates, gini, is_post = load_series(timeline, "gini")
    pre = [g for g, p in zip(gini, is_post) if not p]
    post = [g for g, p in zip(gini, is_post) if p]
    k = min(6, len(pre), len(post))
    last_pre, first_post = pre[-k:], post[:k]
    d = float(np.mean(first_post) - np.mean(last_pre))
    wp = wilcoxon(first_post, last_pre, alternative="two-sided", method="exact").pvalue if k == 6 else None
    slope = float(np.polyfit(np.arange(len(pre)), pre, 1)[0]) if len(pre) >= 3 else float("nan")
    row = {
        "repo": timeline.parent.name,
        "adoption_first_post_snapshot": dates[is_post.index(True)].isoformat(),
        "n_pre": len(pre), "n_post": len(post), "k": k,
        "pre_min": min(pre), "pre_max": max(pre), "post_min": min(post), "post_max": max(post),
        "last_k_pre": float(np.mean(last_pre)), "first_k_post": float(np.mean(first_post)),
        "D": d, "wilcoxon_p": wp,
        "pre_trend_per_month": slope,
        "D_minus_trend": d - slope * k,
    }
    for m in ("delta_aic", "vuong_z"):
        _, vals, post_flags = load_series(timeline, m)
        pre_m = [v for v, q in zip(vals, post_flags) if not q][-k:]
        post_m = [v for v, q in zip(vals, post_flags) if q][:k]
        row[f"D_{m}"] = float(np.mean(post_m) - np.mean(pre_m))
    for m in METRICS:
        cp = changepoint(timeline, m)
        row[f"cp_{m}"] = cp["cp_date"] if cp else ""
        row[f"lag_{m}"] = cp["lag_days"] if cp else ""
        row[f"cpdelta_{m}"] = cp["cp_delta"] if cp else ""
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path(__file__).parent.parent.parent / "data" / "longitudinal-v1.1"))
    args = ap.parse_args()
    base = Path(args.dir)

    rows = [summarize(base / r / "timeline.csv") for r in REPOS if (base / r / "timeline.csv").exists()]
    missing = [r for r in REPOS if not (base / r / "timeline.csv").exists()]
    if missing:
        raise SystemExit(f"missing timelines: {missing}")

    out = base / "pilot_summary.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'repo':<9}{'pre':>4}{'post':>5}{'k':>3}  {'last-k-pre':>10} {'first-k-post':>12} {'D':>9} {'p':>7} "
          f"{'trend/mo':>9} {'D-trend':>9}  lags gini/daic/zlr")
    for r in rows:
        p = f"{r['wilcoxon_p']:.3f}" if r["wilcoxon_p"] is not None else "n/a"
        print(f"{r['repo']:<9}{r['n_pre']:>4}{r['n_post']:>5}{r['k']:>3}  {r['last_k_pre']:>10.4f} {r['first_k_post']:>12.4f} "
              f"{r['D']:>+9.4f} {p:>7} {r['pre_trend_per_month']:>+9.5f} {r['D_minus_trend']:>+9.4f}  "
              f"{r['lag_gini']}/{r['lag_delta_aic']}/{r['lag_vuong_z']}")

    d = [r["D"] for r in rows]
    dt = [r["D_minus_trend"] for r in rows]
    for label, vals in (("D", d), ("D minus pre-trend", dt),
                        ("D delta_aic", [r["D_delta_aic"] for r in rows]),
                        ("D vuong_z", [r["D_vuong_z"] for r in rows])):
        p = wilcoxon(vals, alternative="two-sided", method="exact").pvalue
        print(f"pooled {label}: n={len(vals)} negative={sum(v < 0 for v in vals)} "
              f"median={np.median(vals):+.4f} exact Wilcoxon p={p:.3f}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
