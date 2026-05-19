"""
compute_fanin.py

For each Python repo in a directory, compute intra-repo import fan-in per file.
Output: JSON file per repo -> {relative_file_path: fan_in_count}

Fan-in(f) = number of other .py files in the repo that import f.

Usage:
    python compute_fanin.py --repo-dir ../data/repos/baseline --out-dir ../data/results/baseline
    python compute_fanin.py --repo-dir ../data/repos/agentic  --out-dir ../data/results/agentic
"""

import ast
import json
import sys
import argparse
from pathlib import Path


def collect_py_files(repo_root: Path) -> list[Path]:
    return [p for p in repo_root.rglob("*.py")
            if ".git" not in p.parts and "__pycache__" not in p.parts]


def find_package_roots(repo_root: Path) -> list[Path]:
    """Return candidate roots for Python package resolution.

    Handles flat layout (root), src layout (src/), and common variants.
    Returns the repo root plus any directory named 'src' or 'lib' at depth 1.
    """
    roots = [repo_root]
    for candidate in ["src", "lib"]:
        p = repo_root / candidate
        if p.is_dir():
            roots.append(p)
    return roots


def module_name(file_path: Path, root: Path) -> str:
    """Convert a .py path to its dotted module name relative to root."""
    rel = file_path.relative_to(root)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def extract_imports(file_path: Path, repo_root: Path) -> list[str]:
    """Return list of absolute module names imported by file_path (intra-repo only)."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    imports = []
    current_module = module_name(file_path, repo_root)
    # For __init__.py, the "current package" is the module itself; for other files,
    # it's the parent package.
    if file_path.name == "__init__.py":
        current_package = current_module
    else:
        current_package = ".".join(current_module.split(".")[:-1])

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            if node.level == 0:
                imports.append(node.module)
            else:
                # relative import: resolve against current package
                parts = current_package.split(".") if current_package else []
                # go up (level - 1) packages
                up = node.level - 1
                if up > len(parts):
                    continue  # level exceeds package depth, unresolvable
                base_parts = parts[:len(parts) - up] if up < len(parts) else []
                resolved = ".".join(base_parts + [node.module]) if base_parts else node.module
                imports.append(resolved)

    return imports


def compute_fanin(repo_root: Path) -> dict[str, int]:
    py_files = collect_py_files(repo_root)
    if not py_files:
        return {}

    roots = find_package_roots(repo_root)

    # Build set of all known module names in this repo, indexed from each root.
    # __init__.py files always win for their package name — process them first
    # so that non-init files cannot overwrite the package entry via prefix registration.
    sorted_files = sorted(py_files, key=lambda p: (0 if p.name == "__init__.py" else 1))

    module_to_file: dict[str, Path] = {}
    for f in sorted_files:
        for root in roots:
            try:
                m = module_name(f, root)
                # __init__.py files unconditionally own their package name
                is_init = f.name == "__init__.py"
                if is_init or m not in module_to_file:
                    module_to_file[m] = f
                # register package prefixes (do not overwrite existing entries)
                parts = m.split(".")
                for i in range(1, len(parts)):
                    pkg = ".".join(parts[:i])
                    if pkg not in module_to_file:
                        module_to_file[pkg] = f
            except ValueError:
                continue  # file not under this root

    # Count fan-in: for each file, how many other files import it
    fanin: dict[str, int] = {str(f.relative_to(repo_root)): 0 for f in py_files}

    for f in py_files:
        # Pick the most specific (longest) root that contains this file so that
        # relative imports are resolved with the same module names used in module_to_file.
        matching = [r for r in roots if str(f).startswith(str(r))]
        file_root = max(matching, key=lambda r: len(str(r)), default=repo_root)
        for imp in extract_imports(f, file_root):
            # Find the most specific match: exact match wins over prefix match;
            # among prefix matches, the longer key wins. This prevents "click" from
            # intercepting "click.core" imports before the exact key is checked.
            best_target: Path | None = None
            best_score = -1
            for m, target in module_to_file.items():
                if imp == m:
                    score = len(m) + 10000  # exact match always beats prefix
                elif imp.startswith(m + "."):
                    score = len(m)
                else:
                    continue
                if score > best_score:
                    best_score = score
                    best_target = target
            if best_target is not None and best_target != f:
                key = str(best_target.relative_to(repo_root))
                if key in fanin:
                    fanin[key] += 1

    return fanin


def process_repo(repo_path: Path, out_dir: Path) -> None:
    out_file = out_dir / f"{repo_path.name}.json"
    if out_file.exists():
        print(f"  skip (cached): {repo_path.name}")
        return

    print(f"  processing: {repo_path.name} ...", end=" ", flush=True)
    fanin = compute_fanin(repo_path)
    if not fanin:
        print("no .py files found, skipping")
        return

    out_file.write_text(json.dumps(fanin, indent=2))
    n_files = len(fanin)
    max_fanin = max(fanin.values())
    print(f"{n_files} files, max fan-in={max_fanin}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", required=True, help="Directory containing cloned repos (one subdir per repo)")
    parser.add_argument("--out-dir", required=True, help="Directory to write JSON results")
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repos = [p for p in repo_dir.iterdir() if p.is_dir()]
    if not repos:
        print(f"No subdirectories found in {repo_dir}")
        sys.exit(1)

    print(f"Found {len(repos)} repos in {repo_dir}")
    for repo in sorted(repos):
        process_repo(repo, out_dir)

    print("Done.")


if __name__ == "__main__":
    main()
