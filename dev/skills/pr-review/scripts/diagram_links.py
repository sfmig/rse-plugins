#!/usr/bin/env python3
"""The links of a flow diagram: mermaid `click` lines and the links table under it.

    diagram_links.py BOXES [FOLDER]    (FOLDER default: pr-review, at the repo root)

Run from inside the reviewed repo, after init_package.py. BOXES is a text file, one
box per line: its mermaid ID, its label, and its code anchors, call site first and
definition last, separated by " | ":

    A | Load config: merged with defaults | crabs/mask/mask_video.py:538 crabs/mask/mask_video.py:55
    B | Shard check | crabs/mask/mask_video.py:543

Prints, to paste into 1-general/1-aim.md:
  * the `click` lines: each box opens its last anchor (the definition) on GitHub,
    at the commit code-base-url in FOLDER/_quarto.yml pins;
  * the links table (| Step | Code |), with links relative to the page;
  * a short anchor label for each box, like "mv:538 to mv:55" (file initials).
Then, on stderr, each anchored line of code at that commit, to check by eye that it is
the right line. Exit status 1 if an anchor names a missing file or line.
"""

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

PAGE_DEPTH = "../../"  # from 1-general/1-aim.md to the repo root


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def initials(path):
    return "".join(w[0] for w in PurePosixPath(path).stem.split("_") if w)


def main():
    if not 2 <= len(sys.argv) <= 3 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    boxes_file = Path(sys.argv[1])
    root = Path(git("rev-parse", "--show-toplevel").strip())
    quarto = root / (sys.argv[2] if len(sys.argv) == 3 else "pr-review") / "_quarto.yml"
    if not quarto.exists():
        sys.exit(f"No {quarto}: run init_package.py first.")
    m = re.search(r"^code-base-url: (\S+/blob/([0-9a-f]{7,40})/)", quarto.read_text(), re.M)
    if not m:
        sys.exit(f"{quarto}: code-base-url is not a GitHub blob URL pinned to a commit.")
    url, rev = m[1], m[2]

    boxes = []
    for n, row in enumerate(boxes_file.read_text().splitlines(), 1):
        if not row.strip() or row.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in row.split("|")]
        if len(parts) != 3 or not parts[2]:
            sys.exit(f"{boxes_file}:{n}: expected 'ID | label | path:line [path:line ...]'")
        anchors = []
        for a in parts[2].split():
            path, _, line = a.rpartition(":")
            if not path or not line.isdigit():
                sys.exit(f"{boxes_file}:{n}: bad anchor {a!r}")
            anchors.append((path, int(line)))
        boxes.append((parts[0], parts[1], anchors))

    paths = sorted({p for _, _, anchors in boxes for p, _ in anchors})
    short = {p: initials(p) for p in paths}
    clash = {s for s in short.values() if list(short.values()).count(s) > 1}
    short = {p: (PurePosixPath(p).stem if s in clash else s) for p, s in short.items()}

    problems, checks = [], []
    for path in paths:
        text = git("show", f"{rev}:{path}")
        lines = text.splitlines() if text is not None else None
        for box, _, anchors in boxes:
            for p, line in anchors:
                if p != path:
                    continue
                if lines is None:
                    problems.append(f"{box}: {path} not in {rev[:7]}")
                elif line > len(lines):
                    problems.append(f"{box}: {path} has {len(lines)} lines at {rev[:7]}, anchor says {line}")
                else:
                    checks.append(f"{box:>4}  {short[p]}:{line:<5} {lines[line - 1].strip()[:90]}")

    print("Click lines:\n")
    for box, _, anchors in boxes:
        path, line = anchors[-1]
        print(f'    click {box} href "{url}{path}#L{line}" "{path}:{line}" _blank')
    print("\nLinks table:\n")
    print("| Step | Code |\n|---|---|")
    for _, label, anchors in boxes:
        name, sep, rest = label.partition(": ")
        step = f"**{name}**: {rest}" if sep else f"**{label}**"
        code = ", ".join(f"[{short[p]}:{n}]({PAGE_DEPTH}{p}#L{n})" for p, n in anchors)
        print(f"| {step} | {code} |")
    print("\nAnchor labels for the boxes:\n")
    for box, _, anchors in boxes:
        print(f"    {box}: " + " to ".join(f"{short[p]}:{n}" for p, n in anchors))
    print("\nFiles: " + ", ".join(f"{s} = `{p}`" for p, s in short.items()))

    print(f"\nAnchored lines at {rev[:7]}, to check:", file=sys.stderr)
    print("\n".join(checks), file=sys.stderr)
    for p in problems:
        print("FAIL", p, file=sys.stderr)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
