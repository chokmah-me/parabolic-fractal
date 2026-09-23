"""
check_paper_claims.py

Executable gate for paper v1.1: recomputes every number in the Version Note,
Sections 5 and 6 (longitudinal pilot), and Section 7.7, parses Tables 5.1,
6.1 and 6.2 from the paper and compares every cell, and checks that README.md
and .zenodo.json repeat the same figures. Exit 0 only if every check passes
and none were skipped.

Committed-data checks run anywhere. Clone checks need full-history clones in
data/repos/baseline/ and the v1.0.0 timelines in data/longitudinal/; without
them they are reported as SKIP and the exit code is 2 unless --allow-skip.

Usage:
    python scripts/check_paper_claims.py [--allow-skip]
"""

import csv
import json
import re
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path

from scipy.stats import mannwhitneyu, wilcoxon

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "longitudinal"))
from compare_groups import mannwhitney_u  # noqa: E402
from detect_changepoint import load_series, sliding_window_changepoint  # noqa: E402
from find_adoption_date import _COMMIT_RE, find_adoption_date  # noqa: E402

PAPER = ROOT / "paper" / "dyb-2026q-AI-Python-constructal-v1.1-REL.md"
TEXT = PAPER.read_text(encoding="utf-8")
FLAT = re.sub(r"\s+", " ", TEXT)
README = re.sub(r"\s+", " ", (ROOT / "README.md").read_text(encoding="utf-8"))
ZENODO = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
BASE = ROOT / "data" / "repos" / "baseline"
PILOT = ["celery", "numpy", "pandas", "pytest", "fastapi", "scrapy", "django", "pydantic"]
results = {"PASS": 0, "FAIL": 0, "SKIP": 0}


def check(name, got, want, cite=None, where=None):
    """cite: string (or list) that must appear in the paper, or in `where` if given."""
    hay = FLAT if where is None else where
    cites = [] if cite is None else ([cite] if isinstance(cite, str) else cite)
    missing = [c for c in cites if re.sub(r"\s+", " ", c) not in hay]
    status = "PASS" if got == want and not missing else "FAIL"
    results[status] += 1
    note = f"  (text lacks {missing!r})" if missing else ""
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
                          text=True, encoding="utf-8", errors="replace").stdout


# === E1 / 7.7: AI signals in the measured Cohort A snapshots =================
cont = {r["repo"]: r for r in read(ROOT / "data" / "contamination-baseline.csv")}
snap = {k: int(r["attributed_at_snapshot"]) for k, r in cont.items()}
allr = {k: int(r["attributed_all_refs"]) for k, r in cont.items()}
hits = read(ROOT / "data" / "attributed-commits-baseline.csv")
check("attributed commits at snapshot", (sum(snap.values()), sum(int(r["commits_at_snapshot"]) for r in cont.values())),
      (421, 221145), "421 of 221,145 commits (0.19%)")
with_commits = sorted(k for k, v in snap.items() if v)
affected = sorted(k for k, r in cont.items() if r["adoption_date_at_snapshot"])
clean = sorted(set(cont) - set(affected))
check("repos with attributed commits", len(with_commits), 9, "in 9 repos")
check("Django config-only signal", (snap["django"], cont["django"]["config_file_at_snapshot"], cont["django"]["config_date_at_snapshot"]),
      (0, ".github/copilot-instructions.md", "2026-03-05"), "added 2026-03-05")
check("other config files", sorted(k for k in affected if cont[k]["config_file_at_snapshot"]), ["aiohttp", "celery", "django"],
      "Celery and aiohttp also contain AI configuration files")
check("affected repos (adoption definition)", len(affected), 10, "10 of the 15 repos had adopted AI tools before their snapshot")
check("unaffected repos", clean, ["click", "flask", "httpx", "sqlalchemy", "tornado"],
      "SQLAlchemy, Flask, Click, httpx, and Tornado had not")
check("pandas", (snap["pandas"], int(cont["pandas"]["top_author_count_at_snapshot"]),
                 f"{100 * snap['pandas'] / int(cont['pandas']['commits_at_snapshot']):.1f}%"),
      (386, 379, "1.0%"), ["Pandas holds 386 of the 421 (1.0% of its commits), 379 of them from one contributor"])
others = [k for k in with_commits if k != "pandas"]
check("other repos with attributed commits", (min(snap[k] for k in others), max(snap[k] for k in others),
      all(snap[k] / int(cont[k]["commits_at_snapshot"]) < 0.001 for k in others)), (1, 12, True),
      "between 1 and 12 each, under 0.1% of their commits")
check("earliest attributed at snapshot", min(cont[k]["first_attributed_at_snapshot"][:10] for k in with_commits),
      "2025-05-09", "The earliest is dated 2025-05-09")
