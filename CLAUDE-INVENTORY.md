# CLAUDE.md inventory — `data/repos/` (read-only)

The repositories under `data/repos/` are **third-party cloned repos used as a research dataset**,
organized into a `baseline / agentic / longitudinal` split. Each carries its own upstream
`CLAUDE.md` (and sometimes `.claude/` skills, agents, commands).

**These files are dataset fixtures. Do NOT edit their CLAUDE.md / .claude contents** — doing so
would taint the dataset and invalidate any analysis that treats them as as-collected samples.

If you need project guidance while working *on the parabolic-fractal study itself*, put it here at
the `parabolic-fractal/` root or in a top-level `CLAUDE.md`, not inside `data/repos/*`.

Representative fixtures (non-exhaustive):
- `data/repos/baseline/aiohttp/CLAUDE.md`
- `data/repos/longitudinal/aiohttp/CLAUDE.md`
- `data/repos/agentic/{ott-platform, NewsCrawler, openclaude, J.A.R.V.I.S, django-bolt, ...}/CLAUDE.md`
