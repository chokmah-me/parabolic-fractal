"""
plot_contamination.py

Figures for the v1.1 post-release audit (paper Section 7.7):
  fig7_attribution_timeline.png  when AI-attributed commits occur in Cohort A
  fig8_gini_by_repo.png          per-repo Gini, Cohort A split by attribution

Reads only committed CSVs (no clones needed):
  data/attributed-commits-baseline.csv, data/contamination-baseline.csv,
  data/repos/provenance.csv, data/summary.csv

Usage:
    python scripts/plot_contamination.py
"""

import csv
from datetime import date, datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT = ROOT / "figures" / "v1.1"

BLUE = "#2c7bb6"
RED = "#d7191c"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
LATE = "#b9b7ae"
HAIR = "#e1e0d9"
BAND = "#f3f2ee"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8.5,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.6,
    "xtick.color": INK_2,
    "ytick.color": INK,
    "xtick.major.width": 0.6,
    "xtick.major.size": 3,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def year_frac(d: str) -> float:
    dt = datetime.strptime(d[:10], "%Y-%m-%d").date()
    start = date(dt.year, 1, 1)
    return dt.year + (dt - start).days / 365.25


def bare(ax, keep_bottom=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(keep_bottom)
    ax.tick_params(axis="y", length=0)


def fig_timeline():
    prov = {r["repo"]: r for r in read(DATA / "repos" / "provenance.csv") if r["group"] == "baseline"}
    cont = {r["repo"]: r for r in read(DATA / "contamination-baseline.csv")}
    hits = read(DATA / "attributed-commits-baseline.csv")

    repos = sorted(prov, key=lambda r: prov[r]["first_commit_date"])
    y = {r: len(repos) - 1 - i for i, r in enumerate(repos)}
    zoom = (year_frac("2025-01-01"), year_frac("2026-10-01"))

    fig, (ax_full, ax_zoom) = plt.subplots(
        1, 2, figsize=(6.6, 4.1), sharey=True,
        gridspec_kw={"width_ratios": [1, 1.35], "wspace": 0.06})

    for ax, lo, hi in ((ax_full, 2001, 2027), (ax_zoom, *zoom)):
        for r in repos:
            x0 = max(year_frac(prov[r]["first_commit_date"]), lo)
            x1 = min(year_frac(prov[r]["last_commit_date"]), hi)
            ax.hlines(y[r], x0, x1, color=MUTED, lw=0.8, zorder=1)
        for h in hits:
            x = year_frac(h["date"])
            if lo <= x <= hi:
                measured = h["at_snapshot"] == "True"
                ax.plot(x, y[h["repo"]], marker="|", ms=7, mew=0.9, ls="none",
                        color=RED if measured else LATE, zorder=3 if measured else 2)
        ax.set_xlim(lo, hi)
        bare(ax)

    ax_full.axvspan(*zoom, color=BAND, zorder=0, lw=0)
    ax_full.set_xticks([2005, 2010, 2015, 2020])
    ax_full.set_xticklabels(["2005", "2010", "2015", "2020"])
    ax_full.set_yticks([y[r] for r in repos])
    ax_full.set_yticklabels(repos)
    ax_full.set_title("Full history", loc="left", fontsize=8.5, color=INK_2)

    for r in repos:
        xs = year_frac(cont[r]["snapshot_date"])
        ax_zoom.vlines(xs, y[r] - 0.38, y[r] + 0.38, color=INK, lw=1.1, zorder=4)
        if cont[r]["config_date_at_snapshot"]:
            xc = year_frac(cont[r]["config_date_at_snapshot"])
            for ax in (ax_full, ax_zoom):
                ax.plot(xc, y[r], marker="D", ms=4.5, mfc="white", mec=INK, mew=0.9, ls="none", zorder=5)
        n_attr = int(cont[r]["attributed_at_snapshot"])
        n_all = int(cont[r]["commits_at_snapshot"])
        ax_zoom.text(zoom[1] + 0.03, y[r], f"{n_attr:,} / {n_all:,}", va="center",
                     ha="left", fontsize=7.5, color=INK if n_attr else MUTED)
    ax_zoom.text(zoom[1] + 0.03, len(repos) - 0.2, "attributed / commits\nat snapshot",
                 va="bottom", ha="left", fontsize=7, color=INK_2)
    ax_zoom.set_xticks([year_frac(d) for d in ("2025-01-01", "2025-07-01", "2026-01-01", "2026-07-01")])
    ax_zoom.set_xticklabels(["Jan 2025", "Jul 2025", "Jan 2026", "Jul 2026"])
    ax_zoom.set_title("Jan 2025 to Sep 2026", loc="left", fontsize=8.5, color=INK_2)
    ax_zoom.set_ylim(-0.7, len(repos) - 0.3)

    handles = [
        Line2D([], [], marker="|", ms=7, mew=0.9, ls="none", color=RED,
               label="attributed commit in the measured snapshot"),
        Line2D([], [], marker="|", ms=7, mew=0.9, ls="none", color=LATE,
               label="attributed commit not in the snapshot"),
        Line2D([], [], marker="|", ms=9, mew=1.1, ls="none", color=INK,
               label="snapshot measured in v1.0.0"),
        Line2D([], [], marker="D", ms=4.5, mfc="white", mec=INK, mew=0.9, ls="none",
               label="AI config file added"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.1, 0.02),
               ncol=2, frameon=False, fontsize=7.5, handletextpad=0.3, columnspacing=1.4)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig7_attribution_timeline.png")
    plt.close(fig)


def fig_gini():
    summary = read(DATA / "summary.csv")
    cont = {r["repo"]: r for r in read(DATA / "contamination-baseline.csv")}

    rows = []
    for r in summary:
        g = float(r["gini"])
        c = cont.get(r["repo"])
        if r["group"] == "agentic":
            rows.append((g, r["repo"], "agentic"))
        elif c and c["adoption_date_at_snapshot"]:
            n = int(c["attributed_at_snapshot"])
            tag = f"{n:,}" if n else "config file"
            rows.append((g, f"{r['repo']} ({tag})", "attributed"))
        else:
            rows.append((g, r["repo"], "clean"))
    n_clean = sum(k == "clean" for _, _, k in rows)
    n_att = sum(k == "attributed" for _, _, k in rows)
    rows.sort(key=lambda t: t[0])

    fig, ax = plt.subplots(figsize=(5.2, 5.6))
    lo, hi = 0.40, 1.0
    for i, (g, name, kind) in enumerate(rows):
        ax.hlines(i, lo, g, color=HAIR, lw=0.6, zorder=1)
        if kind == "agentic":
            ax.plot(g, i, "o", ms=5.5, color=RED, mec="white", mew=0.8, zorder=3)
        elif kind == "clean":
            ax.plot(g, i, "o", ms=5.5, color=BLUE, mec="white", mew=0.8, zorder=3)
        else:
            ax.plot(g, i, "o", ms=5.5, mfc="white", mec=BLUE, mew=1.3, zorder=3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([n for _, n, _ in rows], fontsize=7.5)
    ax.set_xlim(lo, hi)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlabel("Fan-in Gini coefficient", color=INK_2)
    bare(ax)

    handles = [
        Line2D([], [], marker="o", ls="none", ms=5.5, color=BLUE, mec="white",
               label=f"Cohort A, no AI signal in the snapshot (n={n_clean})"),
        Line2D([], [], marker="o", ls="none", ms=5.5, mfc="white", mec=BLUE, mew=1.3,
               label=f"Cohort A, AI signal in the snapshot (n={n_att}; attributed commits in parentheses)"),
        Line2D([], [], marker="o", ls="none", ms=5.5, color=RED, mec="white",
               label="Cohort B, agentic (n=12 fitted)"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.02, 1.0),
              frameon=False, fontsize=7.5, handletextpad=0.3)
    fig.savefig(OUT / "fig8_gini_by_repo.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_timeline()
    fig_gini()
    print(f"Wrote {OUT / 'fig7_attribution_timeline.png'} and {OUT / 'fig8_gini_by_repo.png'}")