prov = [r for r in read(ROOT / "data" / "repos" / "provenance.csv") if r["group"] == "baseline"]
check("first-commit years", (min(r["first_commit_date"] for r in prov)[:4], max(r["first_commit_date"] for r in prov)[:4]),
      ("2001", "2019"), "first commits date from 2001 to 2019")
outside = [h for h in hits if h["at_snapshot"] == "False"]
before = [h for h in outside if h["date"][:10] < cont[h["repo"]]["snapshot_date"]]
check("attributed commits outside snapshots (total, later, unmerged)",
      (len(outside), len(outside) - len(before), len(before)), (860, 846, 14),
      "860 further attributed commits that are not in the snapshots: 846 were made after them, and 14 sit on branches never merged into them")
check("Tornado", (snap["tornado"], allr["tornado"], all(h["date"][:10] > cont["tornado"]["snapshot_date"] for h in outside if h["repo"] == "tornado")),
      (0, 33, True), "all 33 in Tornado")
check("per-commit list matches totals", (len(hits), sum(h["at_snapshot"] == "True" for h in hits)), (1281, 421))

# === E1 / 7.7: Gini position and exclusion test ============================
summary = read(ROOT / "data" / "summary.csv")
S = {r["repo"]: r for r in summary}
bl = [r for r in summary if r["group"] == "baseline"]
blc = [r for r in bl if r["repo"] in clean]
ag = [r for r in summary if r["group"] == "agentic"]
med = lambda rows, m="gini": statistics.median(float(r[m]) for r in rows)
check("median Gini: affected / unaffected / Cohort B",
      (f"{med([S[k] for k in affected]):.3f}", f"{med(blc):.3f}", f"{med(ag):.3f}"), ("0.912", "0.845", "0.728"),
      "their median Gini is 0.912, against 0.845 for the five unaffected repos and 0.728 for Cohort B")
check("median Python files: unaffected / affected",
      (f"{med(blc, 'n_files'):.0f}", f"{med([S[k] for k in affected], 'n_files'):.0f}"), ("83", "428"),
      ["median 83 Python files, against 428 for the ten affected ones", "median 83 Python files, against 428 for the ten removed"])
want = {  # metric: (exact p clean, r clean, r full, paper citation)
    "gini": ("0.027", "-0.70", "-0.74", "p=0.027 for Gini (rank-biserial r=-0.70, against -0.74 with all 15 repos)"),
    "vuong_z": ("0.014", "-0.77", "-0.61", "p=0.014 for $$z_{lr}$$ (r=-0.77, against -0.61)"),
    "entropy_norm": ("0.064", "0.60", "0.71", "normalized entropy p=0.064 (r=+0.60, against +0.71)"),
    "delta_aic": ("0.28", "-0.37", "-0.53", "DAIC p=0.28 (r=-0.37, against -0.53)"),
    "frac_leaves": ("0.13", "-0.50", "-0.56", "leaf fraction p=0.13 (r=-0.50, against -0.56)"),
}
for m, (w_p, w_rc, w_rf, cite) in want.items():
    a, b, f = [float(r[m]) for r in blc], [float(r[m]) for r in ag], [float(r[m]) for r in bl]
    p = mannwhitneyu(a, b, alternative="two-sided", method="exact").pvalue
    check(f"exclusion test {m} (n={len(a)} vs {len(b)})",
          (sig2(p), f"{mannwhitney_u(a, b)[2]:.2f}", f"{mannwhitney_u(f, b)[2]:.2f}"), (w_p, w_rc, w_rf), cite)
excl = {r["metric"]: r for r in read(ROOT / "data" / "compare_groups_excl_contaminated.csv")}
check("exclusion CSV matches the 10 affected repos", sorted(excl["gini"]["excluded_repos"].split(";")), affected)

_, p_full, r_full = mannwhitney_u([float(r["gini"]) for r in bl], [float(r["gini"]) for r in ag])
check("v1.0.0 Gini result unchanged", (f"{p_full:.4f}", f"{r_full:.3f}"), ("0.0011", "-0.744"))
_, p_z, r_z = mannwhitney_u([float(r["vuong_z"]) for r in bl], [float(r["vuong_z"]) for r in ag])
check("E7 z_lr p-value", (f"{p_z:.4f}", f"{r_z:.2f}"), ("0.0073", "-0.61"),
      ["The $$z_{lr}$$ comparison gives p=0.0073 (r=-0.61)", "($$z_{lr}$$ mean 2.77 vs 6.00, p=0.0073)"])

