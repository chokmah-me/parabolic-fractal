<p class="hebrew-epigraph" dir="rtl" lang="he">אִם יִרְצֶה הַשֵּׁם</p>

# Topological Atrophy Under Agentic Coding: Longitudinal Evidence for Constructal Hierarchy Resilience in AI-Assisted Software Repositories

by **Daniyel Yaacov Bilar**, Chokmah LLC, chokmah-dyb@pm.me <p class="hebrew-date" dir="rtl" lang="he">ג׳ סִיוָן תשפ״ו</p>

ORCID: [0000-0002-9040-6914](https://orcid.org/0000-0002-9040-6914)

**[PREPRINT DRAFT]** · Companion paper to Bilar (2026a): "Fan-In Distributions in Human-Written vs AI-Generated Python Codebases: A Constructal Law Analysis"

---

## Abstract

Cross-sectional comparisons of human-written vs AI-generated codebases conflate
structural differences with selection effects. We address this with a within-repo
longitudinal design: tracking fan-in topology metrics monthly across N=2 Python
repositories (Celery, Django) before and after a documented transition to AI-assisted
coding. Adoption dates are identified from two independent signals: AI attribution
commit messages (`Co-authored-by: Copilot`, `noreply@anthropic.com`, etc.) and the
first appearance of AI tool config files (`.github/copilot-instructions.md`,
`CLAUDE.md`). We measure Gini coefficient, Vuong z (log-normal vs. power-law), and
delta_AIC at monthly snapshots (24 months pre, 12 months post).

In this preliminary two-repo study, we find no evidence of Gini decline following
AI adoption. In Celery (12 months post-adoption), Gini increased slightly
(p=0.031, paired Wilcoxon; last-6-pre mean 0.8664 vs. first-6-post mean 0.8680)
and the log-normal signal strengthened. In Django (2 months post-adoption), Gini
is unchanged (0.9327 vs. 0.9332). Without a matched control group, we cannot rule
out that these trajectories reflect continued natural maturation rather than any
effect of AI adoption. We interpret the null result as consistent with — but not
confirming — the hypothesis that the flattening effect observed cross-sectionally
is a structural genesis problem, not a maintenance problem: AI agents may flatten
topology when designing module structure from scratch, but AI-assisted contributions
to established codebases appear to follow the existing hierarchical import structure.
N=2 is insufficient for strong inference; these results are hypotheses to test
against a larger cohort.

---

## 1. Introduction

The companion paper establishes a cross-sectional baseline: 14 of 15 mature
human-written Python projects show log-normal fan-in (Gini ≈ 0.882, Vuong z > 1.96),
matching package-ecosystem benchmarks (PyPI, CRAN: Gini ≈ 0.88). Iterative human
refactoring under cognitive pressure acts as a Constructal optimization process,
bending the fan-in distribution from power-law toward log-normal parabolic curvature.

That cross-sectional result cannot rule out a simpler explanation: that AI-generated
and human-written repos differ on confounding variables (age, size, contributors,
domain). A within-repo longitudinal design removes these confounds. If the same
codebase develops lower Gini and weaker log-normal signal after adopting AI coding
tools, the change is attributable to the process, not to repo identity.

**The Conifold Transition.** In string theory, a conifold transition collapses a
3-cycle to a point and re-expands it as a 2-cycle: a smooth topological regime
change with no discontinuity in the physics. The middle layer of a codebase (the
"3-cycle": adapters, services, shared utilities that sit between a trunk and leaf
files) is predicted to collapse analogously when agentic coding removes the
evolutionary pressure that sustains it. The result is a direct trunk-to-leaf
structure (the "2-cycle"), flatter and higher-entropy. The collapse should appear as
a smooth change-point in the Gini time series, not an abrupt step.

**Research question:** Does documented adoption of AI coding tools produce a
measurable, temporally localized decline in fan-in Gini coefficient and log-normal
signal strength within individual Python repositories?

---

## 2. Related Work

**Constructal law and software topology.** Bejan & Lorente (2011) formalize the
constructal law: flow systems that persist are those whose geometry minimizes
resistance. Maillart & Sornette (2008) show that software package ecosystems follow
log-normal size distributions, consistent with constructal-tree predictions. The
companion paper (Bilar 2026a) extends this to intra-repo import topology,
finding that mature human-written Python repos fit log-normal fan-in while
AI-generated repos trend toward the flatter power-law end.

**AI-generated code structure.** Mao et al. (arXiv:2603.27130) show AI code is more
verbose, has higher content ratio (35.9% vs 20.1%), lower lexical density, and a
collapsed complexity distribution. These are consistent with flattening but are
measured cross-sectionally and at function level rather than topology level.

**Navigation and structural blindness.** Paipuru (arXiv:2602.20048) demonstrates
that agents without AST-derived graph access (CodeCompass) completely fail G3 tasks
requiring structural dependency traversal. This explains the mechanism: agents
cannot see the Constructal tree they degrade.

**Change-point detection in software evolution.** Prior longitudinal studies of OSS
structural change focus on coupling metrics, bug density, and code churn (Hassan &
Holt 2004), not on distributional topology. We use the PELT algorithm (Killick et al.
2012) for change-point detection, with a sliding-window mean-difference fallback.

---

## 3. Method

### 3.1 Repo Selection

**Inclusion criteria:**
- Python primary language
- Created before 2023 (minimum 2 years of pre-adoption history)
- Full git history available
- >50 Python files at the adoption date
- At least one unambiguous adoption signal in git history

**Adoption date detection (automated):** earliest of:
1. First commit message matching AI attribution patterns:
   `Co-authored-by: Cursor`, `generated with claude/copilot/gpt`,
   `🤖 Generated`, `vibe cod*`, `cursor agent`, `copilot agent`
2. First git-tracked appearance of AI config files:
   `.cursor/rules`, `.github/copilot-instructions.md`, `CLAUDE.md`,
   `.copilot/`, `copilot-instructions.md`

Detection is implemented in `scripts/longitudinal/find_adoption_date.py`.
Adoption dates are manually verified before inclusion.

### 3.2 Snapshot Protocol

For each included repo:
- Full clone (depth unlimited) to access complete git history
- Monthly snapshots: 24 months pre-adoption through 12 months post-adoption
- Each snapshot: `git checkout <last-commit-before-YYYY-MM-01>`
- Fan-in computed via `compute_fanin.py` (AST-based intra-repo import counting)
- Metrics computed via `fit_distributions.py` (`metrics_from_fanin()`)

### 3.3 Metrics

Per snapshot: Gini, normalized entropy, fraction leaves, Vuong z, delta_AIC,
lognormal_coeff_c (parabola curvature).

Primary outcome: **Gini coefficient** (most stable, least sensitive to repo size
changes). Secondary outcomes: Vuong z, delta_AIC.

### 3.4 Change-Point Detection

PELT algorithm (Killick et al. 2012, implemented via `ruptures` library) applied
to the Gini time series. Penalty parameter 3 (standard for single change-point).
Detected change-point date compared to known adoption date (lag in days).

### 3.5 Aggregate Analysis

Repos aligned to their adoption date (month 0). Mean ± std of each metric plotted
across all repos in the pre/post window. Paired Wilcoxon signed-rank test on
last-6-months-pre vs first-6-months-post Gini per repo.

---

## 4. Results

### 4.1 Candidate Identification and Adoption Dates

We scanned 15 baseline repos (shallow-cloned) for AI adoption signals. Four showed
signals in the shallow history. Full clones of three confirmed candidates yielded
adoption dates:

- **Celery**: first Copilot co-author commit 2025-05-08 ("Update
  t/integration/test_json_serializer_mem_leak.py Co-authored-by: Copilot"). Config
  file `.github/copilot-instructions.md` appeared 2025-08-26. Earliest signal:
  2025-05-08.
- **Django**: `.github/copilot-instructions.md` added 2026-03-05. No commit-level
  AI attribution. Adoption date: 2026-03-05.
- **aiohttp**: commit "Bump benchmark CI job timeout" co-authored by Claude Opus on
  2026-05-04; `CLAUDE.md` appeared 2026-05-17. Adoption date: 2026-05-04.

aiohttp was excluded from analysis: only 15 days of post-adoption data at collection
time. The longitudinal study uses Celery (N=37 monthly snapshots, 25 pre + 12 post)
and Django (N=27 snapshots, 25 pre + 2 post).

### 4.2 Gini Trajectory

| Repo | Adoption | Pre-Gini range | Post-Gini range | Last-6-pre | First-6-post | Δ | Wilcoxon p |
|------|----------|---------------|----------------|-----------|-------------|---|------------|
| Celery | 2025-05-08 | 0.858–0.867 | 0.867–0.871 | 0.8664 | 0.8680 | +0.0016 | 0.031 |
| Django | 2026-03-05 | 0.932–0.933 | 0.933 | 0.9327 | 0.9332 | +0.0005 | n/a (n=2 post) |

Gini increased in both repos post-adoption. The increase in Celery is statistically
significant but in the direction opposite to the flattening hypothesis. Django's
post-adoption window is too short for inference.

**Celery trajectory detail.** Gini sat around 0.858–0.860 through 2023, drifting up
to 0.866–0.867 by early 2025. Post-adoption (June 2025–May 2026), the drift
continued to 0.871. The sliding-window scan detected a change-point at February
2024, 486 days before adoption: that month, 40 files were added in a test
infrastructure reorganization. Nothing in that trajectory ties to AI adoption.

### 4.3 Log-Normal Signal Strength

In Celery, Vuong z and delta_AIC both increased post-adoption. Change-point detection
identified a step in both metrics at March 2026 (+273 days post-adoption):

| Metric | Pre-mean | Post-mean at CP | Δ |
|--------|----------|-----------------|---|
| delta_AIC | 80.0 | 103.4 | +23.4 |
| Vuong z | 6.55 | 7.94 | +1.39 |

The log-normal signal strengthened, not weakened. Django shows the same: Vuong z
rose from 4.6 to 5.3 over 2024–2026, a trend that began well before the 2026-03-05
adoption date and continued without inflection post-adoption.

### 4.4 Change-Point Summary

| Repo | Metric | CP date | Lag vs. adoption | Direction |
|------|--------|---------|-----------------|-----------|
| Celery | Gini | 2024-02-01 | −486 days | increase (pre-adoption structural event) |
| Celery | delta_AIC | 2026-03-01 | +273 days | STRENGTHENED |
| Celery | vuong_z | 2026-03-01 | +273 days | STRENGTHENED |
| Django | Gini | 2026-03-01 | −4 days | increase (+0.0004, negligible) |
| Django | delta_AIC | 2026-03-01 | −4 days | STRENGTHENED |
| Django | vuong_z | 2025-10-01 | −182 days | STRENGTHENED (pre-adoption trend) |

No detected change-point supports the atrophy hypothesis. All significant changes
either precede adoption or show strengthening of the log-normal signal.

---

## 5. Discussion

### 5.1 Genesis vs. Maintenance: Two Distinct Effects

The cross-sectional companion paper found Gini 0.725 in agentic repos vs. 0.882 in
baseline (p=0.0011). This longitudinal study finds no Gini decline when mature repos
adopt AI tools. The two results are compatible if the flattening effect operates at
the level of structural genesis, not structural maintenance.

When an AI agent designs a new codebase from scratch, it has no existing hierarchy to
follow. It generates files and imports based on immediate task context rather than
accumulated architectural pressure. The result is a flat import structure with many
files importing a common set of utilities (low Gini, high entropy) rather than a
tree with a differentiated middle layer.

When an AI assistant contributes to an established codebase, it operates within the
existing module structure. A Copilot suggestion in `celery/app/trace.py` imports
what that file already imports. It does not spontaneously introduce new modules or
reorganize the import graph. The Constructal tree is preserved because the AI is
participating in a context that already has it.

This distinction matters for how we interpret the structural risk of AI coding tools.
The threat is not primarily in ongoing maintenance of existing projects. It is in
new project construction and in wholesale rewrites, where no prior structure exists
to constrain the AI.

### 5.2 Why Celery's Log-Normal Signal Strengthened

Between May 2025 and March 2026, Celery gained ~14 files (404 → 416) and both Vuong
z and delta_AIC stepped up at a March 2026 change-point. The 14 files appear to
have landed high in the import tree rather than as new leaf files, tightening the
log-normal curvature. That is a plausible pattern if AI-assisted contributors
follow existing import conventions strictly. It is also plausible noise: one repo,
12 snapshots, a change-point detected by sliding window rather than PELT.

### 5.3 Implications for Codebase Health Attestation

Gini is useful as a first-look snapshot when evaluating a new repo or reviewing
AI-generated code for the first time. A project with Gini below ~0.75 and weak
log-normal signal (Vuong z < 2) is structurally flat, which is consistent with
AI-generated-from-scratch construction.

For monitoring an established repo over time, Gini is a slow signal. On a 12-month
horizon after AI adoption, it moves less than 0.002. Vuong z and delta_AIC move
faster and track changes in the middle of the distribution, where the constructal
hierarchy actually lives. If you want an early warning of structural degradation in
a mature repo, those are the metrics to watch.

### 5.4 Reversibility

We cannot test reversibility with the current data. Doing so would require repos
with documented AI adoption followed by a documented return to pure human development,
e.g. removal of AI config files. No such repos were identified in this study.

### 5.5 Limitations

N=2 repos (one with a full post-adoption window, one with two months) is insufficient
for strong inference. The conclusions are hypotheses to be tested against a larger
cohort, not settled results.

The adoption date signal is a proxy: many teams adopt AI tools informally before
their first attributable commit. Config file appearance (CLAUDE.md, .cursor/rules)
is a cleaner signal but rarer. Repos that adopted AI tools and then removed the
config files would be excluded.

Fan-in measures Python-layer coupling only. Repos with heavy non-Python layers will
show compressed signals. Repo growth itself can shift metrics; we control by
measuring Gini (scale-invariant) rather than raw fan-in counts.

Without a matched control group (pre-2023 repos that did NOT adopt AI tools over
the same period), we cannot rule out that the Celery and Django Gini trajectories
simply reflect continued natural maturation. The Gini increase we observe may have
nothing to do with AI adoption at all.

---

## 6. Conclusion

The hypothesis that AI adoption causes measurable Gini decline in mature codebases
is not supported by this longitudinal study. In Celery, Gini increased significantly
(p=0.031) in the 12 months following documented Copilot adoption, and the log-normal
signal strengthened. In Django, the metric is stable with only 2 months of post-
adoption data.

The cross-sectional flattening effect is a structural genesis problem, not a
maintenance problem. AI agents flatten topology when they build a codebase from
scratch. When they contribute to an established one, they follow the existing
import structure and leave the hierarchy intact. The structural risk is at project
inception, not at the PR level of mature codebases.

Gini is still a useful one-shot diagnostic for new repos and AI-assisted rewrites.
Whether flattening eventually appears in a mature repo under sustained AI-assisted
development over 3–5 years is still open. Twelve months of Celery post-adoption
data may not be long enough to see it.

---

## References

- Bejan, A. & Lorente, S. (2011). The constructal law and the evolution of design in nature. *Physics of Life Reviews*.
- Hassan, A.E. & Holt, R.C. (2004). Predicting change propagation in software systems. *ICSM 2004*.
- Killick, R., Fearnhead, P., & Eckley, I.A. (2012). Optimal detection of changepoints with a linear computational cost. *JASA*, 107(500), 1590–1598.
- Maillart, T. & Sornette, D. (2008). Heavy-tailed distributions of software structure. *arXiv:0805.3397*.
- Mao, T., Zhao, D., Tang, H., Wang, X., & Zhang, H. (2026). A large-scale empirical study of AI-generated code in real-world repositories. *arXiv:2603.27130*.
- Paipuru, T. (2026). CodeCompass: Navigating the Navigation Paradox in Agentic Code Intelligence. *arXiv:2602.20048*.
- Vuong, Q.H. (1989). Likelihood ratio tests for model selection and non-nested hypotheses. *Econometrica*, 57(2), 307–333.
- Bilar, D.Y. (2026a). Fan-in distributions in human-written vs AI-generated Python codebases: a Constructal Law analysis. [companion preprint, chokmah-me/parabolic-fractal]
- Bilar, D.Y. (2026c). Three regimes of capability attestation for autonomous agents. [forthcoming]
