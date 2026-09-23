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

**Repos studied:** Celery (declared attribution 2025-05-09, corrected from 2025-05-08
after a parser bug fix — see "Data validity" below; 37 monthly snapshots: 25 pre + 12
post) and Django (declared attribution 2026-03-05, 27 snapshots: 25 pre + 2
post). Dates are detected automatically from commit-level AI attribution trailers and
AI config file appearance, then verified manually. This measures *declared*
attribution, not tool adoption itself — see "Data validity" below.

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

A post-release audit found that the baseline group is **not commit-level pure
human-written**, even though every baseline repo predates its cloned snapshot and
was selected as a mainstream human-maintained OSS project. Full history was scanned
with the same regex `find_adoption_date.py` uses (see `scripts/longitudinal/
audit_contamination.py`, run: `python scripts/longitudinal/audit_contamination.py`):

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

10 of 15 baseline repos contain at least one commit with a declared AI-attribution
trailer (e.g. `Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>`). Full data:
`data/contamination-baseline.csv`; per-repo clone provenance (all 37 repos, remote
URL, commit count, shallow status): `data/repos/provenance.csv`.

**What this does and doesn't mean.** A repo-level "baseline = human-written" split
does not imply commit-level purity — a handful of AI-assisted commits landing in an
otherwise human-maintained, decades-old project does not make that project
"agentic" by the same criteria used to build the agentic cohort (which requires
functional applications *built* by AI agents from inception). The cross-sectional
comparison above should be read as a secondary, contamination-flagged result. The
**primary evidence for the AI-topology question is the longitudinal within-repo
design** (Celery, Django): it compares each repo against itself before/after its own
declared-attribution date, so occasional attributed commits elsewhere in the corpus
don't confound it.

Re-running `compare_groups.py` with the 10 contaminated repos excluded
(`data/compare_groups_excl_contaminated.csv`, n=5 baseline) shows the same
direction as the full 15-repo comparison (`data/compare_groups_with_contaminated.csv`)
on Gini and entropy, but loses significance on delta-AIC and fraction-leaf-files —
expected at n=5. The conclusion's direction does not move; its significance on two
of four metrics is not robust to the exclusion, which is itself the result: sample
size, not contamination, is the binding constraint on those two metrics.

**Parser bug fix.** `find_adoption_date.py`'s commit scanner previously only tested
each commit's first output line against the attribution regex, so trailers placed
later in a multi-line commit body (the normal position) were invisible to it. Fixed
to use NUL-safe field separators (same approach as `audit_contamination.py`).
Re-running on full history moved Celery's declared-attribution date by one day
(2025-05-08 → 2025-05-09, the bug had missed an earlier commit); Django is
unchanged. This doesn't change any monthly snapshot boundary in `walk_history.py`,
so the longitudinal results in the paper are unaffected — a confirmed non-movement.

**Construct note.** `find_adoption_date.py` detects *declared* AI attribution (a
literal trailer or marker in the commit message), not tool adoption itself. A
validation pass comparing this regex against a semantic LLM judge (Jev,
`typesafe/jev-1.13`) over 1,275 sampled real commits found 0 disagreements (all raw
data in `data/trials/`) — i.e., in that sample, no commit used AI tooling without
also declaring it. That result supports using the regex alone (no semantic
classifier needed) for the declared signal; it is not evidence that undeclared
("silent") adoption doesn't happen elsewhere in either cohort. Silent adoption is
out of scope for this project.

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
15 contain a minority of individually AI-attributed commits (see "Data validity"
above) — repo-level "baseline" does not mean commit-level purity.

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