# === E5: stale figures ======================================================
old = subprocess.run(["git", "-C", str(ROOT), "show", "80e3fab:data/summary.csv"], capture_output=True, text=True).stdout
old_ag = [float(r["gini"]) for r in csv.DictReader(old.splitlines()) if r["group"] == "agentic"]
check("Fig 3 as published", (len(old_ag), f"{statistics.median(old_ag):.3f}"), (8, "0.747"), "instead of the plotted 0.747")
check("Fig 3 redrawn lower whisker", f"{min(float(r['gini']) for r in ag):.3f}", "0.460", "lower whisker reaches 0.460 (codebase-mcp)")
daic = [float(r["delta_aic"]) for r in ag]
check("Fig 4 caption", (sum(d < 6 for d in daic), max(daic) <= 83, round(max(float(r["delta_aic"]) for r in bl))), (6, True, 308),
      ["(6 of 12) have DAIC below 6", "none exceeds 83", "spreads up to 308"])

# === C1 / 7.7: regex vs LLM classifier =====================================
trial = json.loads((ROOT / "data" / "trials" / "pf_hist_result.json").read_text(encoding="utf-8"))
jev = [t for t in trial if t["jev"] is not None and t["jev"] >= 0.5]
check("trial composition", (len(trial), sum(t["group"] == "baseline" for t in trial), sum(t["group"] == "agentic" for t in trial)),
      (1275, 1028, 247), "1,275 commits (1,028 from Cohort A, 247 from Cohort B)")
check("regex and classifier agree", (sum(1 for t in trial if t["regex"]), len(jev), sum(bool(t["regex"]) != (t in jev) for t in trial)),
      (116, 116, 0), "the same 116 commits")
check("no score in [0.5, 0.9)", sum(1 for t in trial if t["jev"] is not None and 0.5 <= t["jev"] < 0.9), 0,
      "no classifier score fell between 0.5 and 0.9")
check("Cohort A positives in trial", sum(1 for t in trial if t["regex"] and t["group"] == "baseline"), 1,
      "Only one of the 116 came from Cohort A")

# === Sections 5-6: the eight-repo pilot =====================================
ps = {r["repo"]: r for r in read(ROOT / "data" / "longitudinal-v1.1" / "pilot_summary.csv")}
check("pilot repos", sorted(ps), sorted(PILOT))

# eligibility (5.1): adoption signal at snapshot, >50 py files at adoption, >= 2 post snapshots
def post_snapshots(adopt, snapdate):
    a, s_ = date.fromisoformat(adopt), date.fromisoformat(snapdate)
    y, m, n = a.year, a.month, 0
    while True:
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if date(y, m, 1) > s_:
            return n
        n += 1

if (BASE / "celery").exists():
    elig, nfiles = [], {}
    for k in affected:
        adopt = cont[k]["adoption_date_at_snapshot"]
        sha = git(BASE / k, "rev-list", "-n1", f"--before={adopt}T23:59:59", "HEAD").strip()
        nfiles[k] = sum(1 for f in git(BASE / k, "ls-tree", "-r", "--name-only", sha).splitlines() if f.endswith(".py"))
        if nfiles[k] > 50 and post_snapshots(adopt, cont[k]["snapshot_date"]) >= 2:
            elig.append(k)
    check("eligible pilot repos", sorted(elig), sorted(PILOT), "Eight repos qualify")
    check("requests file count at adoption", nfiles["requests"], 36, "Requests is excluded (36 Python files at its adoption date)")
    check("aiohttp post-adoption snapshots", post_snapshots(cont["aiohttp"]["adoption_date_at_snapshot"], cont["aiohttp"]["snapshot_date"]), 0,
          "aiohttp has no post-adoption snapshot (adoption 2026-05-16, collected 2026-05-18)")
else:
    skip("eligibility", "baseline clones not present")

# Table 5.1
t51 = {m.group(1).lower(): (m.group(2), int(m.group(3))) for m in
       re.finditer(r"^\| (\w+)\s*\| (\d{4}-\d\d-\d\d)\s*\| [^|]+\| (\d+)\s*\|$", TEXT, re.M)}
check("Table 5.1 rows", sorted(t51), sorted(PILOT))
for k in PILOT:
    check(f"Table 5.1 {k}", t51.get(k), (cont[k]["adoption_date_at_snapshot"], int(ps[k]["n_post"])))

# 5.2 snapshot counts
counts = ", ".join(f"{n} {int(ps[k]['n_pre']) + int(ps[k]['n_post'])} ({ps[k]['n_pre']} + {ps[k]['n_post']})" for k, n in
                   zip(PILOT, ["Celery", "NumPy", "pandas", "pytest", "FastAPI", "Scrapy", "Django", "Pydantic"]))
check("5.2 snapshot counts", True, True, counts)

# Table 6.1
t61 = {m.group(1).lower(): m.groups()[1:] for m in re.finditer(
    r"^\| (\w+)\s*\| (\d+)\s*\| (\d) \| ([\d.]+)\s*\| ([\d.]+)\s*\| ([+-][\d.]+)\s*\| ([\w./]+)\s*\| ([+-][\d.]+)\s*\|$", TEXT, re.M)}
