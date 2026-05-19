"""
plot_timeline.py

Generate time-series plots from timeline CSVs.
Produces:
  - Per-repo panel: Gini, Vuong z, delta_AIC over time with adoption date marked
  - Aggregate figure: mean ± std across all repos (normalized to adoption date)

Usage:
    python plot_timeline.py --longitudinal-dir ../../data/longitudinal --out-dir ../../figures/longitudinal
    python plot_timeline.py --timeline path/to/timeline.csv --out-dir ../../figures/longitudinal
"""

import csv
import argparse
from datetime import date
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STYLE = {
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
}

METRICS = [
    ("gini",      "Gini coefficient",          "#2c7bb6"),
    ("vuong_z",   "Vuong z (log-normal wins→)", "#d7191c"),
    ("delta_aic", "ΔAIC (log-normal advantage)","#1a9641"),
]


def load_timeline(path: Path) -> list[dict]:
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_date"] = date.fromisoformat(r["date"])
        r["_is_post"] = r["is_post"].lower() == "true"
    return rows


def find_adoption_date(rows: list[dict]) -> date | None:
    post = [r["_date"] for r in rows if r["_is_post"]]
    return min(post) if post else None


def plot_repo(rows: list[dict], repo_name: str, out_path: Path) -> None:
    rows = sorted(rows, key=lambda r: r["_date"])
    adoption = find_adoption_date(rows)
    dates = [r["_date"] for r in rows]

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(len(METRICS), 1, figsize=(8, 3 * len(METRICS)),
                                 sharex=True)
        for ax, (col, label, color) in zip(axes, METRICS):
            vals = []
            for r in rows:
                try:
                    vals.append(float(r[col]))
                except (ValueError, KeyError):
                    vals.append(float("nan"))
            ax.plot(dates, vals, color=color, lw=1.5, marker="o", ms=3)
            if adoption:
                ax.axvline(adoption, color="black", lw=1, ls="--", alpha=0.6,
                           label="Adoption date")
            ax.set_ylabel(label, fontsize=8)
            ax.legend(fontsize=7, loc="upper right")

        axes[-1].set_xlabel("Date")
        fig.suptitle(f"{repo_name} — structural topology over time", fontsize=10)
        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)
    print(f"  saved: {out_path}")


def plot_aggregate(all_series: list[tuple[str, list[dict]]], out_path: Path) -> None:
    """Normalized time axis: months relative to adoption date."""
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(len(METRICS), 1, figsize=(8, 3 * len(METRICS)),
                                 sharex=True)
        for ax, (col, label, color) in zip(axes, METRICS):
            all_months, all_vals = [], []
            for repo_name, rows in all_series:
                adoption = find_adoption_date(rows)
                if adoption is None:
                    continue
                rows_sorted = sorted(rows, key=lambda r: r["_date"])
                for r in rows_sorted:
                    try:
                        v = float(r[col])
                    except (ValueError, KeyError):
                        continue
                    months = (r["_date"].year - adoption.year) * 12 + (
                              r["_date"].month - adoption.month)
                    all_months.append(months)
                    all_vals.append(v)

            if not all_months:
                continue

            # Bin by month offset and compute mean ± std
            month_range = range(min(all_months), max(all_months) + 1)
            means, stds, xs = [], [], []
            for m in month_range:
                bucket = [v for mv, v in zip(all_months, all_vals) if mv == m]
                if bucket:
                    means.append(np.mean(bucket))
                    stds.append(np.std(bucket))
                    xs.append(m)

            xs_arr = np.array(xs)
            means_arr = np.array(means)
            stds_arr = np.array(stds)
            ax.plot(xs_arr, means_arr, color=color, lw=2, label="mean")
            ax.fill_between(xs_arr, means_arr - stds_arr, means_arr + stds_arr,
                            alpha=0.2, color=color)
            ax.axvline(0, color="black", lw=1, ls="--", alpha=0.6, label="Adoption")
            ax.set_ylabel(label, fontsize=8)
            ax.legend(fontsize=7, loc="upper right")

        axes[-1].set_xlabel("Months relative to adoption date")
        fig.suptitle("Aggregate structural topology: pre vs post AI adoption", fontsize=10)
        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)
    print(f"  saved: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--longitudinal-dir")
    src.add_argument("--timeline")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.timeline:
        path = Path(args.timeline)
        rows = load_timeline(path)
        repo_name = path.parent.name
        plot_repo(rows, repo_name, out_dir / f"{repo_name}_timeline.png")
    else:
        long_dir = Path(args.longitudinal_dir)
        all_series = []
        for timeline_path in sorted(long_dir.rglob("timeline.csv")):
            repo_name = timeline_path.parent.name
            rows = load_timeline(timeline_path)
            plot_repo(rows, repo_name, out_dir / f"{repo_name}_timeline.png")
            all_series.append((repo_name, rows))
        if len(all_series) > 1:
            plot_aggregate(all_series, out_dir / "aggregate_timeline.png")

    print("Done.")


if __name__ == "__main__":
    main()
