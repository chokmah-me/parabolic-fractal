"""
aggregate_timeline.py

Compile per-snapshot JSONs from walk_history.py into a timeline CSV.

Usage:
    python aggregate_timeline.py --repo-dir ../../data/longitudinal/my_repo
        --out ../../data/longitudinal/my_repo/timeline.csv
    # or process all repos at once:
    python aggregate_timeline.py --longitudinal-dir ../../data/longitudinal
"""

import json
import csv
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from fit_distributions import metrics_from_fanin

FIELDS = [
    "repo", "date", "commit", "is_post",
    "n_files", "n_files_pos_fanin", "frac_leaves",
    "max_fanin", "mean_fanin", "gini", "entropy_norm",
    "r2_powerlaw", "r2_lognormal",
    "aic_powerlaw", "aic_lognormal",
    "bic_powerlaw", "bic_lognormal",
    "delta_aic", "lognormal_wins",
    "vuong_z", "vuong_p", "lognormal_coeff_c",
]


def process_repo_dir(repo_dir: Path) -> list[dict]:
    rows = []
    repo_name = repo_dir.name
    snapshots = sorted(repo_dir.glob("????-??-??.json"))
    if not snapshots:
        return rows

    for snap_path in snapshots:
        snap = json.loads(snap_path.read_text())
        metrics = metrics_from_fanin(snap["fanin"], repo_name, group="longitudinal")
        if metrics is None:
            print(f"  skip (too few connected files): {snap['date']}")
            continue
        row = {
            "repo": repo_name,
            "date": snap["date"],
            "commit": snap["commit"],
            "is_post": snap["is_post"],
        }
        row.update({k: metrics[k] for k in metrics if k not in ("repo", "group")})
        rows.append(row)

    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  Written: {out_path} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo-dir", help="Single repo snapshot directory")
    group.add_argument("--longitudinal-dir", help="Parent dir containing multiple repo dirs")
    parser.add_argument("--out", help="Output CSV path (only for --repo-dir)")
    args = parser.parse_args()

    if args.repo_dir:
        repo_dir = Path(args.repo_dir)
        rows = process_repo_dir(repo_dir)
        out = Path(args.out) if args.out else repo_dir / "timeline.csv"
        write_csv(rows, out)
    else:
        long_dir = Path(args.longitudinal_dir)
        for repo_dir in sorted(long_dir.iterdir()):
            if not repo_dir.is_dir():
                continue
            if not list(repo_dir.glob("????-??-??.json")):
                continue
            print(f"Processing {repo_dir.name} ...")
            rows = process_repo_dir(repo_dir)
            write_csv(rows, repo_dir / "timeline.csv")


if __name__ == "__main__":
    main()
