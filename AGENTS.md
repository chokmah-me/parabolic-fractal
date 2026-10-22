# AGENTS.md — parabolic-fractal

Code and data for fan-in / constructal-law papers on human-written vs AI-generated Python repos. Cross-section plus longitudinal pilot. Not a proof that AI “simplifies” code in general.

## Commands

```powershell
pip install -r requirements.txt
python scripts/check_paper_claims.py
python scripts/collect_repos.py --group all
python scripts/compute_fanin.py --repo-dir data/repos/baseline --out-dir data/results/baseline
python scripts/fit_distributions.py --results-dir data/results --out data/summary.csv
python scripts/compare_groups.py --summary data/summary.csv
python scripts/longitudinal/pilot_summary.py
```

`check_paper_claims.py` exit 0 iff every cited number in paper v1.1 errata and §7.7 still matches.

## Work rules

- Fitted n is 15 baseline + 12 agentic (27 of 37 clones). Exclusions are below the measurement threshold.
- Longitudinal finding is “no Gini decline after declared AI adoption,” not a causal claim.
- Keep receipt-backed edits on claims, tables, and published figures.

## Pointers

- `README.md` — findings, reproduce steps, DOIs
- `paper/` — manuscript sources
- `scripts/check_paper_claims.py` — executable number gate
