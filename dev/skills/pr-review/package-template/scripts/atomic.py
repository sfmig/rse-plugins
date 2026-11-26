#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""The PR's branches, and the atomic copy of the PR branch.

  atomic.py extend    add the PR branch's new commits to the end of the atomic branch

The atomic branch is built once by the agent (see 2-review/1-atomic-branch.md). When
commits are added to the PR branch later, `extend` replays them on the atomic branch.
This is the only script that changes a branch: review.py only reads.

Branches: the PR branch is the one checked out (or set BRANCH=...), its atomic copy
is <branch>-atomic, and main is origin's default branch (or set MAIN=...).
"""
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip() if r.returncode == 0 else ""


def git_ok(*args):
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def is_test(path):
    """A test file: in a tests/ folder, or named test_*.py, *_test.py or conftest.py."""
    p = PurePosixPath(path)
    return (
        "tests" in p.parts[:-1]
        or p.name.startswith("test_")
        or p.name.endswith("_test.py")
        or p.name == "conftest.py"
    )


@dataclass
class Branches:
    branch: str  # the PR branch
    atomic: str  # its atomic copy, built by the agent
    base: str  # where the PR branch split off from main (full hash)

    @classmethod
    def from_git(cls):
        branch = os.environ.get("BRANCH") or git("branch", "--show-current")
        if branch.endswith("-atomic") and git_ok(
            "rev-parse", "--verify", "--quiet", f"refs/heads/{branch[:-7]}"
        ):
            branch = branch[
                :-7
            ]  # the atomic copy is checked out: review the branch it copies
        main = (
            os.environ.get("MAIN")
            or git(
                "symbolic-ref",
                "--short",
                "refs/remotes/origin/HEAD",
                check=False,
            ).removeprefix("origin/")
            or "main"
        )
        if not branch or branch == main:
            sys.exit(
                f"Check out the PR branch first (or set BRANCH=<branch>). Now on: {branch or 'no branch'}"
            )
        return cls(branch, f"{branch}-atomic", git("merge-base", main, branch))

    def has_atomic(self):
        return git_ok(
            "rev-parse", "--verify", "--quiet", f"refs/heads/{self.atomic}"
        )

    def atomic_up_to_date(self):
        return git_ok("diff", "--quiet", self.atomic, self.branch)

    def commit_matching_atomic(self):
        """The newest commit on the PR branch with the same files as the atomic tip, or None."""
        tree = git("rev-parse", f"{self.atomic}^{{tree}}")
        for row in git(
            "log", "--format=%H %T", f"{self.base}..{self.branch}"
        ).splitlines():
            sha, commit_tree = row.split()
            if commit_tree == tree:
                return sha
        return None


def extend(b):
    """Add the commits made on the PR branch after the one whose files match the atomic tip
    to the end of the atomic branch, with the same message, author and date."""
    if not b.has_atomic():
        sys.exit(
            f"No branch {b.atomic}: ask the agent to build the atomic branch first."
        )
    match = b.commit_matching_atomic()
    if not match:
        sys.exit(
            f"No commit on {b.branch} has the same files as {b.atomic} (rebased?). Ask the agent to rebuild it."
        )
    new = git("rev-list", "--reverse", f"{match}..{b.branch}").split()
    if not new:
        return print(f"{b.atomic} is up to date with {b.branch}.")
    old = tip = git("rev-parse", b.atomic)
    for c in new:  # the atomic tip has the same files as c's parent, so c's files are the result
        author = dict(
            zip(
                ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE"),
                git("log", "-1", "--format=%an%n%ae%n%aI", c).splitlines(),
            )
        )
        tip = subprocess.run(
            [
                "git",
                "commit-tree",
                f"{c}^{{tree}}",
                "-p",
                tip,
                "-m",
                git("log", "-1", "--format=%B", c),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, **author},
            check=True,
        ).stdout.strip()
    git("update-ref", f"refs/heads/{b.atomic}", tip, old)
    first = int(git("rev-list", "--count", f"{b.base}..{old}")) + 1
    print(f"Added to {b.atomic} (undo: git branch -f {b.atomic} {old[:7]}):")
    for n, row in enumerate(
        git(
            "log", "--reverse", "--format=%h %s", f"{old}..{b.atomic}"
        ).splitlines(),
        first,
    ):
        print(f"  {n:2d}  {row}")


if __name__ == "__main__":
    if sys.argv[1:] != ["extend"]:
        sys.exit(__doc__)
    os.chdir(git("rev-parse", "--show-toplevel"))
    extend(Branches.from_git())