check("Table 6.1 rows", sorted(t61), sorted(PILOT))
for k in PILOT:
    r = ps[k]
    p = f"{float(r['wilcoxon_p']):.3f}" if r["wilcoxon_p"] else "n/a"
    want_row = (r["n_post"], r["k"], f"{float(r['last_k_pre']):.4f}", f"{float(r['first_k_post']):.4f}",
                f"{float(r['D']):+.4f}", p, f"{float(r['D_minus_trend']):+.4f}")
    check(f"Table 6.1 {k}", t61.get(k), want_row)

def pooled(vals):
    return (sum(v > 0 for v in vals), sum(v < 0 for v in vals), statistics.median(vals),
            wilcoxon(vals, alternative="two-sided", method="exact").pvalue)
D = [float(ps[k]["D"]) for k in PILOT]
up, down, mD, pD = pooled(D)
check("6.1 pooled D", (up, f"{mD:+.4f}", f"{pD:.3f}"), (6, "+0.0008", "0.195"),
      ["Gini rose after adoption in six of the eight repos", "median D is +0.0008 and the exact Wilcoxon test gives p=0.195",
       "Gini rose in 6 of 8; pooled exact Wilcoxon p=0.195", "Gini rose in six; pooled exact Wilcoxon p=0.195"])
check("6.1 decreases", sorted((k, f"{float(ps[k]['D']):+.4f}") for k in PILOT if float(ps[k]["D"]) < 0),
      [("fastapi", "-0.0023"), ("pytest", "-0.0003")], "fell in pytest (-0.0003) and FastAPI (-0.0023)")
_, _, mT, pT = pooled([float(ps[k]["D_minus_trend"]) for k in PILOT])
check("6.1 detrended", (f"{mT:+.4f}", f"{pT:.3f}"), ("+0.0002", "0.945"), "the median is +0.0002 and p=0.945")
check("6.1 min pooled p reachable with 8 repos", f"{wilcoxon([1.0 * (i + 1) for i in range(8)], method='exact').pvalue:.4f}", "0.0078",
      "with eight repos it can reach p=0.0078")
check("6.1 FastAPI detrended", f"{float(ps['fastapi']['D_minus_trend']):+.4f}", "-0.0103", "0.0103 below its pre-adoption trend")
check("7.6 median post window", statistics.median(int(ps[k]["n_post"]) for k in PILOT), 3.5, "(median 3.5)")

_, _, mA, pA = pooled([float(ps[k]["D_delta_aic"]) for k in PILOT])
_, zdown, mZ, pZ = pooled([float(ps[k]["D_vuong_z"]) for k in PILOT])
check("6.2 DAIC pooled", (sum(float(ps[k]["D_delta_aic"]) < 0 for k in PILOT), f"{mA:.1f}", f"{pA:.3f}"), (5, "-2.3", "0.742"),
      "DAIC fell in five repos and rose in three (median D -2.3, exact Wilcoxon p=0.742)")
check("6.2 z_lr pooled", (zdown, f"{mZ:+.2f}", f"{pZ:.3f}"), (3, "+0.07", "0.945"),
      "fell in three and rose in five (median D +0.07, p=0.945)")

def tl(repo):
    return {r["date"]: r for r in read(ROOT / "data" / "longitudinal-v1.1" / repo / "timeline.csv")}
N, F = tl("numpy"), tl("fastapi")
check("6.2 NumPy drop", (f"{float(N['2025-12-01']['vuong_z']):.2f}", f"{float(N['2026-01-01']['vuong_z']):.2f}",
      f"{float(N['2025-12-01']['delta_aic']):.1f}", f"{float(N['2026-01-01']['delta_aic']):.1f}"), ("3.20", "0.66", "17.2", "-0.8"),
      "NumPy's $$z_{lr}$$ fell from 3.20 to 0.66, and its DAIC from 17.2 to -0.8")
check("6.2 FastAPI drop", (f"{float(F['2026-02-01']['vuong_z']):.2f}", f"{float(F['2026-03-01']['vuong_z']):.2f}",
      int(F["2026-02-01"]["n_files"]) - int(F["2026-03-01"]["n_files"]), F["2026-03-01"]["is_post"]),
      ("9.32", "7.24", 134, "True"), ["FastAPI's $$z_{lr}$$ fell from 9.32 to 7.24", "134 Python files fewer"])
check("6.1 FastAPI step", f"{float(F['2025-02-01']['gini']) - float(F['2025-01-01']['gini']):+.3f}", "+0.033",
      "a step of +0.033 between the January and February 2025 snapshots")

# Table 6.2 (change-points)
t62 = {}
for m in re.finditer(r"^\| (\w+)\s*\| (\d{4}-\d\d-\d\d), ([+-]\d+) d, (up|down)\s*\| (\d{4}-\d\d-\d\d), ([+-]\d+) d, (up|down)\s*\| "
                     r"(\d{4}-\d\d-\d\d), ([+-]\d+) d, (up|down)\s*\|$", TEXT, re.M):
    g = m.groups()
    t62[g[0].lower()] = [(g[1], int(g[2]), g[3]), (g[4], int(g[5]), g[6]), (g[7], int(g[8]), g[9])]
