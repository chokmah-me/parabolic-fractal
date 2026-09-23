"""
check_paper_claims.py

Executable gate for the v1.1 Version Note and Section 7.7: recomputes every
cited number and checks that the paper text states it. Exit 0 only if all
checks pass and none were skipped.

Committed-data checks run anywhere. Clone checks need data/repos/baseline/*
(full history) and data/longitudinal/*/timeline.csv; without them they are
reported as SKIP and the exit code is 2, unless --allow-skip is given.

Usage:
    python scripts/check_paper_claims.py [--allow-skip]
"""

import csv
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

from scipy.stats import mannwhitneyu

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "longitudinal"))
from compare_groups import mannwhitney_u  # noqa: E402
from find_adoption_date import _COMMIT_RE, find_adoption_date  # noqa: E402

PAPER = ROOT / "paper" / "dyb-2026q-AI-Python-constructal-v1.1-REL.md"
TEXT = PAPER.read_text(encoding="utf-8")
BASE = ROOT / "data" / "repos" / "baseline"
results = {"PASS": 0, "FAIL": 0, "SKIP": 0}


def check(name, got, want, cite=None):
    ok = got == want
    cited = cite is None or cite in TEXT
    status = "PASS" if ok and cited else "FAIL"
    results[status] += 1
    note = "" if cited else f"  (paper does not contain {cite!r})"
    print(f"{status}  {name}: got {got!r}, want {want!r}{note}")


def skip(name, why):
    results["SKIP"] += 1
    print(f"SKIP  {name}: {why}")


def read(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sig2(x):
    return f"{x:.2g}"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, errors="ignore").stdout


# --- E1 / 7.7: contamination at the measured snapshots ---------------------
cont = {r["repo"]: r for r in read(ROOT / "data" / "contamination-baseline.csv")}
snap = {k: int(r["attributed_at_snapshot"]) for k, r in cont.items()}
allr = {k: int(r["attributed_all_refs"]) for k, r in cont.items()}
check("attributed commits at snapshot", sum(snap.values()), 421, "421 of 221,145")
check("commits at snapshot", sum(int(r["commits_at_snapshot"]) for r in cont.values()), 221145)
check("share at snapshot", f"{100 * 421 / 221145:.2f}%", "0.19%", "(0.19%)")
affected = sorted(k for k, v in snap.items() if v)
check("affected repos", len(affected), 9, "in 9 repos")
check("unaffected repos", sorted(k for k, v in snap.items() if not v),
      ["click", "django", "flask", "httpx", "sqlalchemy", "tornado"],
      "Django, SQLAlchemy, Flask, Click, httpx, and Tornado have none")
check("pandas at snapshot", snap["pandas"], 386, "Pandas holds 386 of the 421")
check("pandas top contributor", int(cont["pandas"]["top_author_count_at_snapshot"]), 379, "379 of them from one contributor")
pandas_share = snap["pandas"] / int(cont["pandas"]["commits_at_snapshot"])
check("pandas share", f"{100 * pandas_share:.1f}%", "1.0%", "(1.0% of its commits)")
others = [k for k in affected if k != "pandas"]
check("other affected range", (min(snap[k] for k in others), max(snap[k] for k in others)), (1, 12), "between 1 and 12 each")
check("other affected all < 0.1%", all(snap[k] / int(cont[k]["commits_at_snapshot"]) < 0.001 for k in others), True,
      "under 0.1% of their commits")
check("earliest attributed at snapshot", min(cont[k]["first_attributed_at_snapshot"][:10] for k in affected), "2025-05-09",
      "The earliest is dated 2025-05-09")
check("later attributed commits", sum(allr.values()) - sum(snap.values()), 860, "860 further attributed commits")
check("tornado after snapshot", (snap["tornado"], allr["tornado"]), (0, 33), "all 33 in Tornado")

hits = read(ROOT / "data" / "attributed-commits-baseline.csv")
check("per-commit list matches totals", (len(hits), sum(h["at_snapshot"] == "True" for h in hits)), (1281, 421))

prov = [r for r in read(ROOT / "data" / "repos" / "provenance.csv") if r["group"] == "baseline"]
check("first-commit years", (min(r["first_commit_date"] for r in prov)[:4], max(r["first_commit_date"] for r in prov)[:4]),
      ("2001", "2019"), "first commits date from 2001 to 2019")

