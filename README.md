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

**Companion paper:** `paper/dyb-2026q-AI-Python-constructal-v1-REL.md`

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

## Data validity: declared-attribution audit (2026-09-22)

The baseline repos were chosen as projects founded and maintained by people before
AI coding tools existed. That does not make every commit in them free of AI help.
A scan of the full history of all 15, using the regex from `find_adoption_date.py`
(`python scripts/longitudinal/audit_contamination.py`), finds 1,281 commits with a
declared AI attribution out of 226,849 scanned (0.56%), all dated 2025-04-11 or
later:

| Repo | Commits scanned | Attributed commits |
|------|----------------:|--------------------:|
| pandas | 39,081 | 1,067 |
| pytest | 17,781 | 132 |
| tornado | 5,133 | 33 |
| numpy | 42,167 | 24 |
| pydantic | 5,746 | 4 |
| scrapy | 11,511 | 5 |
| celery | 13,332 | 9 |
| fastapi | 7,713 | 3 |
| aiohttp | 14,164 | 3 |
| requests | 6,495 | 1 |
| django, flask, httpx, click, sqlalchemy | (full history) | 0 |

The counts are concentrated in a few contributors: 1,033 of the 1,067 in pandas come
from one person, and all 33 in Tornado are authored under the name "Claude". None
are Dependabot bumps or backport copies. Per-repo counts:
`data/contamination-baseline.csv`. Clone provenance for all 37 repos (remote URL,
commit count, shallow status): `data/repos/provenance.csv`.

**Consequence for the analysis.** The cross-sectional baseline-vs-agentic
comparison is now reported as secondary evidence. The within-repo longitudinal
design (Celery, Django) is primary: it compares each repo with its own history
before its declared-attribution date, so attributed commits elsewhere in the corpus
do not enter it. With the 10 affected repos excluded (n=5 baseline,
`data/compare_groups_excl_contaminated.csv`), baseline Gini stays higher than
agentic Gini (p=0.015) and normalized entropy stays lower (p=0.035). The delta-AIC
and leaf-fraction differences lose significance at n=5 (p=0.14 and p=0.11). The
full 15-repo result is in `data/compare_groups_with_contaminated.csv`.

**Date corrections.** v1.0.0 of the paper gave Celery's date as 2025-05-08. No
Celery commit on that date carries an attribution marker; the earliest is 5c1a13c,
2025-05-09. The v1.0.0 script could not reproduce either date: its commit parser
tested only the first line of each log entry, so it missed `Co-authored-by:`
trailers in commit bodies and returned the config-file date 2025-08-26. The parser
now reads whole messages. Both 2025-05-08 and 2025-05-09 fall between the
2025-05-01 and 2025-06-01 monthly snapshots, so no pre/post label and no computed
longitudinal result changes. v1.0.0 also cited an aiohttp commit on 2026-05-04; no
aiohttp commit on that date mentions Claude or Anthropic, and the earliest
attributed one is 2026-05-16. aiohttp was excluded from the longitudinal study in
v1.0.0 and remains excluded.

**What the detector measures.** `find_adoption_date.py` finds *declared* AI
attribution: a literal trailer in a commit message or an AI config file in the
tree. In a sample of 1,275 commits (1,028 baseline, 247 agentic), the regex and an
LLM classifier reading the same messages (Jev, `typesafe/jev-1.13`) flagged the same
116 commits (raw data in `data/trials/`). So the classifier found no attribution
signal in the messages that the regex missed, and the regex alone is used. Neither
detector can see AI tool use that leaves no trace in the message; that is out of
scope for this project.

---

## Repo layout

```
scripts/
  collect_repos.py          clone baseline + agentic repos
  compute_fanin.py          compute intra-repo import fan-in per file
  fit_distributions.py      fit log-normal vs power-law, compute Gini/entropy
  compare_groups.py         Mann-Whitney U between groups
  longitudinal/
    find_adoption_date.py   detect declared-AI-attribution date from git history
    walk_history.py         monthly snapshots pre/post declared attribution
    aggregate_timeline.py   compile snapshots into timeline CSV
    detect_changepoint.py   PELT change-point detection on metric time series
    plot_timeline.py        per-repo and aggregate timeline figures
    audit_contamination.py  full-history contamination + provenance audit

data/
  repos/baseline/           cloned human-written repos
  repos/agentic/            cloned agentic repos
  repos/provenance.csv      per-repo remote/commit-count/shallow/attribution audit
  results/baseline/         per-repo fan-in JSON
  results/agentic/          per-repo fan-in JSON
  summary.csv               all metrics, one row per repo
  contamination-baseline.csv  full-history AI-attribution scan of baseline repos
  compare_groups_with_contaminated.csv  Mann-Whitney, all 15 baseline repos
  compare_groups_excl_contaminated.csv  Mann-Whitney, 10 contaminated repos excluded
  trials/                   regex-vs-Jev validation raw data (see "Data validity")
  longitudinal/             snapshot JSONs and timeline CSVs (gitignored)

paper/
  dyb-2026q-AI-Python-constructal-v1-REL.md   release paper (cross-sectional + longitudinal pilot)
  dyb-2026q-AI-Python-constructal-v1-REL.pdf   PDF version

figures/
  fig[1-4]_*.png            cross-sectional figures
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
# scan all baseline + agentic repos for declared AI attribution across full history
python scripts/longitudinal/audit_contamination.py
#   -> data/contamination-baseline.csv, data/repos/provenance.csv

# compare groups with vs. without contaminated baseline repos
python scripts/compare_groups.py --summary data/summary.csv \
    --out data/compare_groups_with_contaminated.csv
python scripts/compare_groups.py --summary data/summary.csv \
    --exclude-repos aiohttp,celery,fastapi,numpy,pandas,pydantic,pytest,requests,scrapy,tornado \
    --out data/compare_groups_excl_contaminated.csv
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
