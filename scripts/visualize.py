"""
visualize.py

Generate the four paper figures from summary.csv and per-repo JSON files.

Figure 1: Log-log rank-freq plot, canonical baseline repo (Django), with fitted curves
Figure 2: Same for a canonical agentic repo
Figure 3: Box plots of Gini coefficient, baseline vs. agentic
Figure 4: Scatter — delta_AIC vs. repo age proxy (n_files as stand-in; replace with commit date if available)

Usage:
    python visualize.py --results-dir ../data/results --summary ../data/summary.csv --out-dir ../figures
"""

import json
import csv
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


COLORS = {"baseline": "#2c7bb6", "agentic": "#d7191c"}
STYLE = {
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
}


def load_summary(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def load_fanin(results_dir: Path, group: str, repo_name: str) -> np.ndarray:
    p = results_dir / group / f"{repo_name}.json"
    data = json.loads(p.read_text())
    return np.array(list(data.values()), dtype=float)


def rank_freq_data(fanin: np.ndarray):
    pos = fanin[fanin > 0]
    sorted_vals = np.sort(pos)[::-1]
    ranks = np.arange(1, len(sorted_vals) + 1)
    return ranks, sorted_vals


def fit_powerlaw(log_rank, log_val):
    A = np.column_stack([np.ones_like(log_rank), log_rank])
    c, _, _, _ = np.linalg.lstsq(A, log_val, rcond=None)
    return c


def fit_lognormal(log_rank, log_val):
    A = np.column_stack([np.ones_like(log_rank), log_rank, log_rank**2])
    c, _, _, _ = np.linalg.lstsq(A, log_val, rcond=None)
    return c


def plot_rank_freq(fanin: np.ndarray, title: str, out_path: Path, color: str) -> None:
    ranks, vals = rank_freq_data(fanin)
    log_rank = np.log(ranks)
    log_val = np.log(vals + 1e-9)

    pl_c = fit_powerlaw(log_rank, log_val)
    ln_c = fit_lognormal(log_rank, log_val)

    lr_dense = np.linspace(log_rank.min(), log_rank.max(), 300)
    pl_pred = np.exp(pl_c[0] + pl_c[1] * lr_dense)
    ln_pred = np.exp(ln_c[0] + ln_c[1] * lr_dense + ln_c[2] * lr_dense**2)

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(ranks, vals, s=8, alpha=0.5, color=color, label="observed", zorder=3)
        ax.plot(np.exp(lr_dense), pl_pred, "k--", lw=1.2, label="power-law fit")
        ax.plot(np.exp(lr_dense), ln_pred, color=color, lw=2, label="log-normal fit (parabolic)")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Rank (descending fan-in)")
        ax.set_ylabel("Fan-in count")
        ax.set_title(title)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)
    print(f"  saved: {out_path}")


def plot_gini_boxplots(rows: list[dict], out_path: Path) -> None:
    groups = {}
    for r in rows:
        g = r["group"]
        groups.setdefault(g, []).append(float(r["gini"]))

    labels = sorted(groups.keys())
    data = [groups[g] for g in labels]
    colors = [COLORS.get(g, "#888") for g in labels]

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5, 4))
        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.4)
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_ylabel("Gini coefficient (fan-in distribution)")
        ax.set_title("Fan-in Gini: baseline vs. agentic repos")
        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)
    print(f"  saved: {out_path}")


def plot_delta_aic_scatter(rows: list[dict], out_path: Path) -> None:
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 4))
        seen_groups: set[str] = set()
        for r in rows:
            g = r["group"]
            x = float(r["n_files"])
            y = float(r["delta_aic"])
            ax.scatter(x, y, color=COLORS.get(g, "#888"), s=40, alpha=0.8,
                       label=g if g not in seen_groups else "")
            seen_groups.add(g)
        ax.axhline(0, color="gray", lw=0.8, ls="--")
        ax.axhline(2, color="gray", lw=0.5, ls=":")
        ax.set_xlabel("Number of .py files (repo size proxy)")
        ax.set_ylabel("ΔAIC (power-law − log-normal)\npositive = log-normal wins")
        ax.set_title("Log-normal fit advantage vs. repo size")
        ax.legend(fontsize=8)

        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)
    print(f"  saved: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--baseline-example", default="django",
                        help="Repo name (no .json) to use as Figure 1 example")
    parser.add_argument("--agentic-example", default=None,
                        help="Repo name (no .json) to use as Figure 2 example")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_summary(Path(args.summary))

    # Figure 1: canonical baseline
    try:
        fanin_bl = load_fanin(results_dir, "baseline", args.baseline_example)
        plot_rank_freq(fanin_bl, f"Figure 1: {args.baseline_example} (baseline)",
                       out_dir / "fig1_baseline_rankfreq.png", COLORS["baseline"])
    except FileNotFoundError:
        print(f"  WARNING: baseline example '{args.baseline_example}' not found, skipping Fig 1")

    # Figure 2: canonical agentic
    agentic_repos = [r for r in rows if r["group"] == "agentic"]
    if args.agentic_example:
        example_name = args.agentic_example
    elif agentic_repos:
        example_name = agentic_repos[0]["repo"]
    else:
        example_name = None

    if example_name:
        try:
            fanin_ag = load_fanin(results_dir, "agentic", example_name)
            plot_rank_freq(fanin_ag, f"Figure 2: {example_name} (agentic)",
                           out_dir / "fig2_agentic_rankfreq.png", COLORS["agentic"])
        except FileNotFoundError:
            print(f"  WARNING: agentic example '{example_name}' not found, skipping Fig 2")
    else:
        print("  No agentic repos found, skipping Fig 2")

    # Figure 3: Gini boxplots
    plot_gini_boxplots(rows, out_dir / "fig3_gini_boxplot.png")

    # Figure 4: delta AIC scatter
    plot_delta_aic_scatter(rows, out_dir / "fig4_deltaaic_scatter.png")

    print("Done.")


if __name__ == "__main__":
    main()
