"""
walk_history.py

Walk a repo's git history at monthly snapshots (pre- and post-adoption),
compute fan-in at each snapshot, and save results to data/longitudinal/{repo}/.

Requires a FULL clone (not shallow) to access history.

Usage:
    python walk_history.py --repo /path/to/repo --adoption-date 2024-06-01
        --out-dir ../../data/longitudinal --pre-months 24 --post-months 12
"""

import json
import sys
import argparse
import subprocess
from datetime import date, timedelta
from pathlib import Path

# Allow importing from parent scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from compute_fanin import compute_fanin


def _git(repo: Path, *args) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, errors="ignore"
    )
    return result.stdout.strip()


def _commit_before(repo: Path, target_date: date, tip: str = "HEAD") -> str | None:
    """Return the last commit hash before (or on) target_date, or None.

    tip must be a stable ref (branch name or full SHA) — not HEAD if the repo
    may be in detached-HEAD state during iteration.
    """
    out = _git(repo, "rev-list", "-n", "1",
               f"--before={target_date.isoformat()}T23:59:59", tip)
    return out if out else None


def _month_range(start: date, end: date) -> list[date]:
    """Return first-of-month dates from start to end inclusive."""
    months = []
    cur = start.replace(day=1)
    while cur <= end:
        months.append(cur)
        # advance one month
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return months


def _is_shallow(repo: Path) -> bool:
    return (repo / ".git" / "shallow").exists()


def walk(repo: Path, adoption_date: date, out_dir: Path,
         pre_months: int = 24, post_months: int = 12) -> None:
    if _is_shallow(repo):
        print(f"  ERROR: {repo.name} is a shallow clone. Re-clone without --depth 1.")
        print(f"  Run: git clone https://... {repo}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    pre_start = adoption_date - timedelta(days=30 * pre_months)
    post_end_ideal = adoption_date + timedelta(days=30 * post_months)
    today = date.today()
    post_end = min(post_end_ideal, today)

    snapshots = _month_range(pre_start, post_end)
    print(f"  {len(snapshots)} snapshots from {pre_start} to {post_end}")

    # Save current HEAD so we can restore it, and capture the tip SHA to use
    # as a stable starting point for rev-list (HEAD changes on git checkout --detach)
    original_branch = _git(repo, "symbolic-ref", "--short", "HEAD")
    if not original_branch:
        original_branch = _git(repo, "rev-parse", "HEAD")
    tip_sha = _git(repo, "rev-parse", "HEAD")

    try:
        for snap_date in snapshots:
            out_file = out_dir / f"{snap_date.isoformat()}.json"
            if out_file.exists():
                print(f"    skip (cached): {snap_date}")
                continue

            commit = _commit_before(repo, snap_date, tip=tip_sha)
            if commit is None:
                print(f"    no commit before {snap_date}, skipping")
                continue

            # Detach HEAD to the snapshot commit
            subprocess.run(
                ["git", "-C", str(repo), "checkout", "--quiet", "--detach", commit],
                capture_output=True
            )

            fanin = compute_fanin(repo)

            result = {
                "date": snap_date.isoformat(),
                "commit": commit,
                "is_post": snap_date >= adoption_date,
                "fanin": fanin,
            }
            out_file.write_text(json.dumps(result, indent=2))
            n = len(fanin)
            print(f"    {snap_date}  {'POST' if result['is_post'] else 'pre ':4s}  "
                  f"commit={commit[:8]}  files={n}")
    finally:
        # Always restore original state
        subprocess.run(
            ["git", "-C", str(repo), "checkout", "--quiet", original_branch],
            capture_output=True
        )
        print(f"  Restored to {original_branch}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--adoption-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--pre-months", type=int, default=24)
    parser.add_argument("--post-months", type=int, default=12)
    args = parser.parse_args()

    repo = Path(args.repo)
    adoption_date = date.fromisoformat(args.adoption_date)
    out_dir = Path(args.out_dir) / repo.name

    print(f"Walking {repo.name} (adoption: {adoption_date})")
    walk(repo, adoption_date, out_dir, args.pre_months, args.post_months)
    print("Done.")


if __name__ == "__main__":
    main()