check("Table 6.2 rows", sorted(t62), sorted(PILOT))
cps = []
for k in PILOT:
    row = []
    for metric in ("gini", "delta_aic", "vuong_z"):
        dates, vals, post = load_series(ROOT / "data" / "longitudinal-v1.1" / k / "timeline.csv", metric)
        i = sliding_window_changepoint(vals)
        delta = sum(vals[i:]) / (len(vals) - i) - sum(vals[:i]) / i
        row.append((dates[i].isoformat(), (dates[i] - dates[post.index(True)]).days, "up" if delta > 0 else "down"))
    cps += [(k, mt, *c) for mt, c in zip(("gini", "delta_aic", "vuong_z"), row)]
    check(f"Table 6.2 {k}", t62.get(k), row)
after = [c for c in cps if c[3] >= 0]
check("6.3 counts", (len(cps), len(cps) - len(after), len(after),
      sorted(c[0] for c in after if c[1] == "gini" and c[4] == "up"),
      sum(c[4] == "down" for c in after if c[1] != "gini"), sum(c[4] == "up" for c in after if c[1] != "gini")),
      (24, 15, 9, ["numpy", "pandas"], 4, 3),
      ["Of the 24 change-points, 15 precede the first post-adoption snapshot", "into four decreases", "three increases"])

# E8: v1.0.0 change-points come from the sliding-window scan
v100 = {("celery", "gini"): -486, ("celery", "delta_aic"): 273, ("celery", "vuong_z"): 273,
        ("django", "gini"): -31, ("django", "delta_aic"): -31, ("django", "vuong_z"): -182}
for (k, metric), lag in v100.items():
    f = ROOT / "data" / "longitudinal" / k / "timeline.csv"
    if not f.exists():
        skip(f"E8 v1.0.0 {k} {metric}", "v1.0.0 timeline not present (gitignored)")
        continue
    dates, vals, post = load_series(f, metric)
    i = sliding_window_changepoint(vals)
    check(f"E8 v1.0.0 {k} {metric} lag via sliding window", (dates[i] - dates[post.index(True)]).days, lag)
check("ruptures not required", "ruptures" in (ROOT / "requirements.txt").read_text(), False)

# E2/E6: re-walked Celery and Django reproduce v1.0.0 timelines
for k in ("celery", "django"):
    f = ROOT / "data" / "longitudinal" / k / "timeline.csv"
    if not f.exists():
        skip(f"E2 {k} reproduction", "v1.0.0 timeline not present (gitignored)")
        continue
    a = {r["date"]: r for r in read(f)}
    b = tl(k)
    diff = [d for d in a if d not in b or any(abs(float(a[d][m]) - float(b[d][m])) > 1e-9 for m in ("gini", "delta_aic", "vuong_z"))
            or a[d]["is_post"] != b[d]["is_post"]]
    check(f"E2/E6 {k} v1.1 timeline reproduces v1.0.0", (len(a), len(b), diff), (len(a), len(a), []))

# === Clone-dependent checks: E2, E3, E6 mainline, snapshot identity ========
if not (BASE / "celery").exists() or (BASE / "celery" / ".git" / "shallow").exists():
    skip("clone checks", "full-history baseline clones not present")
