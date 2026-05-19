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
failure). The exclusions strengthen the finding — the most degenerate repos are below
the measurement threshold, not in it.

---

## Repo layout

```
scripts/
  collect_repos.py       clone baseline + agentic repos
  compute_fanin.py       compute intra-repo import fan-in per file
  fit_distributions.py   fit log-normal vs power-law, compute Gini/entropy
  compare_groups.py      Mann-Whitney U between groups
  longitudinal/          (in progress) longitudinal study scripts

data/
  repos/baseline/        cloned human-written repos
  repos/agentic/         cloned agentic repos
  results/baseline/      per-repo fan-in JSON
  results/agentic/       per-repo fan-in JSON
  summary.csv            all metrics, one row per repo

paper/
  draft.md               full paper draft

figures/                 generated plots
```

---

## Reproduce

```bash
pip install -r requirements.txt

# clone repos (shallow)
python scripts/collect_repos.py --group all

# compute fan-in
python scripts/compute_fanin.py --repo-dir data/repos/baseline --out-dir data/results/baseline
python scripts/compute_fanin.py --repo-dir data/repos/agentic  --out-dir data/results/agentic

# fit distributions + write summary.csv
python scripts/fit_distributions.py --results-dir data/results --out data/summary.csv

# compare groups
python scripts/compare_groups.py --summary data/summary.csv
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
Elke Shayna (2026). Fan-In Distributions in Human-Written vs AI-Generated Python
Codebases: A Constructal Law Analysis. [preprint]
```
