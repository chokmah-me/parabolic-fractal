"""
plot_pilot.py

Paper v1.1 Figure 6: Gini trajectories of the eight pilot repos, indexed to
the last pre-adoption snapshot and aligned at the adoption boundary.

Usage:
    python scripts/longitudinal/plot_pilot.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "longitudinal-v1.1"
OUT = ROOT / "figures" / "v1.1" / "fig6_pilot_gini.png"
REPOS = ["celery", "numpy", "pandas", "pytest", "fastapi", "scrapy", "django", "pydantic"]

RED, INK, INK_2, MUTED, HAIR = "#d7191c", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": INK_2, "ytick.color": INK_2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})


def series(repo):
    with open(DATA / repo / "timeline.csv") as f:
        rows = [r for r in csv.DictReader(f) if r["gini"]]
    post = [r["is_post"].lower() == "true" for r in rows]
    first = post.index(True)
    base = float(rows[first - 1]["gini"])
    xs = [i - first for i in range(len(rows))]
    ys = [float(r["gini"]) - base for r in rows]
    return xs, ys, first, rows[first]["date"][:7]


def main():
    data = {r: series(r) for r in REPOS}
    lim = max(abs(v) for xs, ys, _, _ in data.values() for v in ys) * 1.1
    fig, axes = plt.subplots(2, 4, figsize=(6.6, 3.8), sharex=True, sharey=True,
                             gridspec_kw={"hspace": 0.55, "wspace": 0.12})
    for ax, repo in zip(axes.flat, REPOS):
        xs, ys, first, month = data[repo]
        ax.axhline(0, color=HAIR, lw=0.8, zorder=0)
        ax.axvline(-0.5, color=MUTED, lw=0.6, zorder=0)
        ax.plot(xs[:first], ys[:first], color=MUTED, lw=1.1)
        ax.plot(xs[first - 1:], ys[first - 1:], color=RED, lw=1.4)
        ax.plot(xs[-1], ys[-1], "o", ms=3, color=RED)
        ax.set_title(repo, loc="left", fontsize=8, color=INK, pad=9)
        ax.text(0, 1.015, f"adoption boundary {month}", transform=ax.transAxes, fontsize=6.5, color=INK_2, va="bottom")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.set_ylim(-lim, lim)
        ax.set_xlim(-25, 13)
        ax.set_xticks([-24, -12, 0, 12])
    for ax in axes[1]:
        ax.set_xlabel("months from adoption", color=INK_2)
    for ax in axes[:, 0]:
        ax.set_ylabel("Gini change", color=INK_2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