else:
    celery, aiohttp = BASE / "celery", BASE / "aiohttp"
    check("E2 Celery date (fixed parser)", find_adoption_date(celery), "2025-05-09", "is dated 2025-05-09")
    lines = [ln.split(" ", 3) for ln in git(celery, "log", "--all", "--format=%ai %s %b").splitlines()]
    old_commit = sorted(p[0] for p in lines if len(p) == 4 and _COMMIT_RE.search(p[3]))
    cfg = git(celery, "log", "--all", "--diff-filter=A", "--format=%ad", "--date=short", "--", ".github/copilot-instructions.md").split()
    check("E2 v1.0.0 parser result", min(old_commit[:1] + cfg), "2025-08-26", "2025-08-26")
    fs, rs = "\x1f", "\x1e"
    day = git(celery, "log", "--all", "--since=2025-05-08T00:00", "--until=2025-05-08T23:59:59", f"--format=%s{fs}%b{rs}")
    check("E2 no attributed Celery commit on 2025-05-08", sum(1 for rec in day.split(rs) if rec.strip() and _COMMIT_RE.search(rec)), 0)
    day = git(aiohttp, "log", "--all", "--since=2026-05-04T00:00", "--until=2026-05-04T23:59:59", f"--format=%s%n%b{rs}")
    check("E3 no aiohttp commit on 2026-05-04 mentions Claude/Anthropic", bool(re.search(r"claude|anthropic", day, re.I)), False)
    check("E3 aiohttp earliest attributed / snapshot", (cont["aiohttp"]["first_attributed_all_refs"][:10], cont["aiohttp"]["snapshot_date"]),
          ("2026-05-16", "2026-05-18"), "dated 2026-05-16")
    off = 0
    for k in ("numpy", "pytest", "scrapy", "pydantic"):
        head = git(BASE / k, "rev-parse", "HEAD").strip()
        for d in tl(k):
            a = git(BASE / k, "rev-list", "-n1", f"--before={d}T23:59:59", head).strip()
            b = git(BASE / k, "rev-list", "-n1", "--first-parent", f"--before={d}T23:59:59", head).strip()
            off += a != b
        for d, r in tl(k).items():
            if r["commit"] != git(BASE / k, "rev-list", "-n1", "--first-parent", f"--before={d}T23:59:59", head).strip():
                off += 1000
    check("E6 off-mainline snapshots avoided", off, 31, "the unrestricted rule picked 31 commits")
    py = lambda c: [f for f in git(BASE / "numpy", "ls-tree", "-r", "--name-only", c, "numpy/distutils").splitlines() if f.endswith(".py")]
    moved = [ln for ln in git(BASE / "numpy", "diff", "--name-status", "-M", N["2025-12-01"]["commit"], N["2026-01-01"]["commit"]).splitlines()
             if ln.startswith("R") and "numpy/distutils/" in ln and ln.endswith(".py") and "numpy/_build_utils/" in ln]
    check("6.2 numpy/distutils removal", (len(py(N["2025-12-01"]["commit"])), len(py(N["2026-01-01"]["commit"])), len(moved)), (80, 0, 1),
          "was removed (80 Python files, one of them moved to `numpy/_build_utils`)")
    num = git(BASE / "fastapi", "diff", "--shortstat", F["2025-01-01"]["commit"], F["2025-02-01"]["commit"], "--", "*.py")
    dels = int(re.search(r"(\d+) deletion", num).group(1))
    check("6.1 FastAPI deleted lines Jan->Feb 2025", 24000 <= dels <= 26000, True, "about 25,000 lines of Python were deleted")
    P_ = tl("pydantic")
    check("Fig 6 caption: pydantic-core files added", int(P_["2025-12-01"]["n_files"]) - int(P_["2025-11-01"]["n_files"]) > 100
          and "pydantic-core" in git(BASE / "pydantic", "log", "--first-parent", "--format=%s",
                                      f"{P_['2025-11-01']['commit']}..{P_['2025-12-01']['commit']}"), True,
          "when the pydantic-core Python sources were added to the repository")
    from compute_fanin import compute_fanin
    diff = [p.name for p in sorted(BASE.iterdir())
            if compute_fanin(p) != json.loads((ROOT / "data" / "results" / "baseline" / f"{p.name}.json").read_text())]
    check("fan-in at HEAD equals stored results", diff, [], "reproduces the stored per-file results exactly")

# === Round-3 coverage: recipe, eligibility details, captions, 7.4, 7.7 =====
T51_SIGNAL = {m.group(1).lower(): m.group(2).strip() for m in
              re.finditer(r"^\| (\w+)\s*\| \d{4}-\d\d-\d\d\s*\| ([^|]+)\|", TEXT, re.M)}
want_sig = {k: ("commit trailer (config file from 2025-08-26)" if k == "celery" else
                "`.github/copilot-instructions.md`" if k == "django" else "commit trailer") for k in PILOT}
check("Table 5.1 first-signal column", {k: T51_SIGNAL.get(k) for k in PILOT}, want_sig)
check("Table 5.1 signals match audit", all(
    (cont[k]["config_date_at_snapshot"] == "2025-08-26" and cont[k]["first_attributed_at_snapshot"][:10] == "2025-05-09") if k == "celery" else
    (cont[k]["config_date_at_snapshot"] == cont[k]["adoption_date_at_snapshot"] and snap[k] == 0) if k == "django" else
    (not cont[k]["config_date_at_snapshot"] and cont[k]["first_attributed_at_snapshot"][:10] == cont[k]["adoption_date_at_snapshot"])
    for k in PILOT), True)
pv = {r["repo"]: r for r in prov}
check("5.1 created before 2023 and full history", all(pv[k]["first_commit_date"] < "2023-01-01" and pv[k]["shallow"] == "False" for k in PILOT), True,
      "created before 2023 (at least 24 months of pre-adoption history), full git history available")
check("5.2 pre-adoption snapshots", sorted({int(ps[k]["n_pre"]) for k in PILOT}), [24, 25], "which gives 24 or 25 pre-adoption snapshots")

