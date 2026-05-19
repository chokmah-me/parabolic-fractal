"""
collect_repos.py

Clone the curated baseline and agentic repo lists into data/repos/.
Shallow clone (depth=1) to save space.

Usage:
    python collect_repos.py --group baseline
    python collect_repos.py --group agentic
    python collect_repos.py --group all
"""

import subprocess
import argparse
from pathlib import Path

BASELINE_REPOS = [
    # Python — mature OSS
    "https://github.com/django/django",
    "https://github.com/pallets/flask",
    "https://github.com/numpy/numpy",
    "https://github.com/pandas-dev/pandas",
    "https://github.com/sqlalchemy/sqlalchemy",
    "https://github.com/celery/celery",
    "https://github.com/tiangolo/fastapi",
    "https://github.com/psf/requests",
    "https://github.com/pytest-dev/pytest",
    "https://github.com/scrapy/scrapy",
    "https://github.com/encode/httpx",
    "https://github.com/pydantic/pydantic",
    "https://github.com/aio-libs/aiohttp",
    "https://github.com/tornadoweb/tornado",
    "https://github.com/pallets/click",
]

# Agentic repos: known vibe-coded / AI-generated projects (2024-2025)
# These should be reviewed and extended manually before running the full study.
# Inclusion criteria: repo created 2024+, README or commit history references AI tooling,
# or self-describes as AI/agent-generated.
AGENTIC_REPOS = [
    "https://github.com/stefanros481/ott-platform",      # CLAUDE.md, FastAPI OTT backend, 67 commits
    "https://github.com/SteppieD/tradinggame",           # "Built with Claude Code", .claude/agents/, 72.8% Python
    "https://github.com/rdumasia303/deepseek_ocr_app",   # "vibe coded", FastAPI+PyTorch OCR backend
    "https://github.com/jandrews65/zhang2025",           # "Built with Claude Code", macro ML pipeline
    "https://github.com/NanmiCoder/NewsCrawler",         # CLAUDE.md, FastAPI+MCP crawler
    "https://github.com/sitcon-tw/camp2025-stock",       # CLAUDE.md, FastAPI DDD backend, 55.5% Python
    "https://github.com/is0383kk/openclaude",            # README "Built with claude-agent-sdk"
    "https://github.com/marvingreenberg/fqf",            # CLAUDE.md, FastAPI backend, 151 commits
    "https://github.com/asklokesh/loki-mode",            # CLAUDE.md, FastAPI 100+ endpoints, multi-agent
    "https://github.com/yusufkaraaslan/lazy-bird",       # "Built with Claude Code", FastAPI+Celery
    "https://github.com/coleam00/dark-factory-experiment", # CLAUDE.md+FACTORY_RULES.md, asyncpg, uv
    "https://github.com/dj-bolt/django-bolt",            # CLAUDE.md, Rust/Python Django framework
    "https://github.com/triepod-ai/claude-cli-rest-api", # CLAUDE.md, FastAPI MCP wrapper
    "https://github.com/MinBZK/poc-machine-law",         # CLAUDE.md, uv, Python simulation backend
]

BASE_DIR = Path(__file__).parent.parent / "data" / "repos"


def clone(url: str, target_dir: Path) -> None:
    name = url.rstrip("/").split("/")[-1]
    dest = target_dir / name
    if dest.exists():
        print(f"  skip (exists): {name}")
        return
    print(f"  cloning: {name} ...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--quiet", url, str(dest)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ERROR cloning {url}: {result.stderr.strip()}")
    else:
        print(f"  ok: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["baseline", "agentic", "all"], default="all")
    args = parser.parse_args()

    if args.group in ("baseline", "all"):
        dest = BASE_DIR / "baseline"
        dest.mkdir(parents=True, exist_ok=True)
        print(f"\nCloning baseline repos -> {dest}")
        for url in BASELINE_REPOS:
            clone(url, dest)

    if args.group in ("agentic", "all"):
        dest = BASE_DIR / "agentic"
        dest.mkdir(parents=True, exist_ok=True)
        print(f"\nCloning agentic repos -> {dest}")
        if not AGENTIC_REPOS:
            print("  NOTE: AGENTIC_REPOS list is empty. Populate it before running.")
        for url in AGENTIC_REPOS:
            clone(url, dest)

    print("\nDone.")


if __name__ == "__main__":
    main()
