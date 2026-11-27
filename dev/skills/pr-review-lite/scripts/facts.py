#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""The facts of a PR, as Markdown: commits, and files with a guess of which are tests.

    facts.py [BRANCH]    (default: the checked-out branch)

Run from inside the reviewed repo. Read-only. The base is where BRANCH split off
origin's default branch (or set MAIN=...).

The test guess uses common conventions for many languages (atomic.guess_test). Files
marked "unsure" have a name that suggests test code but match no convention: ask the
user about them. If <package>/tests.md exists, its `test:` files are the final answer.
"""

import os
import sys

from atomic import Branches, git, guess_test, package_dir, read_tests_md
import atomic


def files_changed(base, tip):
    """[(status, old path, new path, added, removed)] of the diff base..tip."""
    numstat = {}
    for row in git("diff", "--numstat", "-M", base, tip).splitlines():
        added, removed, path = row.split("\t", 2)
        if " => " in path:
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
        return (head + middle.split(" => ")[1] + tail).replace("//", "/")
    return path.split(" => ")[1]


def main():
    if len(sys.argv) > 2 or sys.argv[1:2] in (["-h"], ["--help"]):
        sys.exit(__doc__)
    if len(sys.argv) == 2:
        os.environ["BRANCH"] = sys.argv[1]
    os.chdir(git("rev-parse", "--show-toplevel"))
    b = Branches.from_git()
    package = package_dir()
    read_tests_md(package / "tests.md")
    tip = git("rev-parse", b.branch)
    commits = git("log", "--reverse", "--format=%h %s", f"{b.base}..{b.branch}").splitlines()
    files = files_changed(b.base, tip)
    total = lambda i: sum(int(f[i]) for f in files if f[i].isdigit())

    rows = []
    for status, old, new, added, removed in files:
        test, why, unsure = guess_test(new)
        if atomic.TEST_LIST is not None:
            test, why, unsure = new in atomic.TEST_LIST, "tests.md", False
        rows.append((status, old, new, added, removed, test, why, unsure))
    n_tests = sum(r[5] for r in rows)

    print(f"# Facts: `{b.branch}`\n")
    print("| | |\n|---|---|")
    print(f"| Base | `{b.base[:7]}` (merge base with the default branch) |")
    print(f"| Tip | `{tip[:7]}` |")
    print(f"| Commits | {len(commits)} |")
    print(f"| Files | {len(files)} ({len(files) - n_tests} code, {n_tests} test) |")
    print(f"| Lines | +{total(3)}/-{total(4)} |")
    print(f"| Atomic branch | `{b.atomic}` {'exists' if b.has_atomic() else 'not built'} |")
    print(f"| Package | `{package.name}/` {'exists' if package.exists() else 'not made'}"
          f"{', tests.md set' if atomic.TEST_LIST is not None else ''} |\n")

    print("## Commits, oldest first\n")
    print("\n".join(f"{n}. `{c[:7]}` {c[8:]}" for n, c in enumerate(commits, 1)) + "\n")

    print("## Files\n")
    print("| File | +/- | Kind | Why | Status |\n|---|---|---|---|---|")
    for status, old, new, added, removed, test, why, unsure in rows:
        name = f"`{new}`" if old == new else f"`{old}` → `{new}`"
        kind = "**unsure**" if unsure else ("test" if test else "code")
        print(f"| {name} | +{added}/-{removed} | {kind} | {why} | {status} |")
    unsure = [r[2] for r in rows if r[7]]
    if unsure:
        print("\nUnsure, ask the user: " + ", ".join(f"`{p}`" for p in unsure))


if __name__ == "__main__":
    main()
