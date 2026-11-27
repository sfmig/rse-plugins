#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""The PR's branches, the atomic copy of the PR branch, and which files are tests.

  atomic.py extend    add the PR branch's new commits to the end of the atomic branch

The atomic branch is built once by the agent (build_atomic.py). When
commits are added to the PR branch later, `extend` replays them on the atomic branch.
This is the only script that changes a branch: review.py only reads.

Branches: the PR branch is the one checked out (or set BRANCH=...), its atomic copy
is <branch>-atomic, and main is origin's default branch (or set MAIN=...).
"""
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip() if r.returncode == 0 else ""


def git_ok(*args):
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


# ------------------------------------------------------------------ test files
# A guess from common conventions. The agent checks it, asks the user when unsure,
# and writes <package>/tests.md, whose `test:` files then win (read_tests_md).

TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testthat", "androidTest"}
TEST_NAMES = [  # (regex on the file name, convention)
    (r"^test_.*\.py$|^.*_test\.py$|^conftest\.py$", "Python (pytest)"),
    (r"^.*\.(test|spec)\.[cm]?[jt]sx?$", "JavaScript/TypeScript"),
    (r"^.*_test\.go$", "Go"),
    (r"^.*(Test|Tests|IT|Spec)\.(java|kt|kts|scala|groovy)$", "JVM"),
    (r"^.*(Test|Tests)\.(cs|fs|vb)$", ".NET"),
    (r"^.*(_spec|_test)\.rb$", "Ruby"),
    (r"^.*Test\.php$", "PHP (PHPUnit)"),
    (r"^test[-_].*\.[rR]$", "R (testthat)"),
    (r"^runtests\.jl$", "Julia"),
    (r"^.*(_test|_unittest)\.(c|cc|cpp|cxx)$|^test_.*\.(c|cc|cpp|cxx)$", "C/C++"),
    (r"^.*_test\.exs$", "Elixir"),
    (r"^.*Tests?\.swift$", "Swift"),
    (r"^.*\.bats$", "Bash (bats)"),
    (r"^test[-_].*\.m$|^.*Test\.m$", "MATLAB"),
]
# Names that suggest test code but match no rule: the agent asks about these.
UNSURE = re.compile(r"test|spec|fixture|mock|stub|fake|conftest|testdata|bench", re.I)

TEST_LIST = None  # set of paths: the `test:` files of <package>/tests.md
STEPS = []  # [(title, [paths])]: the steps of the tests review, from tests.md


def package_dir():
    """The review package: <repo>/pr-review, or <repo>/$PR_REVIEW_DIR. Run from the repo root."""
    return Path(os.environ.get("PR_REVIEW_DIR", "pr-review")).resolve()


def ensure_package():
    """Make the package folder, and ignore it in .git/info/exclude so it is never committed."""
    package = package_dir()
    package.mkdir(exist_ok=True)
    exclude = Path(git("rev-parse", "--git-path", "info/exclude")).resolve()
    exclude.parent.mkdir(parents=True, exist_ok=True)
    entries = exclude.read_text().splitlines() if exclude.exists() else []
    if f"/{package.name}/" not in entries:
        exclude.write_text("\n".join([*entries, f"/{package.name}/"]) + "\n")
    return package


def read_tests_md(path):
    """Read tests.md, if it exists: one `## ` heading per step of the tests review, then
    one bullet per file, `- code: `path`` or `- test: `path``. Sets STEPS, and TEST_LIST
    to every `test:` file: the files the code review leaves out."""
    global TEST_LIST
    if not path.exists():
        return
    TEST_LIST = set()
    for line in path.read_text().splitlines():
        heading = re.match(r"^##\s+(?:\d+[.)]\s*)?(.+?)\s*$", line)
        bullet = re.match(r"^\s*[-*]\s*(code|tests?)\s*:(.*)$", line, re.I)
        if heading:
            STEPS.append((heading[1], []))
        elif bullet:
            paths = re.findall(r"`([^`]+)`", bullet[2]) or [bullet[2].strip()]
            if bullet[1].lower().startswith("test"):
                TEST_LIST.update(paths)
            if STEPS:
                STEPS[-1][1].extend(p for p in paths if p not in STEPS[-1][1])


def guess_test(path):
    """(is a test, why, unsure) for a path, from the conventions above."""
    p = PurePosixPath(path)
    dirs = [d for d in p.parts[:-1] if d in TEST_DIRS]
    if dirs:
        return True, f"in a {dirs[0]}/ folder", False
    if "/src/test/" in f"/{path}":
        return True, "in src/test/ (JVM)", False
    for pattern, convention in TEST_NAMES:
        if re.match(pattern, p.name):
            return True, f"file name ({convention})", False
    if UNSURE.search(path):
        return False, "name suggests test code, no convention matched", True
    return False, "no test convention", False


def is_test(path):
    """A test file: a `test:` file of tests.md if the package has one, else by convention."""
    if TEST_LIST is not None:
        return path in TEST_LIST
    return guess_test(path)[0]


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