# --- 7.7: Gini position and exclusion test ----------------------------------
summary = read(ROOT / "data" / "summary.csv")
gini = {r["repo"]: float(r["gini"]) for r in summary}
bl_all = [r for r in summary if r["group"] == "baseline"]
bl_clean = [r for r in bl_all if r["repo"] not in affected]
ag = [r for r in summary if r["group"] == "agentic"]
check("median Gini, affected", f"{statistics.median(gini[k] for k in affected):.3f}", "0.906", "Their median Gini is 0.906")
check("median Gini, unaffected", f"{statistics.median(float(r['gini']) for r in bl_clean):.3f}", "0.855", "0.855 for the six unaffected")
check("median Gini, Cohort B", f"{statistics.median(float(r['gini']) for r in ag):.3f}", "0.728", "0.728 for Cohort B")
check("group sizes", (len(bl_clean), len(ag)), (6, 12), "n=6 vs. 12")

want = {  # metric: (exact p, normal-approx p, r clean, r full)
    "gini": ("0.0097", "0.011", "-0.75", "-0.74"),
    "entropy_norm": ("0.024", "0.025", "0.67", "0.71"),
    "delta_aic": ("0.12", "0.11", "-0.47", "-0.53"),
    "frac_leaves": ("0.083", "0.075", "-0.53", "-0.56"),
}
max_dr = 0.0
for m, (w_exact, w_norm, w_rc, w_rf) in want.items():
    a = [float(r[m]) for r in bl_clean]
    b = [float(r[m]) for r in ag]
    full = [float(r[m]) for r in bl_all]
    exact = mannwhitneyu(a, b, alternative="two-sided", method="exact").pvalue
    _, p_norm, r_clean = mannwhitney_u(a, b)
    _, _, r_full = mannwhitney_u(full, b)
    max_dr = max(max_dr, abs(r_clean - r_full))
    check(f"{m} exact p (n=6)", sig2(exact), w_exact, f"p={w_exact}" if m != "delta_aic" and m != "frac_leaves" else f"(p={w_exact})")
    check(f"{m} normal-approx p (n=6)", sig2(p_norm), w_norm, w_norm)
    check(f"{m} r (n=6 / n=15)", (f"{r_clean:.2f}", f"{r_full:.2f}"), (w_rc, w_rf))
check("r shift within 0.07", max_dr < 0.07, True, "within 0.07 of their full-sample values")

_, p_full, r_full = mannwhitney_u([float(r["gini"]) for r in bl_all], [float(r["gini"]) for r in ag])
check("v1.0.0 Gini result unchanged", (f"{p_full:.4f}", f"{r_full:.3f}"), ("0.0011", "-0.744"))

# --- E5: stale figures ------------------------------------------------------
old_summary = subprocess.run(["git", "-C", str(ROOT), "show", "80e3fab:data/summary.csv"],
                             capture_output=True, text=True).stdout
old_ag = [float(r["gini"]) for r in csv.DictReader(old_summary.splitlines()) if r["group"] == "agentic"]
ag_g = [float(r["gini"]) for r in ag]
check("Fig 3 as published: agentic n / median", (len(old_ag), f"{statistics.median(old_ag):.3f}"), (8, "0.747"),
      "instead of the plotted 0.747")
check("Fig 3 redrawn: min agentic Gini", f"{min(ag_g):.3f}", "0.460", "lower whisker reaches 0.460 (codebase-mcp)")
daic = sorted(float(r["delta_aic"]) for r in ag)
check("Fig 4: agentic DAIC < 6", sum(d < 6 for d in daic), 6, "(6 of 12) have DAIC below 6")
check("Fig 4: agentic max DAIC <= 83", max(daic) <= 83, True, "none exceeds 83")
check("Fig 4: baseline max DAIC", round(max(float(r["delta_aic"]) for r in bl_all)), 308, "spreads up to 308")

# --- C1 / 7.7: regex vs Jev -------------------------------------------------
trial = json.loads((ROOT / "data" / "trials" / "pf_hist_result.json").read_text(encoding="utf-8"))
jev_pos = [t for t in trial if t["jev"] is not None and t["jev"] >= 0.5]
check("trial size by cohort", (len(trial), sum(t["group"] == "baseline" for t in trial), sum(t["group"] == "agentic" for t in trial)),
      (1275, 1028, 247), "1,275 commits (1,028 from Cohort A, 247 from Cohort B)")
