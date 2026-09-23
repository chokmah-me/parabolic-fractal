# parabolic-fractal

Code and data for the preprint:

**"Fan-In Distributions in Human-Written vs AI-Generated Python Codebases: A Constructal Law Analysis"**

---

## Key findings

Import fan-in measures how many other files in a repo import a given file. We computed
it across 27 Python repos with sufficient coupling for distribution fitting (15
baseline + 12 agentic), drawn from 37 cloned repos total.

| Group | n (fitted) | Gini mean | LN wins | z_lr mean |
|-------|----------:|----------:|--------:|-------------:|
| Baseline (human-written OSS) | 15 | 0.882 | 14/15 | 6.00 |
| Agentic (AI-generated, 2024-2026) | 12 | 0.725 | 11/12 | 2.77 |

Mann-Whitney U between groups:

| Metric | p | rank-biserial r |
|--------|---|----------------|
| Gini | 0.0011 | -0.744 |
| Delta AIC (log-normal advantage) | 0.019 | -0.533 |
| Normalized entropy | 0.002 | +0.711 |
| Fraction leaf files | 0.015 | -0.556 |

Of 22 agentic repos cloned, 10 could not be fitted (3 had zero intra-repo coupling,
4 had fewer than 10 connected files, 1 too small, 1 had no Python files, 1 checkout
failure). The exclusions strengthen the finding: the most degenerate repos are below
the measurement threshold, not in it.

---

## Longitudinal study

**Companion paper:** `paper/dyb-2026q-AI-Python-constructal-v1.1-REL.md` (v1.0.0 kept as `-v1-REL`)

The cross-sectional design cannot rule out that AI repos and human repos differ on
confounds (age, size, contributors). The longitudinal pilot tracks the same repos
monthly before and after their declared AI adoption.

**Repos studied (v1.1):** the eight Cohort A repos that meet the pilot's inclusion
criteria: Celery (adoption 2025-05-09), NumPy (2025-10-10), pandas (2025-12-14),
pytest (2026-01-17), FastAPI (2026-02-17), Scrapy (2026-02-20), Django (2026-03-05),
and Pydantic (2026-03-08), with 2 to 12 post-adoption months each. v1.0.0 studied only
Celery and Django; with full history scanned, six more qualify.

