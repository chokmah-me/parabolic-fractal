"""
audit_contamination.py

T1/T4 from the corpus-validity brief (2026-09-22):
  - T1: scan every baseline repo for declared-AI-attribution commits (same
    regex as find_adoption_date.py's _COMMIT_RE), unshallowing first if needed,
    in two scopes: commits reachable from local HEAD (the snapshot the
    cross-sectional fan-in was measured on) and commits on all refs (history
    up to the fetch date). Writes data/contamination-baseline.csv.
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


def attributed_commits(repo: Path, rev: str) -> tuple[int, list[dict]]:
    """Return (commits_scanned, attributed) for commits reachable from rev ("--all" or a ref)."""
    fmt = f"%H{FIELD_SEP}%ai{FIELD_SEP}%an{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}"
    raw = _git(repo, "log", rev, f"--format={fmt}").stdout
    scanned = 0
    hits = []
    for record in raw.split(RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) < 5:
            continue
        sha, date_str, author, subject, body = parts[:5]
        scanned += 1
        if _COMMIT_RE.search(subject + "\n" + body):
            hits.append({"sha": sha, "date": date_str, "author": author, "subject": subject})
    return scanned, hits


def summarize(scanned: int, hits: list[dict], prefix: str) -> dict:
    first = min(hits, key=lambda h: h["date"]) if hits else None
    authors: dict[str, int] = {}
    for h in hits:
        authors[h["author"]] = authors.get(h["author"], 0) + 1
    top = max(authors.items(), key=lambda kv: kv[1]) if authors else ("", 0)
    return {
        f"commits_{prefix}": scanned,
        f"attributed_{prefix}": len(hits),
        f"first_attributed_{prefix}": first["date"] if first else "",
        f"first_sha_{prefix}": first["sha"] if first else "",
        f"first_subject_{prefix}": first["subject"] if first else "",
        f"top_author_{prefix}": top[0],
        f"top_author_count_{prefix}": top[1],
    }


def commit_count(repo: Path) -> int:
    result = _git(repo, "rev-list", "--all", "--count")
    try:
        return int(result.stdout.strip())
    except ValueError:
        return -1


def first_commit_date(repo: Path) -> str:
    roots = _git(repo, "rev-list", "--max-parents=0", "--all").stdout.split()
    dates = [_git(repo, "log", "-1", "--format=%ad", "--date=short", r).stdout.strip() for r in roots]
    dates = [d for d in dates if d]
    return min(dates) if dates else ""


def process_repo(repo: Path, skip_fetch: bool) -> dict:
    if not repo.exists():
        return {"repo": repo.name, "error": f"MISSING_CLONE: {repo}", "commits": -1, "shallow": True}

    fetch_ok, fetch_msg = (True, "skipped") if skip_fetch else fetch_unshallow(repo)
    # Local HEAD is the commit the cross-sectional fan-in was computed on;
    # --unshallow --all moves only remote refs, never HEAD.
    snap_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    snap_date = _git(repo, "log", "-1", "--format=%ad", "--date=short", "HEAD").stdout.strip()

    row = {
        "repo": repo.name,
        "error": "" if fetch_ok else f"FETCH_FAILED: {fetch_msg}",
        "snapshot_sha": snap_sha,
        "snapshot_date": snap_date,
        "remote_url": remote_url(repo),
        "commits": commit_count(repo),
        "shallow": is_shallow(repo),
        "first_commit_date": first_commit_date(repo),
    }
    if row["commits"] < 0 and not row["error"]:
        row["error"] = "UNREADABLE_HISTORY"
    row["last_commit_date"] = _git(repo, "log", "--all", "-1", "--format=%ad", "--date=short").stdout.strip()
    n_snap, snap_hits = attributed_commits(repo, "HEAD")
    n_all, all_hits = attributed_commits(repo, "--all")
    row.update(summarize(n_snap, snap_hits, "at_snapshot"))
    row.update(summarize(n_all, all_hits, "all_refs"))
    snap_shas = {h["sha"] for h in snap_hits}
    row["_hits"] = [{"repo": repo.name, **h, "at_snapshot": h["sha"] in snap_shas} for h in all_hits]
    return row


def write_hits_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["repo", "sha", "date", "author", "at_snapshot", "subject"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerows(sorted(row.get("_hits", []), key=lambda h: h["date"]))


def write_contamination_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["repo", "error", "snapshot_sha", "snapshot_date"]
    for scope in ("at_snapshot", "all_refs"):
        fields += [f"commits_{scope}", f"attributed_{scope}", f"first_attributed_{scope}",
                   f"first_sha_{scope}", f"first_subject_{scope}",
                   f"top_author_{scope}", f"top_author_count_{scope}"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_provenance_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["repo", "group", "error", "remote_url", "commits", "shallow",
              "first_commit_date", "snapshot_date", "last_commit_date",
              "attributed_at_snapshot", "attributed_all_refs"]
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
    write_hits_csv(contamination_rows, Path(args.contamination_out).with_name("attributed-commits-baseline.csv"))

    for scope in ("at_snapshot", "all_refs"):
        hit = sum(1 for r in contamination_rows if r.get(f"attributed_{scope}", 0) > 0)
        tot = sum(r.get(f"attributed_{scope}", 0) for r in contamination_rows)
        n = sum(r.get(f"commits_{scope}", 0) for r in contamination_rows)
        print(f"{scope}: {tot} attributed / {n} commits, {hit} of {len(contamination_rows)} repos")
    print(f"Wrote {args.contamination_out}")
    print(f"Wrote {args.provenance_out} ({len(provenance_rows)} repos total)")


if __name__ == "__main__":
    main()