check("regex and Jev positives", (sum(1 for t in trial if t["regex"]), len(jev_pos)), (116, 116), "the same 116 commits")
check("disagreements", sum(bool(t["regex"]) != (t in jev_pos) for t in trial), 0)
check("scores in [0.5, 0.9)", sum(1 for t in trial if t["jev"] is not None and 0.5 <= t["jev"] < 0.9), 0,
      "no classifier score fell between 0.5 and 0.9")

# --- Clone-dependent checks (E2, E3, E4, snapshot identity) -----------------
celery, aiohttp = BASE / "celery", BASE / "aiohttp"
if (celery / ".git" / "shallow").exists() or not celery.exists() or not aiohttp.exists():
    skip("E2/E3 dates", "full-history clones of celery and aiohttp not present")
else:
    check("E2 Celery date (fixed parser)", find_adoption_date(celery), "2025-05-09", "is dated 2025-05-09")
    log = git(celery, "log", "--all", "--format=%ai %s %b")
    old = [ln.split(" ", 3) for ln in log.splitlines()]
    old_commit = sorted(p[0] for p in old if len(p) == 4 and _COMMIT_RE.search(p[3]))
    cfg = git(celery, "log", "--all", "--diff-filter=A", "--format=%ad", "--date=short", "--", ".github/copilot-instructions.md").split()
    check("E2 v1.0.0 parser result", min(old_commit[:1] + cfg), "2025-08-26", "2025-08-26")
    fs, rs = "\x1f", "\x1e"
    day = git(celery, "log", "--all", "--since=2025-05-08T00:00", "--until=2025-05-08T23:59:59",
              f"--format=%s{fs}%b{rs}")
    check("E2 no attributed Celery commit on 2025-05-08",
          sum(1 for rec in day.split(rs) if rec.strip() and _COMMIT_RE.search(rec)), 0)
    day = git(aiohttp, "log", "--all", "--since=2026-05-04T00:00", "--until=2026-05-04T23:59:59", f"--format=%s%n%b{rs}")
    check("E3 no aiohttp commit on 2026-05-04 mentions Claude/Anthropic",
          bool(re.search(r"claude|anthropic", day, re.I)), False)
    check("E3 aiohttp earliest attributed", cont["aiohttp"]["first_attributed_all_refs"][:10], "2026-05-16", "dated 2026-05-16")
    check("E3 aiohttp snapshot date", cont["aiohttp"]["snapshot_date"], "2026-05-18", "(2026-05-18)")

lags = {("celery", "gini"): "-486", ("celery", "delta_aic"): "+273", ("celery", "vuong_z"): "+273",
        ("django", "gini"): "-31", ("django", "delta_aic"): "-31", ("django", "vuong_z"): "-182"}
for (repo, metric), want_lag in lags.items():
    tl = ROOT / "data" / "longitudinal" / repo / "timeline.csv"
    if not tl.exists():
        skip(f"E4 lag {repo} {metric}", f"{tl.relative_to(ROOT)} not present (gitignored)")
        continue
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "longitudinal" / "detect_changepoint.py"),
                          "--timeline", str(tl), "--metric", metric], capture_output=True, text=True).stdout
    m = re.search(r"lag: ([+-]\d+) days", out)
    check(f"E4 lag {repo} {metric}", m.group(1) if m else None, want_lag, f"| {want_lag} days")

if not (BASE / "click").exists():
    skip("snapshot identity", "baseline clones not present")
else:
    from compute_fanin import compute_fanin
    diff = [p.name for p in sorted(BASE.iterdir())
            if compute_fanin(p) != json.loads((ROOT / "data" / "results" / "baseline" / f"{p.name}.json").read_text())]
    check("fan-in at HEAD equals stored results", diff, [], "reproduces the stored per-file results exactly")

check("no unresolved [AUTHOR ...] placeholders", re.findall(r"\[AUTHOR[^\]]*\]", TEXT), [])

print(f"\n{results['PASS']} passed, {results['FAIL']} failed, {results['SKIP']} skipped")
allow_skip = "--allow-skip" in sys.argv
sys.exit(1 if results["FAIL"] else (2 if results["SKIP"] and not allow_skip else 0))