**Finding:** no Gini decline after adoption. Gini rose in 6 of 8 repos (pooled exact
Wilcoxon p=0.195; p=0.945 after removing each repo's pre-adoption trend). The
log-normal signal shows no consistent direction either; NumPy and FastAPI drop, in
months when large sets of files were removed.

**Interpretation:** with no matched control group and short post-adoption windows, the
pilot cannot distinguish a structural-genesis explanation (AI flattening confined to
new projects) from a null effect of AI adoption on mature codebases. Since adoption,
declared AI commits make up 0% to 32.5% of each repo's commits (pandas is highest),
and pandas shows no Gini decline.

---

## Data validity: post-release audit (paper v1.1)

Version 1.1 of the paper opens with a Version Note listing eight corrections to
v1.0.0 and adds Section 7.7. `python scripts/check_paper_claims.py` recomputes every
number in the Version Note, Sections 5 and 6, and Section 7.7 and exits nonzero on
any mismatch.

**Cohort A contains AI signals.** The baseline repos were chosen as projects founded
and maintained by people before AI coding tools existed. In the 15 snapshots whose
fan-in the paper measures, 421 of 221,145 commits (0.19%) carry a declared AI
attribution, in 9 repos, and Django's snapshot adds an AI config file:

| Repo | Attributed / commits at snapshot | AI config file |
|------|---------------------------------:|----------------|
| pandas | 386 / 38,026 | |
| numpy | 12 / 41,216 | |
| pytest | 9 / 17,342 | |
| celery | 8 / 13,092 | `.github/copilot-instructions.md` |
| fastapi | 2 / 7,156 | |
| aiohttp, pydantic, requests, scrapy | 1 each | aiohttp: `CLAUDE.md` |
| django | 0 / 34,597 | `.github/copilot-instructions.md` (2026-03-05) |
| sqlalchemy, flask, click, httpx, tornado | 0 | |

379 of the pandas commits come from one contributor. The history fetched in
September 2026 holds 860 more attributed commits outside the snapshots (846 made
later, 14 on unmerged branches); none enters a result. The ten affected repos have a
higher median Gini (0.912) than the five unaffected ones (0.845). With the ten
removed, Cohort A Gini stays above Cohort B Gini (exact Mann-Whitney p=0.027,
r=-0.70) and so does z_lr (p=0.014); entropy, Delta AIC and leaf fraction lose
significance. The five unaffected repos are small (median 83 Python files against
428), and Delta AIC grows with repo size.

**Other corrections.** Celery's adoption date is 2025-05-09, not 2025-05-08, and no
aiohttp commit on 2026-05-04 mentions Claude. Change-point lags are measured from the
first post-adoption monthly snapshot (two Django lags are -31 days, not -4), and the
change-points come from a sliding-window mean-difference scan, not PELT. Figures 2
to 4 of v1.0.0 predated the second wave of agentic repos and are redrawn. The
Conclusion's z_lr p-value is 0.0073, not 0.019.

**What the detector measures.** An adoption date here is the date of the first
*declared* AI attribution: a commit trailer or an AI config file. AI use that leaves
no such marker cannot be detected from repository history. On 1,275 sampled commits
an LLM classifier reading the same messages (Jev, `typesafe/jev-1.13`) flagged the
same 116 as the regex (`data/trials/`); only one of the 116 is from Cohort A.

---

## Repo layout

```
scripts/
  collect_repos.py          clone baseline + agentic repos
  compute_fanin.py          compute intra-repo import fan-in per file
  fit_distributions.py      fit log-normal vs power-law, compute Gini/entropy
  compare_groups.py         Mann-Whitney U between groups
  plot_contamination.py     v1.1 Figures 7 and 8 (post-release audit)
  check_paper_claims.py     executable gate for every number in paper v1.1 errata and 7.7
  longitudinal/
    find_adoption_date.py   detect declared-AI-attribution date from git history
    walk_history.py         monthly snapshots pre/post declared attribution
    aggregate_timeline.py   compile snapshots into timeline CSV
    detect_changepoint.py   single change-point scan (PELT only if ruptures is installed)
    plot_timeline.py        per-repo and aggregate timeline figures
    pilot_summary.py        v1.1 pilot tables: per-repo and pooled tests, change-points
    plot_pilot.py           v1.1 Figure 6
    audit_contamination.py  attributed-commit audit (at snapshot and all refs) + provenance

data/
  repos/baseline/           cloned human-written repos
  repos/agentic/            cloned agentic repos
  repos/provenance.csv      per-repo remote/commit-count/shallow/attribution audit
  results/baseline/         per-repo fan-in JSON
  results/agentic/          per-repo fan-in JSON
  summary.csv               all metrics, one row per repo
  contamination-baseline.csv  attributed-commit counts per baseline repo, two scopes
  attributed-commits-baseline.csv  every attributed commit, flagged if in the snapshot
  compare_groups_with_contaminated.csv  Mann-Whitney, all 15 baseline repos
  compare_groups_excl_contaminated.csv  Mann-Whitney, 10 repos with an AI signal excluded
  trials/                   regex-vs-Jev validation raw data (see "Data validity")
  longitudinal/             v1.0.0 timeline CSVs (per-snapshot JSONs gitignored)
  longitudinal-v1.1/        v1.1 pilot: timeline.csv per repo, pilot_summary.csv

paper/
  dyb-2026q-AI-Python-constructal-v1-REL.md   v1.0.0 release paper, unchanged
  dyb-2026q-AI-Python-constructal-v1-REL.pdf   v1.0.0 PDF
  dyb-2026q-AI-Python-constructal-v1.1-REL.md v1.1: errata, 8-repo pilot, post-release audit
  dyb-2026q-AI-Python-constructal-v1.1-REL.pdf v1.1 PDF

figures/
  fig[1-4]_*.png            cross-sectional figures as published in v1.0.0
  v1.1/                     all figures for paper v1.1 (Figs 1-4 redrawn, new Figs 6-8)
  longitudinal/             per-repo and aggregate timeline plots
```

---

## Reproduce

### Cross-sectional study

```bash
pip install -r requirements.txt

python scripts/collect_repos.py --group all
python scripts/compute_fanin.py --repo-dir data/repos/baseline --out-dir data/results/baseline
python scripts/compute_fanin.py --repo-dir data/repos/agentic  --out-dir data/results/agentic
python scripts/fit_distributions.py --results-dir data/results --out data/summary.csv
python scripts/compare_groups.py --summary data/summary.csv
```

### Longitudinal study (v1.1 pilot)

Requires full (non-shallow) clones in `data/repos/baseline/` (see the audit below).

```bash
# declared-attribution date, from the history of the clone's HEAD (the snapshot)
python scripts/longitudinal/find_adoption_date.py --repo data/repos/baseline/celery --rev HEAD --verbose

# monthly mainline snapshots, 24 months before to 12 after, ending at the snapshot
python scripts/longitudinal/walk_history.py     --repo data/repos/baseline/celery --adoption-date 2025-05-09     --out-dir data/longitudinal-v1.1 --pre-months 24 --post-months 12     --end-date 2026-05-13
python scripts/longitudinal/aggregate_timeline.py --repo-dir data/longitudinal-v1.1/celery

# after all eight repos: per-repo and pooled tests, change-points, Figure 6
python scripts/longitudinal/pilot_summary.py
python scripts/longitudinal/plot_pilot.py
```

Dates and end dates for all eight repos are in the paper's Table 5.1 and
`data/contamination-baseline.csv` (`adoption_date_at_snapshot`, `snapshot_date`).

### Data-validity audit (baseline contamination)

```bash
# count declared-AI-attributed commits at each snapshot (HEAD) and on all refs
python scripts/longitudinal/audit_contamination.py
#   -> data/contamination-baseline.csv, data/attributed-commits-baseline.csv,
#      data/repos/provenance.csv

# compare groups with vs. without contaminated baseline repos
python scripts/compare_groups.py --summary data/summary.csv \
    --out data/compare_groups_with_contaminated.csv
python scripts/compare_groups.py --summary data/summary.csv \
    --exclude-repos aiohttp,celery,django,fastapi,numpy,pandas,pydantic,pytest,requests,scrapy \
    --out data/compare_groups_excl_contaminated.csv

# figures for paper v1.1, then the claims gate (exit 0 = every cited number verified)
python scripts/visualize.py --results-dir data/results --summary data/summary.csv --out-dir figures/v1.1
python scripts/plot_contamination.py
python scripts/check_paper_claims.py
```

---

## Cohorts

**Baseline (15 repos):** Django, Flask, NumPy, pandas, SQLAlchemy, Celery, FastAPI,
requests, pytest, Scrapy, httpx, Pydantic, aiohttp, Tornado, Click. Selected as
mainstream human-maintained OSS projects predating the agentic-coding era. In 10 of
the 15, the measured snapshot contains a declared AI signal (see "Data validity"
above).

**Agentic (22 repos cloned, 12 fitted):** Python repositories created 2024-2026 with
explicit AI authorship signals: CLAUDE.md, `.cursor/rules`, README self-attribution,
or `Co-authored-by: Cursor` / `noreply@anthropic.com` commit trailers. Repos are
functional applications with declared AI assistance, not AI tooling frameworks.

---

## Citation

```
Bilar, Daniyel Yaacov (2026). Fan-In Distributions in Human-Written vs AI-Generated
Python Codebases: A Constructal Law Analysis. Chokmah LLC. Version 1.1.
Paper (all versions): https://doi.org/10.5281/zenodo.20313668
Code and data (all versions): https://doi.org/10.5281/zenodo.20318457
https://github.com/chokmah-me/parabolic-fractal
```
