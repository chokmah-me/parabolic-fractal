<p class="hebrew-epigraph" dir="rtl" lang="he">אִם יִרְצֶה הַשֵּׁם</p>

# Fan-In Distributions in Human-Written vs AI-Generated Python Codebases: A Constructal Law Analysis

by **Daniyel Yaacov Bilar**, Chokmah LLC, chokmah-dyb@pm.me <p class="hebrew-date" dir="rtl" lang="he">ג׳ סִיוָן תשפ״ו</p>

ORCID: [0000-0002-9040-6914](https://orcid.org/0000-0002-9040-6914)

---

## Abstract

Import fan-in — the count of intra-repo modules that import a given file — encodes
the hierarchical coupling structure of a codebase. Constructal theory (Bejan 1996)
predicts that any finite flow system shaped by iterative optimization develops
log-normal, not power-law, size distributions. We measure fan-in distributions across
15 mature Python open-source projects (Cohort A) and 22 Python repositories with
public AI-authorship signals created 2024-2026 (Cohort B, identified by CLAUDE.md,
`.cursor/rules`, `Co-authored-by: Cursor` commit trailers, or README self-attribution;
these skew toward single-author short-lifespan projects and are not representative
of all AI-assisted code).
In Cohort A, 14 of 15 projects show statistically significant log-normal fan-in
(Vuong z > 1.96), with Gini mean 0.882, matching prior benchmarks for mature package
ecosystems (PyPI, CRAN: Gini ≈ 0.88). In Cohort B, 10 of 22 repos could not be fitted (3 with Gini=0.000, 4 with
fewer than 10 connected files, 3 too small or inaccessible); 32% exhibit zero or
near-zero intra-repo coupling. Among the 12 Cohort B repos with sufficient coupling,
Gini mean is 0.725 (Mann-Whitney U, p = 0.0011, rank-biserial r = −0.744), and
log-normal signal strength is halved (mean Vuong z 2.77 vs 6.00, p = 0.019). 11 of
12 still exhibit log-normal shape, but with markedly lower concentration and weaker
parabolic curvature. We term this the **agentic flattening effect**: the partial
collapse of the hierarchical fan-in topology that Constructal theory predicts when
iterative cognitive refactoring pressure is removed from the development cycle.

---

## TL;DR by Audience

**Software engineer / architect:** We parsed every `import` statement in 37 Python
repos (15 mature OSS, 22 publicly AI-attributed), fitted distributions on the 27 with
sufficient coupling, and measured how unequally fan-in is distributed (Gini) and
whether the rank-frequency curve is log-normal or power-law (AIC + Vuong test).
Human-written repos: Gini 0.88, log-normal wins 14/15. AI-attributed repos: three
have *zero* intra-repo imports (every file only touches external packages), and among
the 12 with sufficient coupling, Gini drops to 0.72 (p=0.001, large effect). The parabolic log-log curvature weakens but doesn't
flip. Practical upshot: fan-in Gini is a cheap, CI-friendly structural health metric.
If your repo's Gini is trending toward 0.6, your intermediate abstraction layer is
dissolving.

**Cognitive scientist:** Human developers experience coupling as cognitive friction.
When a module accumulates too many dependents, navigating its blast radius becomes
costly enough to trigger refactoring — an unconscious optimization loop that matches
Bejan's Constructal Law for flow networks. The signature is a log-normal fan-in
distribution with Gini ≈ 0.88, matching package-ecosystem benchmarks at a different
scale. LLMs have no equivalent feedback: processing a 10,000-line file incurs no
additional cognitive cost to the agent. Our data shows what we hypothesize is the
structural consequence: absent coupling pressure, the intermediate branching layer
partially collapses, Gini drops, and three repos reach the degenerate state of
zero intra-repo coupling.

**General reader:** When experienced programmers build software over years, it
develops a predictable internal structure — a small number of central files that
everything else depends on, surrounded by layers of intermediate connectors. Think
of it like a city road network: highways feed arterials feed local streets. We found
this hub-and-spoke structure in 14 of 15 well-known Python projects. In the
AI-attributed projects, that structure is visibly degraded: three repos had zero
connections between their own files (every file a dead end), and the rest had
significantly flatter hierarchies. The software runs — but it lacks the layered
organization that makes large codebases maintainable over time.

**Skeptic:** Fair objections: (1) Selection bias — our agentic repos are publicly
self-attributing outliers, not representative of all AI-assisted code. (2) FastAPI's
own design philosophy encourages thin routers and heavy external-library coupling,
independently of AI authorship. (3) The Mann-Whitney test uses only 12 agentic repos
after filtering; the sample is still modest. (4) "Log-normal wins 11/12" in agentic
repos undercuts a simple narrative. Our response: we acknowledge these limits
explicitly in Section 5.5. The filter exclusions (10 repos too flat or too small to
measure) strengthen, not weaken, the finding. The FastAPI confound is real but cannot
explain Gini=0.000 in repos with 88-92 files. The effect size (r=−0.744) is large
enough to be meaningful at n=12. And the log-normal persistence is theoretically
interesting: the parabola flattens, it doesn't invert — consistent with Constructal
gradient atrophy, not a phase transition.

**Funders / investors:** AI coding tools promise 10× developer velocity. Our data
suggests an unreported structural cost: AI-generated codebases show significantly
lower architectural concentration (Gini −18%, p=0.001) and weaker hierarchical
organization. Three of 22 studied repos had zero internal coupling — each file a
standalone island. This matters for maintainability: flat architectures increase
the cost of every future change (no shared abstraction to update; changes must be
made everywhere). The fix is not to stop using AI tools, but to instrument CI
pipelines with structural health metrics — a lightweight, automated check that
flags architectural decay before it accumulates. This paper provides the first
empirical baseline for what "healthy" fan-in distribution looks like, enabling
such tooling.

**Policy-maker / regulator:** Autonomous AI coding agents are already writing
production software in critical domains — financial modeling, medical data
pipelines, government simulation systems (one of our study repos is a Dutch
government machine-law proof-of-concept). We provide the first structural evidence
that AI-generated code differs measurably from human-written code in its
architectural organization, independent of whether it passes tests. Three of 22 repos
had zero internal structure — each file isolated from every other. A companion
framework (Daniyel Yaacov Bilar, forthcoming) shows that behavioral testing of AI agents is
mathematically intractable under adversarial conditions. Structural metrics like
fan-in Gini offer a passive, non-gameable complement: a codebase whose Gini matches
the human-written baseline has demonstrably undergone the kind of iterative
refinement that produces maintainable, auditable software. Our results suggest structural topology
metrics are worth investigating as passive complements to behavioral testing in
regulated software contexts; this paper provides an empirical baseline to support
such tooling.

---

## 1. Introduction

Software dependency graphs are not random. Organic growth under refactoring
pressure, code review, and the DRY principle produces characteristic topologies.
Early studies of operating systems and Unix libraries observed heavily skewed
fan-in distributions and attributed them to preferential attachment, predicting
power-law degree distributions. A strict power-law requires an infinite network
to sustain its straight-line tail in log-log space. Real codebases are finite,
bounded by what human architects can safely navigate, and the tail bends.

Constructal theory explains this bending from first principles. Bejan's Constructal
Law states: "For a finite-size flow system to persist in time (to live), it must
evolve in such a way that it provides easier access to the imposed currents that
flow through it." Applied to software, the "currents" are execution paths and
cognitive attention. A developer who feels the resistance of navigating an
overloaded, highly coupled module will refactor it — splitting the bottleneck,
building intermediate abstraction layers, and bending the fan-in distribution away
from a pure power-law into a downward-opening parabola in log-log space. That
parabola is the signature of a log-normal distribution. Clauset, Shalizi, and Newman
(2009) showed that capacity limits cause real finite-network distributions to decay
faster than any pure power-law, making log-normal the better empirical fit; we extend
that test to intra-repo file-level fan-in and to a new comparison class: AI-generated
code.

AI code generators remove this optimization pressure. A developer who feels the
cognitive resistance of an overloaded module will refactor it — an intrinsic feedback
loop. An LLM has no equivalent: it processes a 10,000-line file at no additional
cognitive cost to itself, and so has no intrinsic pressure to split bottlenecks or
build intermediate abstraction layers. We hypothesize that the predicted architectural
consequence is the **agentic flattening effect**: collapse of Gini inequality and
weakening of log-normal parabolic curvature, because the evolutionary pressure that
builds the intermediate branching layer is absent at structural genesis.

**Research question:** Do mature human-written Python projects show significantly
higher fan-in Gini and stronger log-normal signal compared to publicly AI-attributed
projects?

---

## 2. Related Work

**Power-law and log-normal in networks.** Preferential attachment (Barabasi & Albert
1999) predicts power-law degree distributions in growing networks. Clauset, Shalizi,
and Newman (2009) established that power-law fits are often indistinguishable from
log-normal in finite data, and provided rigorous testing methods. Their key finding:
cognitive and physical capacity limits cause real-world distributions to decay faster
than any pure power-law, making log-normal a better fit.

**Software dependency metrics.** Maillart and Sornette (2008) showed that Linux
open-source package size distributions follow Zipf's power law, with Gibrat's
proportional growth as the generating mechanism. In finite networks with bounded
growth, proportional growth produces log-normal rather than power-law tails (Clauset
et al. 2009); the Constructal prediction is that cognitive refactoring pressure
imposes exactly this finite-size bound. Package ecosystem studies report Gini ≈ 0.88
for dependency fan-in in PyPI and CRAN, and 0.84 in Bioconductor [cite: source for
these benchmark figures needed].

**Constructal law in flow systems.** Hess and Murray showed that minimizing both
construction cost and flow resistance in branching networks yields the cubic law
$d_0^3 = d_1^3 + d_2^3$ at each bifurcation. Bejan and Lorente (2011) generalized
this to arbitrary flow systems under the Constructal Law. In log-log rank-frequency
space, the resulting size distribution traces a downward-opening parabola.

**AI-generated code structure.** Mao et al. (2026) conducted a large-scale empirical
study of AI-generated code in real-world repositories. AI code is consistently more
verbose, with higher content ratio (35.9% vs 20.1%) but lower lexical density
(0.531 vs 0.658), and a collapsed complexity distribution — uniform medium-sized
blocks replacing the heavy-tailed distribution of human code. These are consistent
with flattening at the function level; we test the same hypothesis at the
architectural (fan-in topology) level.

**Navigation in AI agents.** Paipuru (2026) showed that agents without AST-derived
graph access fail completely on G3 tasks requiring structural dependency traversal
with zero lexical overlap with the prompt. This is consistent with a mechanism in
which structural blindness produces architectural drift: agents that cannot traverse
the import graph cannot feel the coupling pressure that would otherwise drive
refactoring.

Given that (a) Constructal optimization under cognitive pressure produces log-normal
fan-in at multiple scales, (b) AI-generated code shows distributional flattening at
the function level (Mao et al. 2026), and (c) AI agents lack the structural
perception that would enable Constructal feedback (Paipuru 2026), we extend the
log-normal test to intra-repo file-level fan-in and compare mature human-written
repositories against a cohort of publicly AI-attributed repositories.

---

## 3. Method

### 3.1 Repository Selection

**Cohort A (baseline — human-written):** 15 mature Python OSS projects, all with
>5 years of development and >100 contributors: Django, Flask, NumPy, pandas,
SQLAlchemy, Celery, FastAPI, requests, pytest, Scrapy, httpx, Pydantic, aiohttp,
Tornado, Click.

**Cohort B (agentic — AI-generated or AI-assisted):** 22 Python repositories
created 2024-2026, each meeting at least one of:
- CLAUDE.md or `.cursor/rules` present in root
- Commit messages containing `Co-authored-by: Cursor cursoragent@cursor.com`
  or `noreply@anthropic.com`
- README explicitly describes AI-assisted or AI-generated development

Repositories were selected to avoid AI *tooling* frameworks (LangChain, AutoGPT)
in favor of actual applications *built by* AI agents.

All repos cloned at HEAD (shallow, depth=1) as of May 2026.

### 3.2 Fan-In Measurement

For each `.py` file $f$ in a repository:

$$\text{fan-in}(f) = |\{g \in \text{repo} : g \neq f,\ g \text{ imports } f\}|$$

Fan-in is measured using Python's `ast` module. Relative imports are resolved
against the intra-repo module namespace. External imports are discarded. Files
with zero fan-in (leaves) are included in Gini and entropy calculations but
excluded from distribution shape fitting, which requires $\geq 10$ files with
positive fan-in.

### 3.3 Distribution Fitting

We fit two models to rank-frequency data of positive fan-in values in log-log space:

**Power-law:** $\log v = a + b \log r$, OLS, $k=2$ parameters.

**Log-normal (parabolic):** $\log v = a + b \log r + c (\log r)^2$, OLS, $k=3$ parameters.

Model comparison:

1. **AIC:** $\Delta\text{AIC} = \text{AIC}_\text{PL} - \text{AIC}_\text{LN}$. Positive = log-normal preferred. Threshold $\Delta\text{AIC} > 2$ (Burnham & Anderson 2002).

2. **Vuong's closeness test (1989):** Per-observation log-likelihood ratios $\text{LR}_i = \ell_{\text{LN},i} - \ell_{\text{PL},i}$. Test statistic $z = \sqrt{n}\,\overline{\text{LR}} / \hat{\sigma}_{\text{LR}}$. $z > 0$ favors log-normal.

We use AIC + Vuong rather than the Clauset et al. (2009) KS + MLE protocol because
the Clauset approach fits only the upper tail of the power-law and does not directly
compare against a log-normal alternative. Our method fits both candidate models to
the full rank-frequency curve in log-log space and selects between them — appropriate
here because our question is which shape better describes the complete fan-in
distribution, not whether the tail alone is power-law.

### 3.4 Statistical Comparison

Mann-Whitney U (non-parametric, two-sided). Effect sizes as rank-biserial $r$.

---

## 4. Results

### 4.1 Baseline Group (Cohort A)

| Repo       | Files | Gini  | ΔAIC   | Vuong z | LN? |
|------------|------:|------:|-------:|--------:|-----|
| django     | 2910  | 0.933 | +308.3 | +5.32   | YES |
| flask      | 83    | 0.866 | +13.4  | +4.64   | YES |
| numpy      | 494   | 0.939 | +1.5   | +1.11   | no  |
| pandas     | 1509  | 0.962 | +206.5 | +10.17  | YES |
| sqlalchemy | 669   | 0.939 | +262.6 | +11.40  | YES |
| celery     | 416   | 0.871 | +106.0 | +8.14   | YES |
| fastapi    | 1119  | 0.981 | +165.8 | +7.09   | YES |
| requests   | 37    | 0.660 | +24.8  | +5.57   | YES |
| pytest     | 262   | 0.906 | +79.8  | +11.08  | YES |
| scrapy     | 439   | 0.900 | +97.6  | +2.30   | YES |
| httpx      | 60    | 0.816 | +10.8  | +3.23   | YES |
| pydantic   | 402   | 0.917 | +62.4  | +2.98   | YES |
| aiohttp    | 164   | 0.846 | +24.1  | +3.92   | YES |
| tornado    | 107   | 0.844 | +51.4  | +7.58   | YES |
| click      | 63    | 0.845 | +13.2  | +5.54   | YES |
| **mean**   |       | **0.882** | **+95.2** | **+6.00** | **14/15** |

14 of 15 repos show log-normal fan-in. The exception is NumPy ($\Delta\text{AIC}=+1.5$,
Vuong $z=+1.11$): NumPy's Python layer is a thin wrapper over C extensions,
compressing intra-Python coupling. The Gini mean of 0.882 matches prior benchmarks
(PyPI, CRAN: Gini ≈ 0.88; Bioconductor: 0.84 [cite: source needed]) — validating
the method across scales.

### 4.2 Agentic Group (Cohort B)

Of 22 agentic repos cloned, 10 could not be fitted:

| Repo | Files | Files (fanin>0) | Gini | Reason excluded |
|------|------:|----------------:|-----:|-----------------|
| dark-factory-experiment | 92 | 0 | 0.000 | Zero intra-repo coupling |
| ott-platform | 88 | 0 | 0.000 | Zero intra-repo coupling |
| OneResearchClaw | 30 | 0 | 0.000 | Zero intra-repo coupling |
| tradinggame | 62 | 4 | 0.946 | <10 connected files |
| camp2025-stock | 119 | 8 | 0.971 | <10 connected files |
| J.A.R.V.I.S | 57 | <5 | — | <10 connected files |
| Hackathon-II_The-Evolution-of-Todo | 66 | <2 | — | <10 connected files |
| deepseek_ocr_app | 4 | — | — | Too small |
| agentic-sprint | 0 | — | — | No Python files (agent config template) |
| claude-cli-rest-api | — | — | — | Checkout failure (Windows path) |

Three repos (dark-factory-experiment, ott-platform, OneResearchClaw) have Gini=0.000:
every Python file is isolated with zero intra-repo imports. No baseline repo showed
this pattern. Among the 12 fitted agentic repos:

| Repo | Files | Gini  | ΔAIC  | Vuong z | LN? |
|------|------:|------:|------:|--------:|-----|
| borrowhood | 275 | 0.854 | +78.9 | +4.03 | YES |
| loki-mode | 531 | 0.922 | +34.9 | +4.19 | YES |
| lazy-bird | 136 | 0.834 | +83.0 | +7.47 | YES |
| CLI-Anything-WEB | 453 | 0.751 | +78.4 | +3.24 | YES |
| zhang2025 | 50 | 0.826 | +5.1 | +1.98 | YES |
| django-bolt | 292 | 0.789 | +4.4 | +1.45 | YES |
| marsa-planner | 37 | 0.705 | +2.1 | +1.29 | YES |
| fqf | 36 | 0.705 | +11.7 | +3.10 | YES |
| NewsCrawler | 121 | 0.652 | +22.9 | +3.24 | YES |
| openclaude | 21 | 0.625 | +3.9 | +2.02 | YES |
| poc-machine-law | 286 | 0.581 | +3.1 | +0.52 | YES |
| codebase-mcp | 51 | 0.460 | +1.2 | +0.67 | no |
| **mean** | | **0.725** | **+27.5** | **+2.77** | **11/12** |

11 of 12 show log-normal shape ($\Delta\text{AIC} > 2$). The exception is
codebase-mcp ($\Delta\text{AIC}=+1.2$, Vuong $z=+0.67$): a small FastAPI MCP server
where the log-normal preference exists but falls below both thresholds. poc-machine-law
(Vuong $z=+0.52$, p=0.60) meets the AIC threshold but not Vuong significance.

### 4.3 Between-Group Comparison

| Metric | Baseline (n=15) | Agentic (n=12) | U | p | r |
|--------|----------------:|---------------:|--:|--:|--:|
| Gini | 0.882 | 0.725 | 157.0 | **0.0011** | −0.744 |
| ΔAIC | 95.2 | 27.5 | 138.0 | **0.019** | −0.533 |
| Entropy (norm.) | 0.770 | 0.887 | 26.0 | **0.002** | +0.711 |
| Fraction leaves | 0.680 | 0.495 | 140.0 | **0.015** | −0.556 |

Gini is significantly lower in the agentic group (large effect, r=−0.744). Entropy
is significantly higher (more uniform distribution, r=+0.711). Log-normal signal
strength (ΔAIC) is also significantly lower (r=−0.533). Fraction of leaf files is
now also significant (r=−0.556): agentic repos have proportionally fewer zero-fanin
files. This likely reflects survivor bias — larger projects with some intermediate
structure passed the fitting filter — rather than genuine architectural improvement;
the three repos with Gini=0.000 are all excluded from this comparison.

Figure 3 shows Gini boxplots by group. Figure 4 shows ΔAIC vs repo size, with
agentic repos clustering near the power-law boundary.

---

## 5. Discussion

### 5.1 Two Modes of Structural Degeneration

The agentic group shows degeneration in two distinct forms, not one:

**Mode 1 — Total isolation (Gini=0):** dark-factory-experiment, ott-platform, and
OneResearchClaw have zero intra-repo fan-in. Every Python file is a leaf. The first
two are FastAPI backends with complete routing logic; the third is an autonomous
research framework. All their coupling is to *external* libraries, not to each other.
The intra-repo dependency graph is an empty set. No baseline repo approached this
state.

**Mode 2 — Partial flattening (lower Gini, attenuated parabola):** The 12 fitted
agentic repos still show log-normal shape in 11 of 12 cases, but at 82% of baseline
Gini. The intermediate branching layer is present but thinner. This is not random
noise: Vuong z values in agentic repos average 2.77 vs 6.00 in baseline — the
parabolic curvature is real but shallow.

Both modes are consistent with the Constructal prediction: remove the optimization
pressure, and the branching hierarchy degrades. The degree of degradation depends
on how much coupling the project requires to function at all. Highly modular
FastAPI backends can achieve full functionality with zero intra-repo coupling
(just external library imports), while larger orchestration systems (loki-mode,
531 files) cannot avoid some intermediate structure.

### 5.2 The Log-Normal Paradox

11 of 12 fitted agentic repos prefer log-normal over power-law. This is not a null
result — it refines the hypothesis. The Constructal prediction is not that
AI-generated code produces power-law fan-in; it is that AI-generated code lacks
the *intermediate branching layer* that bends the distribution away from power-law.
Without enough connected files to measure (Gini=0.000 cases), there is no
distribution to bend at all. In repos with some coupling, the curvature is present
but weak: lower Gini, lower Vuong z, lower ΔAIC, and one case (poc-machine-law)
with a non-significant Vuong test.

The finding is therefore: agentic repos do not switch to power-law; they shrink
toward the power-law boundary. The parabola flattens without inverting.

### 5.3 Survivor Bias and True Degeneration Rate

The Mann-Whitney comparison (Gini 0.882 vs 0.725, p=0.0011) understates the gap
because the three most extreme agentic repos (Gini=0.000) are excluded by the
fitting filter. Including them as Gini=0.000 would bring the agentic mean to
approximately 0.580 — a gap of 0.302 vs baseline. The true degeneration rate across
all 22 agentic repos is: 3 repos total isolation (14%), 4 repos near-isolation
(<10 connected files, 18%), and 12 repos measurably flattened. Just over half the
agentic corpus has enough intra-Python coupling to measure at all.

### 5.4 Connection to Attestation

The three-regime attestation framework (Daniyel Yaacov Bilar, forthcoming) shows that
behavioral verification of autonomous agents is intractable in Regime 3 (adversarial
stochastic). Fan-in topology offers a complementary passive structural signal.
Unlike behavioral tests, structural metrics require actual refactoring work to fake:
an agent generating plausible test-passing code cannot easily replicate the log-normal
fan-in signature of a genuinely maintained codebase without building the intermediate
abstraction layer. Gini and Vuong z could serve as lightweight health indicators in
CI pipelines or code review tools, flagging structural atrophy before it becomes
irreversible.

### 5.5 Limitations

Fan-in is first-order; it ignores call graphs, data flow, and semantic coupling.
Agentic repo selection is biased toward projects with public AI attribution — private
vibe-coded codebases may differ. Shallow cloning captures HEAD without evolutionary
trajectory; the companion longitudinal study (Bilar 2026b) finds that mature repos
adopting AI tools do not exhibit Gini decline on a 12-month horizon. The Constructal
interpretation is analogical; Bejan's framework was not formally derived for
discrete directed graphs. FastAPI's design philosophy (thin routers, heavy external
dependencies) may independently reduce intra-repo coupling regardless of authorship,
partially confounding the agentic vs human comparison. Of the 22 Cohort B repos, at
least 3 are FastAPI-style backends (dark-factory-experiment, ott-platform — both
Gini=0.000 — and codebase-mcp). If further repos in the fitted group are also
FastAPI-style, the confound may account for a portion of the Gini gap that is not
attributable to AI authorship.

