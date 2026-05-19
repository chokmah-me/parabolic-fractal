# Topological Atrophy Under Agentic Coding: Longitudinal Evidence for Constructal Hierarchy Collapse in AI-Assisted Software Repositories

**[PREPRINT DRAFT — data collection pending]**

Companion paper to: "Fan-In Distributions in Human-Written vs AI-Generated Python
Codebases: A Constructal Law Analysis" (cross-sectional preprint)

---

## Abstract

Cross-sectional comparisons of human-written vs AI-generated codebases conflate
structural differences with selection effects. We address this with a within-repo
longitudinal design: tracking fan-in topology metrics monthly across [N] Python
repositories before and after a documented transition to AI-assisted coding. Adoption
dates are identified from two independent signals — AI attribution commit messages
(`Co-authored-by: Cursor`, `generated with Claude`, etc.) and the first appearance
of AI tool config files (`.cursor/rules`, `CLAUDE.md`, `copilot-instructions.md`).
We measure Gini coefficient, Vuong z (log-normal vs power-law), and delta_AIC at
each snapshot. [RESULTS PENDING.] A detected Gini decline post-adoption would
constitute the first longitudinal empirical evidence for the "agentic flattening
effect": the collapse of the hierarchical fan-in topology predicted by Constructal
theory when iterative human cognitive pressure is removed from the development cycle.

---

## 1. Introduction

The companion paper establishes a cross-sectional baseline: 14 of 15 mature
human-written Python projects show log-normal fan-in (Gini ≈ 0.882, Vuong z > 1.96),
matching package-ecosystem benchmarks (PyPI, CRAN: Gini ≈ 0.88). The interpretation
is that iterative human refactoring under cognitive pressure acts as a Constructal
optimization process, bending the fan-in distribution from power-law toward
log-normal parabolic curvature.

This cross-sectional result cannot rule out a simpler explanation: that AI-generated
and human-written repos differ on confounding variables (age, size, number of
contributors, domain). A within-repo longitudinal design eliminates these confounds.
If the same codebase develops lower Gini and weaker log-normal signal after adopting
agentic coding tools, the change is attributable to the process change, not to repo
identity.

**The Conifold Transition.** In string theory, a conifold transition collapses a
3-cycle to a point and re-expands it as a 2-cycle — a smooth topological regime
change with no discontinuity in the physics. We use this as a metaphor: the
intermediate branching layer of a codebase (the "3-cycle" — adapters, services,
shared utilities that mediate trunk-to-leaf connections) is predicted to collapse
smoothly as agentic coding removes the evolutionary pressure that sustains it. The
resulting topology is a direct trunk-to-leaf structure (the "2-cycle"), flatter and
higher-entropy. The transition should be detectable as a smooth change-point in the
Gini time series, not an abrupt step.

**Research question:** Does documented adoption of AI coding tools produce a
measurable, temporally localized decline in fan-in Gini coefficient and log-normal
signal strength within individual Python repositories?

---

## 2. Related Work

**Constructal law and software topology.** [Cite companion paper. Cite Bejan &
Lorente 2011. Cite Maillart & Sornette 2008 for log-normal in software.]

**AI-generated code structure.** Mao et al. (arXiv:2603.27130) show AI code is more
verbose, has higher content ratio (35.9% vs 20.1%), lower lexical density, and a
collapsed complexity distribution. These are consistent with flattening but are
measured cross-sectionally and at function level rather than topology level.

**Navigation and structural blindness.** Paipuru (arXiv:2602.20048) demonstrates
that agents without AST-derived graph access (CodeCompass) completely fail G3 tasks
requiring structural dependency traversal. This explains the mechanism: agents
cannot see the Constructal tree they degrade.

**Change-point detection in software evolution.** [FILL: prior longitudinal studies
of OSS structural change. Killick et al. 2012 PELT algorithm for change-point
detection in time series (cite for methodology).]

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

[PENDING — requires repo data collection and walk_history.py execution]

Expected table structure:

| Repo | Adoption date | Adoption signal | Pre-Gini (mean) | Post-Gini (mean) | Delta | CP lag |
|------|--------------|-----------------|-----------------|------------------|-------|--------|
| ...  | ...          | ...             | ...             | ...              | ...   | ...    |

---

## 5. Discussion

[PENDING results]

### 5.1 Rate of Decay

[If confirmed: how many months post-adoption until change-point is detectable?
Is the transition gradual or step-like? Does it correlate with commit volume?]

### 5.2 Reversibility

[Can a repo recover log-normal topology after AI adoption, e.g. through explicit
refactoring sprints? Requires repos with documented AI → human-review transitions.]

### 5.3 Implications for Codebase Health Attestation

Fan-in Gini is a lightweight, passive, history-accessible metric. A repo whose Gini
trajectory is declining post-adoption is exhibiting structural atrophy detectable
without running any tests. This complements behavioral attestation (the three-regime
framework) with a structural signal. Unlike behavioral tests, it is hard to spoof:
an agent generating plausible-looking code cannot easily fake log-normal fan-in
without doing the intermediate-abstraction refactoring that creates it.

Practical implication: CI pipelines or code review tools could track rolling Gini
and Vuong z per PR, flagging structural decay before it becomes irreversible.

### 5.4 Limitations

The adoption date signal is a proxy: many teams adopt AI tools informally before
their first attributable commit. Config file appearance (CLAUDE.md, .cursor/rules)
is a cleaner signal but rarer. Repos that adopted AI tools and then removed the
config files would be excluded. Fan-in measures Python-layer coupling only; repos
with heavy non-Python layers (like NumPy in the companion paper) will show
compressed signals. Repo growth itself increases n_files and can shift metrics;
we control by measuring Gini (scale-invariant) rather than raw counts.

---

## 6. Conclusion

[PENDING results]

---

## References

- Bejan, A. & Lorente, S. (2011). The constructal law and the evolution of design in nature. *Physics of Life Reviews*.
- Killick, R., Fearnhead, P., & Eckley, I.A. (2012). Optimal detection of changepoints with a linear computational cost. *JASA*, 107(500), 1590-1598.
- Maillart, T. & Sornette, D. (2008). Heavy-tailed distributions of software structure. *arXiv:0805.3397*.
- Mao, T., Zhao, D., Tang, H., Wang, X., & Zhang, H. (2026). A large-scale empirical study of AI-generated code in real-world repositories. *arXiv:2603.27130*.
- Paipuru, T. (2026). CodeCompass: Navigating the Navigation Paradox in Agentic Code Intelligence. *arXiv:2602.20048*.
- Vuong, Q.H. (1989). Likelihood ratio tests for model selection and non-nested hypotheses. *Econometrica*, 57(2), 307-333.
- Elke Shayna (2026). Fan-in distributions in human-written vs AI-generated Python codebases. [companion preprint]
- Elke Shayna (2026). Three regimes of capability attestation for autonomous agents. [forthcoming]
