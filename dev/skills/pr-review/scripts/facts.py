#!/usr/bin/env python3
"""The facts of a PR, as Markdown: commits, files, and the functions it changes.

    facts.py [BRANCH]    (default: the checked-out branch)

Run from inside the reviewed repo. Read-only. The base is where BRANCH split off
origin's default branch (or set MAIN=...). Prints:

  * the PR: branch, base, tip, commits, files and lines changed;
  * the commits, oldest first;
  * the files: lines added and removed, code or test, status (A, M, D, R);
  * the functions and constants of the changed .py files that are added, removed,
    or changed: signature (parameters, return annotation, constant value) or body
    only. Code and tests in separate tables.

Covered: top-level functions, methods of top-level classes (`Class.method`),
UPPER_CASE module constants. Not covered: nested functions, non-Python files.
A function moved between files shows as removed in one and added in the other.
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "package"))
from atomic import Branches, git, is_test  # noqa: E402


def files_changed(base, tip):
    """[(status, old path, new path, added, removed)] of the diff base..tip."""
    numstat = {}
    for row in git("diff", "--numstat", "-M", base, tip).splitlines():
        added, removed, path = row.split("\t", 2)
        if " => " in path:  # a rename: "dir/{a => b}/f.py" or "a.py => b.py"
            path = rename_target(path)
        numstat[path] = (added, removed)
    out = []
    for row in git("diff", "--name-status", "-M", base, tip).splitlines():
        status, *paths = row.split("\t")
        old, new = paths[0], paths[-1]
        added, removed = numstat.get(new, ("?", "?"))
        out.append((status[0], old, new, added, removed))
    return out


def rename_target(path):
    """The new path of a --numstat rename ("a/{b => c}/d" -> "a/c/d")."""
    if "{" in path:
        head, rest = path.split("{", 1)
        middle, tail = rest.split("}", 1)
        new = middle.split(" => ")[1]
        return (head + new + tail).replace("//", "/")
    return path.split(" => ")[1]


def definitions(rev, path):
    """{'def name' / 'def Class.name' / 'const NAME': (signature, body dump)} at rev."""
    text = git("show", f"{rev}:{path}", check=False)
    if not text:
        return {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}
    out = {}

    def add_function(node, prefix=""):
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        out[f"def {prefix}{node.name}"] = (f"({ast.unparse(node.args)}){returns}", ast.dump(node))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add_function(node)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    add_function(item, f"{node.name}.")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value:
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and target.id.isupper():
                value = ast.unparse(node.value)
                out[f"const {target.id}"] = (value, value)
    return out


def changes(base, tip, old, new):
    """[(change, name, signature)] between old at base and new at tip."""
    before, after = definitions(base, old), definitions(tip, new)
    rows = []
    for key in sorted(before.keys() | after.keys()):
        b, a = before.get(key), after.get(key)
        if b == a:
            continue
        if b is None:
            change = "added"
        elif a is None:
            change = "removed"
        elif b[0] != a[0]:
            change = "value" if key.startswith("const") else "signature"
        else:
            change = "body"
        rows.append((change, key, (a or b)[0]))
    return rows


def cell(text, width=80):
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def main():
    if len(sys.argv) > 2 or sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(__doc__)
    if len(sys.argv) == 2:
        os.environ["BRANCH"] = sys.argv[1]
    os.chdir(git("rev-parse", "--show-toplevel"))
    b = Branches.from_git()
    tip = git("rev-parse", b.branch)
    commits = git("log", "--reverse", "--format=%h %s", f"{b.base}..{b.branch}").splitlines()
    files = files_changed(b.base, tip)
    total = lambda i: sum(int(f[i]) for f in files if f[i].isdigit())

    print(f"# Facts: `{b.branch}`\n")
    print("| | |\n|---|---|")
    print(f"| Base | `{b.base[:7]}` (merge base with the default branch) |")
    print(f"| Tip | `{tip[:7]}` |")
    print(f"| Commits | {len(commits)} |")
    n_tests = sum(is_test(f[2]) for f in files)
    print(f"| Files | {len(files)} ({len(files) - n_tests} code, {n_tests} test) |")
    print(f"| Lines | +{total(3)}/-{total(4)} |")
    print(f"| Atomic branch | `{b.atomic}` {'exists' if b.has_atomic() else 'not built'} |\n")

    print("## Commits, oldest first\n")
    print("\n".join(f"{n}. `{c[:7]}` {c[8:]}" for n, c in enumerate(commits, 1)) + "\n")

    print("## Files\n")
    print("| File | +/- | Kind | Status |\n|---|---|---|---|")
    for status, old, new, added, removed in files:
        name = f"`{new}`" if old == new else f"`{old}` → `{new}`"
        print(f"| {name} | +{added}/-{removed} | {'test' if is_test(new) else 'code'} | {status} |")
    print()

    rows = {"code": [], "test": []}
    for status, old, new, _, _ in files:
        if not new.endswith(".py"):
            continue
        for change, name, signature in changes(b.base, tip, old, new if status != "D" else old):
            rows["test" if is_test(new) else "code"].append((new, change, name, signature))
    for kind, title in (("code", "Functions and constants changed: code"),
                        ("test", "Functions changed: tests")):
        print(f"## {title}\n")
        if not rows[kind]:
            print("None.\n")
            continue
        print("| File | Change | Name | Signature or value |\n|---|---|---|---|")
        for path, change, name, signature in rows[kind]:
            print(f"| `{path}` | {change} | `{name}` | `{cell(signature)}` |")
        print()
    print("Change: added, removed, signature (parameters or return differ), value (of a "
          "constant), body (same signature, different code).")


if __name__ == "__main__":
    main()