---

## 6. Conclusion

We measured import fan-in distributions across 15 mature human-written and 22
AI-generated Python repositories. Human-written repos show log-normal fan-in with
Gini mean 0.882, matching prior benchmarks and consistent with Constructal flow
optimization under cognitive refactoring pressure. AI-generated repos exhibit
two forms of structural degeneration: total isolation (Gini=0.000, 3/22 repos)
and partial flattening (Gini mean 0.725 among measurable repos, p=0.0011,
r=−0.744). 11 of 12 fitted agentic repos retain log-normal shape, but with
significantly weaker parabolic curvature (Vuong z mean 2.77 vs 6.00, p=0.019).
The log-normal signature is not erased — it is attenuated. This is the structural
fingerprint of a codebase that never underwent the iterative refactoring that bends
fan-in distributions toward their Constructal optimum. The companion longitudinal
study (Bilar 2026b) finds that this atrophy does not appear in mature repos after
documented AI adoption on a 12-month horizon, suggesting the flattening effect is
specific to structural genesis rather than ongoing maintenance.

---

## References

- Barabasi, A.L. & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286, 509-512.
- Bejan, A. (1996). Constructal-theory network of conducting paths for cooling a heat generating volume. *Int. J. Heat Mass Transfer*, 40(4), 799-816.
- Bejan, A. & Lorente, S. (2011). The constructal law and the evolution of design in nature. *Physics of Life Reviews*, 8(3), 209-240.
- Burnham, K.P. & Anderson, D.R. (2002). *Model Selection and Multimodel Inference*. Springer.
- Clauset, A., Shalizi, C.R. & Newman, M.E.J. (2009). Power-law distributions in empirical data. *SIAM Review*, 51(4), 661-703.
- Maillart, T. & Sornette, D. (2008). Empirical tests of Zipf's law mechanism in open source Linux distribution. *Physical Review Letters*, 101, 218701. https://doi.org/10.1103/PhysRevLett.101.218701
- Mao, T., Zhao, D., Tang, H., Wang, X., & Zhang, H. (2026). A large-scale empirical study of AI-generated code in real-world repositories. *arXiv:2603.27130*.
- Paipuru, T. (2026). CodeCompass: Navigating the Navigation Paradox in Agentic Code Intelligence. *arXiv:2602.20048*.
- Vuong, Q.H. (1989). Likelihood ratio tests for model selection and non-nested hypotheses. *Econometrica*, 57(2), 307-333.
- Bilar, D.Y. (2026a). Fan-in distributions in human-written vs AI-generated Python codebases: a Constructal Law analysis. [this paper, chokmah-me/parabolic-fractal]
- Bilar, D.Y. (2026b). Topological atrophy under agentic coding: longitudinal evidence for Constructal hierarchy resilience in AI-assisted software repositories. [companion preprint, chokmah-me/parabolic-fractal]
- Bilar, D.Y. (2026c). Three regimes of capability attestation for autonomous agents. [forthcoming]
