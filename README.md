# parabolic-fractal

Code and data for the preprint:

**"Fan-In Distributions in Human-Written vs AI-Generated Python Codebases: A Constructal Law Analysis"**

---

## Key findings

Import fan-in measures how many other files in a repo import a given file. We computed
it across 27 Python repos with sufficient coupling for distribution fitting (15
baseline + 12 agentic), drawn from 37 cloned repos total.

| Group | n (fitted) | Gini mean | LN wins | Vuong z mean |
|-------|----------:|----------:|--------:|-------------:|
| Baseline (human-written OSS) | 15 | 0.882 | 14/15 | 6.00 |
| Agentic (AI-generated, 2024-2026) | 12 | 0.725 | 11/12 | 2.77 |

Mann-Whitney U between groups:

| Metric | p | rank-biserial r |
|--------|---|----------------|
| Gini | 0.0011 | −0.744 |
| Delta AIC (log-normal advantage) | 0.019 | −0.533 |
| Normalized entropy | 0.002 | +0.711 |
| Fraction leaf files | 0.015 | −0.556 |

Of 22 agentic repos cloned, 10 could not be fitted (3 had zero intra-repo coupling,
4 had fewer than 10 connected files, 1 too small, 1 had no Python files, 1 checkout
failure). The exclusions strengthen the finding: the most degenerate repos are below
the measurement threshold, not in it.

---

## Longitudinal study

**Companion paper:** `paper/dyb-2026q-AI-Python-constructal-v1.1-REL.md` (v1.0.0 kept as `-v1-REL`)

The cross-sectional design cannot rule out that AI repos and human repos differ on
confounds (age, size, contributors). The longitudinal study tracks the same repos
before and after documented AI adoption to remove those confounds.

**Repos studied:** Celery (declared attribution 2025-05-09; v1.0.0 of the paper
gave 2025-05-08, which no commit supports, see "Data validity" below; 37 monthly
snapshots: 25 pre + 12 post) and Django (declared attribution 2026-03-05, 27
snapshots: 25 pre + 2 post). Dates come from AI attribution trailers in commit
messages and from AI config files appearing in history. They mark *declared*
attribution. Tool use without a declared marker is invisible to this method.

**Finding:** The agentic flattening hypothesis is rejected for mature repos. In
Celery, Gini increased post-adoption (last-6-pre mean 0.8664, first-6-post mean
0.8680, Wilcoxon p=0.031) and the log-normal signal strengthened. In Django, Gini
is unchanged (0.9327 vs. 0.9332, 2 months of post data).

**Interpretation:** The flattening effect is a structural genesis problem, not a
maintenance problem. AI agents produce flat topology when designing a codebase from
scratch, where no prior import hierarchy constrains them. When contributing to an
established codebase, they follow the existing structure and leave the topology
intact. The structural risk of AI coding is concentrated at project inception.

---

## Data validity: post-release audit (paper v1.1)

Version 1.1 of the paper (`paper/dyb-2026q-AI-Python-constructal-v1.1-REL.md`)
opens with a Version Note listing five corrections to v1.0.0 and adds Section 7.7.
No conclusion changes. `python scripts/check_paper_claims.py` recomputes every number
cited there and exits nonzero on any mismatch.

**Cohort A contains a few AI-attributed commits.** The baseline repos were chosen as
projects founded and maintained by people before AI coding tools existed. Scanning
every commit in the 15 snapshots whose fan-in the paper measures finds 421 of
221,145 (0.19%) with a declared AI attribution, in 9 repos:

| Repo | Attributed / commits at snapshot |
|------|---------------------------------:|
| pandas | 386 / 38,026 |
| numpy | 12 / 41,216 |
| pytest | 9 / 17,342 |
| celery | 8 / 13,092 |
| fastapi | 2 / 7,156 |
| aiohttp, pydantic, requests, scrapy | 1 each |
| django, sqlalchemy, flask, click, httpx, tornado | 0 |

379 of the pandas commits come from one contributor. History fetched later, up to
September 2026, adds 860 more (including 33 in Tornado); those postdate the
snapshots and enter no result. The affected repos have a higher median Gini (0.906)
than the unaffected ones (0.855), and removing them leaves Cohort A Gini above
Cohort B Gini (exact Mann-Whitney p=0.0097, n=6 vs. 12) with the same effect size.
Data: `data/contamination-baseline.csv`, `data/attributed-commits-baseline.csv`,
`data/compare_groups_excl_contaminated.csv`; figures in `figures/v1.1/`.