ex = {r["metric"]: r for r in read(ROOT / "data" / "compare_groups_excl_contaminated.csv")}
check("exclusion CSV holds the printed exact p-values", {m: sig2(float(ex[m]["p_exact"])) for m in ex},
      {"gini": "0.027", "vuong_z": "0.014", "entropy_norm": "0.064", "delta_aic": "0.28", "frac_leaves": "0.13"},
      "Results, with exact and normal-approximation p-values, are in `data/compare_groups_excl_contaminated.csv`")
full = {r["metric"]: r for r in read(ROOT / "data" / "compare_groups_with_contaminated.csv")}
check("full-sample CSV has the z_lr row (E7)", f"{float(full['vuong_z']['p']):.4f}", "0.0073")

sizes = sorted(bl, key=lambda r: int(r["n_files"]))
check("four of five unaffected among the five smallest", sum(r["repo"] in clean for r in sizes[:5]), 4,
      "Four of the five unaffected repos are among the five smallest in Cohort A")
check("SQLAlchemy DAIC", f"{float(S['sqlalchemy']['delta_aic']):.1f}", "262.6", "SQLAlchemy, the one large unaffected repo, has DAIC 262.6")

DJ = tl("django")
dj_pre = [float(r["delta_aic"]) for r in DJ.values() if r["is_post"] == "False"]
check("6.3 Django DAIC change-point", (f"{float(ps['django']['cpdelta_delta_aic']):.1f}", f"{sum(dj_pre) / len(dj_pre):.1f}",
      f"{float(ps['django']['cpdelta_gini']):+.4f}"), ("38.7", "260.5", "+0.0004"),
      "The Gini change is negligible (+0.0004); the DAIC change is a rise of 38.7 on a pre-adoption mean of 260.5")

def steps(k):
    X = list(tl(k).values())
    return {X[i]["date"][:7]: float(X[i]["gini"]) - float(X[i - 1]["gini"]) for i in range(1, len(X)) if X[i]["is_post"] == "False"}
top = {k: max(steps(k), key=lambda d: abs(steps(k)[d])) for k in ("fastapi", "scrapy", "pydantic")}
check("Fig 6 caption: largest pre-adoption steps", top, {"fastapi": "2025-02", "scrapy": "2025-06", "pydantic": "2025-12"},
      "The large steps before adoption are FastAPI (February 2025), Scrapy (June 2025), and Pydantic")
pst = steps("pydantic")
check("Fig 6 caption: Pydantic steps", (f"{pst['2024-11']:+.3f}", f"{pst['2025-12']:+.3f}"), ("-0.027", "+0.037"),
      "a drop of 0.027 in November 2024 and a rise of 0.037 in December 2025")
C1 = tl("celery")
check("Celery detail: +40 files at the 2024-02 change-point", int(C1["2024-02-01"]["n_files"]) - int(C1["2024-01-01"]["n_files"]), 40,
      "corresponds to a test infrastructure reorganization that added 40 files")
check("abstract length and content", len(FLAT[FLAT.index("## Abstract") + 12:FLAT.index("------", FLAT.index("## Abstract"))].split()) <= 250, True,
      ["the Gini gap holds without the ten Cohort A repos carrying declared AI signals (p=0.027)",
       "the log-normal signal moves in no consistent direction"])
check("plain-language and conclusion mention E1", True, True,
      ["10 of its 15 measured snapshots carry a declared AI signal",
       "Ten of the 15 human-written repos carry declared AI signals in their measured snapshots"])
check("conclusion log-normal counts", (sum(float(ps[k]["D_delta_aic"]) < 0 for k in PILOT), sum(float(ps[k]["D_vuong_z"]) < 0 for k in PILOT)),
      (5, 3), "DAIC fell in five repos, $$z_{lr}$$ in three")

