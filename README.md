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

**Companion paper:** `paper/longitudinal-draft.md`

The cross-sectional design cannot rule out that AI repos and human repos differ on
confounds (age, size, contributors). The longitudinal study tracks the same repos
before and after documented AI adoption to remove those confounds.

**Repos studied:** Celery (adoption 2025-05-08, 37 monthly snapshots: 25 pre + 12
post) and Django (adoption 2026-03-05, 27 snapshots: 25 pre + 2 post). Adoption
dates are detected automatically from commit-level AI attribution and AI config
file appearance, then verified manually.

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

## Repo layout

```
scripts/
  collect_repos.py          clone baseline + agentic repos
  compute_fanin.py          compute intra-repo import fan-in per file
  fit_distributions.py      fit log-normal vs power-law, compute Gini/entropy
  compare_groups.py         Mann-Whitney U between groups
  longitudinal/
    find_adoption_date.py   detect AI adoption date from git history
    walk_history.py         monthly snapshots pre/post adoption
    aggregate_timeline.py   compile snapshots into timeline CSV
    detect_changepoint.py   PELT change-point detection on metric time series
    plot_timeline.py        per-repo and aggregate timeline figures

data/
  repos/baseline/           cloned human-written repos
  repos/agentic/            cloned agentic repos
  results/baseline/         per-repo fan-in JSON
  results/agentic/          per-repo fan-in JSON
  summary.csv               all metrics, one row per repo
  longitudinal/             snapshot JSONs and timeline CSVs (gitignored)

paper/
  draft.md                  cross-sectional paper
  longitudinal-draft.md     longitudinal companion paper

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

# detect adoption date
python scripts/longitudinal/find_adoption_date.py --repo data/repos/longitudinal/celery --verbose

# walk history (edit adoption date to match)
python scripts/longitudinal/walk_history.py \
    --repo data/repos/longitudinal/celery \
    --adoption-date 2025-05-08 \
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

---

## Cohorts

**Baseline (15 repos):** Django, Flask, NumPy, pandas, SQLAlchemy, Celery, FastAPI,
requests, pytest, Scrapy, httpx, Pydantic, aiohttp, Tornado, Click.

**Agentic (22 repos cloned, 12 fitted):** Python repositories created 2024-2026 with
explicit AI authorship signals — CLAUDE.md, `.cursor/rules`, README self-attribution,
or `Co-authored-by: Cursor` / `noreply@anthropic.com` commit trailers. Repos are
functional applications built by AI agents, not AI tooling frameworks.

---

## Citation

Preprint forthcoming. In the meantime:

```
Bilar, D.Y. (2026). Fan-In Distributions in Human-Written vs AI-Generated Python
Codebases: A Constructal Law Analysis. [preprint]
```