**Other corrections in v1.1.** Celery's adoption date is 2025-05-09, not 2025-05-08;
the v1.0.0 date parser missed trailers in commit bodies and is fixed. No aiohttp
commit on 2026-05-04, the date v1.0.0 cites, mentions Claude; the first attributed
commit is 2026-05-16. Change-point
lags are measured from the first post-adoption monthly snapshot, which fixes two
Django rows (-31 days, not -4). Figures 2 to 4 of v1.0.0 predated the second wave of
agentic repos and are redrawn.

**What the detector measures.** An adoption date here is the date of the first
*declared* AI attribution: a commit trailer or an AI config file. AI use that leaves
no such marker cannot be detected from repository history. On 1,275 sampled commits
an LLM classifier reading the same messages (Jev, `typesafe/jev-1.13`) flagged the
same 116 as the regex (`data/trials/`), so the regex is used alone.

---

## Repo layout

```
scripts/
  collect_repos.py          clone baseline + agentic repos
  compute_fanin.py          compute intra-repo import fan-in per file
  fit_distributions.py      fit log-normal vs power-law, compute Gini/entropy
  compare_groups.py         Mann-Whitney U between groups
  plot_contamination.py     v1.1 Figures 6 and 7 (post-release audit)
  check_paper_claims.py     executable gate for every number in paper v1.1 errata and 7.7
  longitudinal/
    find_adoption_date.py   detect declared-AI-attribution date from git history
    walk_history.py         monthly snapshots pre/post declared attribution
    aggregate_timeline.py   compile snapshots into timeline CSV
    detect_changepoint.py   PELT change-point detection on metric time series
    plot_timeline.py        per-repo and aggregate timeline figures
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
  compare_groups_excl_contaminated.csv  Mann-Whitney, 9 repos with attributed commits excluded
  trials/                   regex-vs-Jev validation raw data (see "Data validity")
  longitudinal/             snapshot JSONs and timeline CSVs (gitignored)

paper/
  dyb-2026q-AI-Python-constructal-v1-REL.md   v1.0.0 release paper, unchanged
  dyb-2026q-AI-Python-constructal-v1.1-REL.md v1.1: errata + post-release audit (Section 7.7)
  dyb-2026q-AI-Python-constructal-v1-REL.pdf   PDF version

figures/
  fig[1-4]_*.png            cross-sectional figures as published in v1.0.0
  v1.1/                     all figures for paper v1.1 (Figs 1-4 redrawn, new Figs 6-7)
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

### Longitudinal study

Requires full (non-shallow) clones and the `ruptures` package for PELT.

```bash
# full clone a candidate repo
git clone https://github.com/celery/celery.git data/repos/longitudinal/celery

# detect declared-attribution date
python scripts/longitudinal/find_adoption_date.py --repo data/repos/longitudinal/celery --verbose

# walk history (edit date to match)
python scripts/longitudinal/walk_history.py \
    --repo data/repos/longitudinal/celery \
    --adoption-date 2025-05-09 \
    --out-dir data/longitudinal \
    --pre-months 24 --post-months 12

# aggregate metrics
python scripts/longitudinal/aggregate_timeline.py \
    --repo-dir data/longitudinal/celery \
    --out data/longitudinal/celery/timeline.csv

# change-point detection
python scripts/longitudinal/detect_changepoint.py --timeline data/longitudinal/celery/timeline.csv

# figures
python scripts/longitudinal/plot_timeline.py \
    --longitudinal-dir data/longitudinal \
    --out-dir figures/longitudinal
```

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
    --exclude-repos aiohttp,celery,fastapi,numpy,pandas,pydantic,pytest,requests,scrapy \
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
mainstream human-maintained OSS projects predating the agentic-coding era; 10 of the
15 contain a small number of individually AI-attributed commits (see "Data
validity" above).

**Agentic (22 repos cloned, 12 fitted):** Python repositories created 2024-2026 with
explicit AI authorship signals — CLAUDE.md, `.cursor/rules`, README self-attribution,
or `Co-authored-by: Cursor` / `noreply@anthropic.com` commit trailers. Repos are
functional applications built by AI agents, not AI tooling frameworks.

---

## Citation

```
Bilar, Daniyel Yaacov (2026). Fan-In Distributions in Human-Written vs AI-Generated
Python Codebases: A Constructal Law Analysis. Chokmah LLC.
https://doi.org/10.5281/zenodo.20318458
https://github.com/chokmah-me/parabolic-fractal
```
