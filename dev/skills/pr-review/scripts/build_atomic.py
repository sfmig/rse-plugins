#!/usr/bin/env python3
"""Build the atomic copy of the PR branch from a plan: one entry per commit.

    build_atomic.py PLAN.json [--force]

Run from inside the reviewed repo. The PR branch is the checked-out one (or set
BRANCH=...); the result is the local branch <branch>-atomic, never pushed.

PLAN.json lists the commits, oldest first. Each sets some files:

    [
      {"message": "Add scikit-image dependency", "files": ["pyproject.toml"]},
      {"message": "Rename boxes_from_dataset to bbox_prompts",
       "files": ["crabs/mask/utils/boxes_from_dataset.py", "crabs/mask/utils/bbox_prompts.py"]},
      {"message": "Labels: 8-frame chunks",
       "files": [{"path": "crabs/mask/mask_video.py", "from": "stages/05/mask_video.py"}]}
    ]

  * "path": the file as it is at the PR tip; a file the tip deletes is deleted.
  * {"path": ..., "from": FILE}: the file's content at this commit, for a file whose
    changes are split over several commits. FILE is relative to PLAN.json's folder.
    Write it from the previous stage with exact string replacements.

It starts from the base (where the branch split off origin's default branch), and
commits with a temporary index: the working tree, the index and the PR branch are
not touched. The branch is created only if the last commit has the same files as
the PR tip (zero diff); else it lists the files that differ and exits with status 1.
An existing <branch>-atomic is kept unless --force; then the old tip is printed, to
undo. Middle commits are not run or tested.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "package-template" / "scripts"))
from atomic import Branches, git, git_ok  # noqa: E402


def load_plan(path):
    plan = json.loads(path.read_text())
    if not isinstance(plan, list) or not plan:
        sys.exit(f"{path}: expected a list of commits")
    commits = []
    for n, c in enumerate(plan, 1):
        if not c.get("message") or not c.get("files"):
            sys.exit(f"{path}: commit {n} needs a message and files")
        entries = []
        for f in c["files"]:
            if isinstance(f, str):
                entries.append((f, None))
            else:
                source = path.parent / f["from"]
                if not source.is_file():
                    sys.exit(f"{path}: commit {n}: no file {source}")
                entries.append((f["path"], source))
        commits.append((c["message"], entries))
    return commits


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    plan_path = Path(args[0]).resolve()
    os.chdir(git("rev-parse", "--show-toplevel"))
    b = Branches.from_git()
    commits = load_plan(plan_path)
    tip = git("rev-parse", b.branch)
    changed = set(git("diff", "--name-only", "--no-renames", b.base, tip).splitlines())

    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp) / "index")}

        def run(*a, **kw):
            r = subprocess.run(["git", *a], env=env, capture_output=True, text=True, **kw)
            if r.returncode:
                sys.exit(f"git {' '.join(a)} failed:\n{r.stderr}")
            return r.stdout.strip()

        run("read-tree", b.base)
        parent, made = b.base, []
        for n, (message, entries) in enumerate(commits, 1):
            lines = []
            for path, source in entries:
                if path not in changed:
                    print(f"Note: commit {n}: the PR does not change {path}")
                if source is None:  # as at the tip, or deleted
                    row = git("ls-tree", tip, "--", path)
                    if row:
                        info, _ = row.split("\t", 1)
                        mode, _, sha = info.split()
                        lines.append(f"{mode} {sha}\t{path}")
                    else:
                        lines.append(f"0 {'0' * 40}\t{path}")
                else:
                    row = git("ls-tree", tip, "--", path) or git("ls-tree", b.base, "--", path)
                    mode = row.split()[0] if row else "100644"
                    sha = run("hash-object", "-w", str(source))
                    lines.append(f"{mode} {sha}\t{path}")
            run("update-index", "--index-info", input="\n".join(lines) + "\n")
            tree = run("write-tree")
            if tree == git("rev-parse", f"{parent}^{{tree}}"):
                sys.exit(f"Commit {n} changes nothing: {message.splitlines()[0]}")
            parent = run("commit-tree", tree, "-p", parent, "-m", message)
            made.append(parent)

    differ = git("diff", "--name-only", parent, tip).splitlines()
    if differ:
        print(f"Not created: the last commit differs from {b.branch} in {len(differ)} file(s):")
        print("\n".join(f"  {p}" for p in differ))
        print(f"Inspect it with: git diff {parent[:12]} {tip[:12]}")
        sys.exit(1)

    old = git("rev-parse", "--verify", "--quiet", f"refs/heads/{b.atomic}", check=False)
    if old and "--force" not in sys.argv:
        sys.exit(f"{b.atomic} exists ({old[:7]}): add --force to replace it.")
    git("update-ref", f"refs/heads/{b.atomic}", parent, *([old] if old else []))
    print(f"Created {b.atomic}: {len(made)} commits, zero diff with {b.branch} ({tip[:7]}).")
    if old:
        print(f"Replaced {old[:7]} (undo: git branch -f {b.atomic} {old[:7]})")
    for n, sha in enumerate(made, 1):
        print(f"  {n:2d}  {sha[:7]}  {git('log', '-1', '--format=%s', sha)}")
    assert git_ok("diff", "--quiet", b.atomic, b.branch)


if __name__ == "__main__":
    main()
