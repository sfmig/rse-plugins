#!/usr/bin/env python3
"""Check a PR review package before handing it to the reviewer.

    check_package.py [FOLDER]    (default: pr-review, at the repo root)

Run from inside the reviewed repo, with the PR branch checked out. Checks:

  1. Each page has exactly one "# " heading, on its first line (it becomes the tab name).
  2. Each `path:N` or `path:N-M` anchor in the pages names a file that exists, with
     that many lines, at the commit code-base-url pins (else at the branch tip).
  3. Each preloaded question sits on a line the PR adds (new side of base..branch):
     difit may not show a comment on any other line.
  4. review.py can read the tables: sessions, test steps, commit weights; every
     changed test file is in a test step.

Mermaid diagrams are not checked here: use the proposal skill's check-mermaid.sh.
Prints one line per problem; exit status 1 if there is any, 0 otherwise.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ANCHOR = re.compile(r"`([\w./-]+\.[\w]+):(\d+)(?:-(\d+))?`")
PAGES = ["1-general/1-aim.md", "2-review/1-atomic-branch.md", "2-review/2-code.md", "2-review/3-tests.md"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout if r.returncode == 0 else None


def headings(text):
    """The "# " lines of a page, outside code fences."""
    out, fence = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            fence = not fence
        elif not fence and line.startswith("# "):
            out.append(n)
    return out


def added_lines(base, tip):
    """{path: set of new-side line numbers the diff base..tip adds}."""
    out, path = {}, None
    for row in git("diff", "-U0", "-M", base, tip).splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
        elif row.startswith("@@") and path:
            m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))?", row)
            start, count = int(m[1]), int(m[2] or 1)
            out.setdefault(path, set()).update(range(start, start + count))
    return out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "pr-review"
    root = Path(git("rev-parse", "--show-toplevel").strip())
    package = root / name
    if not (package / "scripts" / "review.py").exists():
        sys.exit(f"No package at {package}: run init_package.py first.")
    sys.path.insert(0, str(package / "scripts"))
    import review  # the package's own: reads the tables as the review will
    from atomic import Branches, is_test

    problems = []
    b = Branches.from_git()
    tip = git("rev-parse", b.branch).strip()

    quarto = (package / "_quarto.yml").read_text()
    pinned = re.search(r"^code-base-url: .*/blob/([0-9a-f]{7,40})/", quarto, re.M)
    at = pinned[1] if pinned else tip
    if not pinned:
        problems.append("_quarto.yml: code-base-url is not a GitHub blob URL pinned to a commit")
    elif not tip.startswith(at):
        print(f"Note: pages are pinned to {at[:7]}; the branch tip is {tip[:7]}.")

    # 1, 2: pages
    for page in PAGES:
        path = package / page
        if not path.exists():
            problems.append(f"{page}: missing")
            continue
        text = path.read_text()
        h = headings(text)
        if h != [1]:
            problems.append(f"{page}: needs exactly one '# ' heading, on line 1 (found on lines {h})")
        for n, line in enumerate(text.splitlines(), 1):
            for m in ANCHOR.finditer(line):
                file, first, last = m[1], int(m[2]), int(m[3] or m[2])
                content = git("show", f"{at}:{file}", check=False)
                if content is None:
                    problems.append(f"{page}:{n}: {file} not in {at[:7]}")
                elif last > len(content.splitlines()):
                    problems.append(f"{page}:{n}: {file} has {len(content.splitlines())} lines at {at[:7]}, anchor says {last}")

    # 3: questions on added lines
    added = added_lines(b.base, tip)
    for review_name in ("code", "tests"):
        qpath = package / "2-review" / f"questions-{review_name}.json"
        if not qpath.exists():
            continue
        for q in json.loads(qpath.read_text()):
            pos, file = q["position"], q["filePath"]
            line = pos["line"]
            lines = [line] if isinstance(line, int) else [line["start"], line["end"]]
            if pos.get("side") != "new" or not all(l in added.get(file, ()) for l in lines):
                problems.append(f"{qpath.name}: not on an added line: {file}:{line} ({q['body'][:40]})")
            if review_name == "code" and is_test(file):
                problems.append(f"{qpath.name}: on a test file, so the code review will not show it: {file}")

    # 4: tables review.py reads (a missing page is reported above)
    if not (review.SESSIONS.exists() and review.TESTS.exists() and review.COMMIT_LIST.exists()):
        for p in problems:
            print("FAIL", p)
        sys.exit(1)
    sessions = review.session_items(b)
    if not sessions:
        problems.append("2-code.md: no rows in the session plan table")
    for it in sessions:
        if not it.files:
            problems.append(f"2-code.md: session {it.number} has no file changed by the PR")
    steps = review.test_items(b)  # prints the changed test files that are in no step
    changed_tests = {p for p in review.changed_files(b.base, b.branch) if is_test(p)}
    in_steps = set().union(*(s.files for s in steps)) if steps else set()
    if changed_tests - in_steps:
        problems.append("3-tests.md: some changed test files are in no test step (listed above)")
    if b.has_atomic():
        n_commits = len(git("rev-list", f"{b.base}..{b.atomic}").split())
        if len(review.weights()) != n_commits:
            problems.append(f"1-atomic-branch.md: {len(review.weights())} commits with a weight, the atomic branch has {n_commits}")
    else:
        problems.append(f"no branch {b.atomic}: build the atomic branch first")

    for p in problems:
        print("FAIL", p)
    print(f"{len(problems)} problem(s)." if problems else "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
