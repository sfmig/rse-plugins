#!/usr/bin/env python3
"""List top-level functions and constants that differ between two git revisions.

Deterministic input for the signatures view of a PR review: no LLM involved.
Run from inside the reviewed repo:

    python signature_changes.py BASE TIP [PATH ...]

PATH limits the search (default: the whole repo). Only changed .py files are parsed.
Reports, per file: added / removed / changed
  - functions (def, async def): parameters or return annotation differ
  - UPPER_CASE module constants: value differs
Not covered: class methods, nested functions, behaviour changes inside a body.
A function moved between files shows as removed in one and added in the other.
"""

import ast
import subprocess
import sys


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def top_level(rev: str, path: str) -> dict[str, str]:
    """Map 'def name' / 'const NAME' to its signature or value at rev."""
    shown = git("show", f"{rev}:{path}")
    if shown.returncode:  # file absent at this revision
        return {}
    out = {}
    for node in ast.parse(shown.stdout).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            returns = ast.unparse(node.returns) if node.returns else ""
            out[f"def {node.name}"] = f"({ast.unparse(node.args)}) -> {returns}"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and target.id.isupper() and node.value:
                out[f"const {target.id}"] = ast.unparse(node.value)
    return out


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    base, tip, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    names = git("diff", "--name-only", base, tip, "--", *paths).stdout.split()
    for path in (p for p in names if p.endswith(".py")):
        before, after = top_level(base, path), top_level(tip, path)
        for key in sorted(before.keys() | after.keys()):
            if before.get(key) == after.get(key):
                continue
            status = (
                "added" if key not in before else "removed" if key not in after else "changed"
            )
            print(f"{path}\t{status}\t{key}\t{after.get(key, before.get(key))}")


if __name__ == "__main__":
    main()
