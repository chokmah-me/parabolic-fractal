"""
audit_contamination.py

T1/T4 from the corpus-validity brief (2026-09-22):
  - T1: scan the FULL history of every baseline repo for declared-AI-attribution
    commits (same regex as find_adoption_date.py's _COMMIT_RE), unshallowing
    first if needed. Writes data/contamination-baseline.csv.
  - T4: for every repo in both baseline and agentic, record remote URL, commit
    count, shallow status, first-commit date, and attributed-commit count.
    Writes data/repos/provenance.csv.

Does not modify find_adoption_date.py's regex; imports and reuses it so the
two scripts can never silently drift apart.

Usage:
    python scripts/longitudinal/audit_contamination.py
    python scripts/longitudinal/audit_contamination.py --skip-fetch   # scan only, no network
"""

import csv
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from find_adoption_date import _COMMIT_RE  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent.parent
BASELINE_DIR = REPO_ROOT / "data" / "repos" / "baseline"
AGENTIC_DIR = REPO_ROOT / "data" / "repos" / "agentic"

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"


def _git(repo: Path, *args, timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, errors="ignore", timeout=timeout,
    )


def is_shallow(repo: Path) -> bool:
    return (repo / ".git" / "shallow").exists()


def fetch_unshallow(repo: Path, timeout: int = 600) -> tuple[bool, str]:
    """Attempt to unshallow. Returns (success, message)."""
    if not is_shallow(repo):
        return True, "already full"
    try:
        result = _git(repo, "fetch", "--unshallow", "--all", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    if result.returncode != 0:
        return False, (result.stderr.strip() or "unknown git error")[:300]
    return True, "unshallowed"


def remote_url(repo: Path) -> str:
    result = _git(repo, "remote", "get-url", "origin")
    return result.stdout.strip() or "UNKNOWN"


def scan_commits(repo: Path) -> tuple[int, int, str | None, str, str]:
    """Return (commits_scanned, attributed_commits, first_attributed_date, sample_sha, sample_subject)."""
    fmt = f"%H{FIELD_SEP}%ai{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}"
    result = _git(repo, "log", "--all", f"--format={fmt}")
    raw = result.stdout
    if not raw:
        return 0, 0, None, "", ""

    scanned = 0
    attributed = 0
    first_date = None
    sample_sha = ""
    sample_subject = ""

    for record in raw.split(RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) < 4:
            continue
        sha, date_str, subject, body = parts[0], parts[1], parts[2], parts[3]
        scanned += 1
        haystack = subject + "\n" + body
        if _COMMIT_RE.search(haystack):
            attributed += 1
            if first_date is None or date_str < first_date:
                first_date = date_str
                sample_sha = sha
                sample_subject = subject

    return scanned, attributed, first_date, sample_sha, sample_subject


def commit_count(repo: Path) -> int:
    result = _git(repo, "rev-list", "--all", "--count")
    try:
        return int(result.stdout.strip())
    except ValueError:
        return -1


def first_commit_date(repo: Path) -> str:
    result = _git(repo, "log", "--all", "--reverse", "--format=%ai", "-1")
    return result.stdout.strip().split(" ")[0] if result.stdout.strip() else ""


def process_repo(repo: Path, skip_fetch: bool) -> dict:
    shallow_before = is_shallow(repo)
    fetch_ok, fetch_msg = (True, "skipped") if skip_fetch else fetch_unshallow(repo)

    if not repo.exists():
        return {
            "repo": repo.name, "error": "MISSING_CLONE",
            "commits_scanned": -1, "attributed_commits": -1,
            "first_attributed_date": "", "sample_sha": "", "sample_subject": f"MISSING: {repo}",
            "remote_url": "", "commits": -1, "shallow": True, "first_commit_date": "",
        }

    if not fetch_ok:
        scanned, attributed, first_dt, sha, subj = scan_commits(repo)
        error_note = f"FETCH_FAILED: {fetch_msg}"
    else:
        scanned, attributed, first_dt, sha, subj = scan_commits(repo)
        error_note = ""

    return {
        "repo": repo.name,
        "error": error_note,
        "commits_scanned": scanned,
        "attributed_commits": attributed,
        "first_attributed_date": first_dt or "",
        "sample_sha": sha,
        "sample_subject": (error_note + " | " + subj) if error_note and subj else (error_note or subj),
        "remote_url": remote_url(repo),
        "commits": commit_count(repo),
        "shallow": is_shallow(repo),
        "first_commit_date": first_commit_date(repo),
    }


def write_contamination_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["repo", "commits_scanned", "attributed_commits",
              "first_attributed_date", "sample_sha", "sample_subject"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_provenance_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["repo", "group", "remote_url", "commits", "shallow",
              "first_commit_date", "attributed_commits"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true",
                         help="Scan history as-is without attempting git fetch --unshallow")
    parser.add_argument("--contamination-out",
                         default=str(REPO_ROOT / "data" / "contamination-baseline.csv"))
    parser.add_argument("--provenance-out",
                         default=str(REPO_ROOT / "data" / "repos" / "provenance.csv"))
    args = parser.parse_args()

    baseline_repos = sorted(p for p in BASELINE_DIR.iterdir() if p.is_dir())
    agentic_repos = sorted(p for p in AGENTIC_DIR.iterdir() if p.is_dir())

    contamination_rows = []
    provenance_rows = []

    print(f"Scanning {len(baseline_repos)} baseline repos...")
    for repo in baseline_repos:
        print(f"  {repo.name} ...")
        row = process_repo(repo, args.skip_fetch)
        if row["error"]:
            print(f"    ERROR: {row['error']}")
        contamination_rows.append(row)
        provenance_rows.append({**row, "group": "baseline"})

    print(f"Scanning {len(agentic_repos)} agentic repos (provenance only)...")
    for repo in agentic_repos:
        print(f"  {repo.name} ...")
        row = process_repo(repo, args.skip_fetch)
        if row["error"]:
            print(f"    ERROR: {row['error']}")
        provenance_rows.append({**row, "group": "agentic"})

    write_contamination_csv(contamination_rows, Path(args.contamination_out))
    write_provenance_csv(provenance_rows, Path(args.provenance_out))

    n_attributed = sum(1 for r in contamination_rows if r["attributed_commits"] > 0)
    print(f"\nWrote {args.contamination_out} ({len(contamination_rows)} baseline repos, "
          f"{n_attributed} with >=1 attributed commit)")
    print(f"Wrote {args.provenance_out} ({len(provenance_rows)} repos total)")


if __name__ == "__main__":
    main()