if (BASE / "celery").exists():
    check("B2: released recipe (--rev HEAD) reproduces Table 5.1", {k: find_adoption_date(BASE / k, rev="HEAD") for k in PILOT},
          {k: t51[k][0] for k in PILOT}, "`find_adoption_date.py --rev HEAD`")
    pt_all = cont["pytest"]["first_sha_all_refs"]
    check("5.1 pytest all-refs date is off the snapshot history",
          (find_adoption_date(BASE / "pytest"), subprocess.run(["git", "-C", str(BASE / "pytest"), "merge-base", "--is-ancestor", pt_all, "HEAD"]).returncode != 0),
          ("2025-04-11", True), "Scanning all refs instead would date pytest from a commit on a branch never merged into its snapshot")
    check("7.7 the 14 earlier outside commits are not in the snapshots", sum(
        subprocess.run(["git", "-C", str(BASE / h["repo"]), "merge-base", "--is-ancestor", h["sha"], "HEAD"]).returncode == 0 for h in before), 0)
    six = ["numpy", "pandas", "pytest", "fastapi", "scrapy", "pydantic"]
    check("E6: six added repos signal through commit trailers only, no config file in the snapshot",
          ([k for k in six if cont[k]["config_file_at_snapshot"]], all(snap[k] > 0 for k in six)), ([], True),
          ["declare AI assistance through commit trailers and have no AI configuration file in their snapshots",
           "so why these six were missed is unknown"])
    check("Table 5.1 'commit trailer': first signal of each trailer repo is a Co-authored-by trailer",
          [k for k in PILOT if k != "django" and "co-authored-by" not in git(BASE / k, "show", "-s", "--format=%B",
           cont[k]["first_sha_at_snapshot"]).lower()], [])
    check("7.7 aiohttp is outside the Cohort B creation window", (pv["aiohttp"]["first_commit_date"][:4], cont["aiohttp"]["config_file_at_snapshot"]),
          ("2013", "CLAUDE.md"), ["Cohort B requires creation in 2024-2026, and aiohttp's first commit dates from 2013",
                                   "22 Python repositories created 2024-2026"])
    since = {k: sum(1 for d in git(BASE / k, "log", "HEAD", "--format=%ad", "--date=short").split() if d >= cont[k]["adoption_date_at_snapshot"]) for k in PILOT}
    att = {k: sum(1 for h in hits if h["repo"] == k and h["at_snapshot"] == "True" and h["date"][:10] >= cont[k]["adoption_date_at_snapshot"]) for k in PILOT}
    shares = {k: 100 * att[k] / since[k] for k in PILOT}
    check("7.4(b) post-adoption AI shares", (f"{min(shares.values()):.0f}%", min(shares, key=shares.get), f"{max(shares.values()):.1f}%",
          max(shares, key=shares.get), att["pandas"], since["pandas"], f"{float(ps['pandas']['D']):+.4f}"),
          ("0%", "django", "32.5%", "pandas", 386, 1188, "+0.0009"),
          "between 0% (Django) and 32.5% (pandas, 386 of 1,188 commits by author date)")
    F2 = tl("fastapi")
    ns = git(BASE / "fastapi", "diff", "--name-status", F2["2026-02-01"]["commit"], F2["2026-03-01"]["commit"], "--", "*.py").splitlines()
    moved = [ln for ln in ns if ln[0] in "DR"]
    check("6.2 FastAPI change is a docs-example reorganization (>=95% of removed/renamed files in docs_src)",
          sum("docs_src/" in ln for ln in moved) / len(moved) >= 0.95, True, "after a reorganization of its documentation examples")
else:
    skip("round-3 clone checks", "baseline clones not present")

# === README, .zenodo.json, DOIs, placeholders ==============================
check("README repeats audit and pilot numbers", True, True,
      ["421 of 221,145", "0.912", "0.845", "p=0.027", "p=0.014", "846 made later, 14 on unmerged branches",
       "median 83 Python files against 428", "Gini rose in 6 of 8 repos", "p=0.195", "p=0.945",
       "The Conclusion's z_lr p-value is 0.0073", "0% to 32.5% of each repo's commits (pandas is highest)",
       "10 repos with an AI signal excluded", "--rev HEAD --verbose",
       "number in the Version Note, Sections 5 and 6, and Section 7.7"], where=README)
check("README has no stale PELT claim", "PELT change-point detection" in README, False)
check("README exclusion command matches", True, True, "--exclude-repos " + ",".join(affected), where=README)
zd = re.sub(r"\s+", " ", ZENODO["description"])
check(".zenodo.json repeats numbers", True, True, ["421 of 221,145", "p=0.027", "p=0.195", "corrects eight errors", "a tenth, Django, has an AI configuration file"], where=zd)
check("DOIs", True, True, ["paper doi: 10.5281/zenodo.20313669", "code and data doi: 10.5281/zenodo.20318458",
                           "all versions: doi: 10.5281/zenodo.20318457", "Paper, all versions: doi: 10.5281/zenodo.20313668"])
nc = {r["repo"]: r for r in read(ROOT / "data" / "repos" / "provenance.csv")}["NewsCrawler"]
check("3.1 NewsCrawler: human commits before first AI signal", (nc["first_commit_date"], nc["adoption_date_at_snapshot"]),
      ("2024-11-07", "2025-10-15"), ["NewsCrawler, for example, has its first commit on 2024-11-07 and its first AI signal on 2025-10-15",
                                     "v1.1 describes them that way"])
check("no unresolved [AUTHOR ...] placeholders", re.findall(r"\[AUTHOR[^\]]*\]", TEXT), [])
check("figures referenced exist", [f for f in re.findall(r"\]\(\.\./(figures/[^)]+)\)", TEXT) if not (ROOT / f).exists()], [])

print(f"\n{results['PASS']} passed, {results['FAIL']} failed, {results['SKIP']} skipped")
allow_skip = "--allow-skip" in sys.argv
sys.exit(1 if results["FAIL"] else (2 if results["SKIP"] and not allow_skip else 0))
