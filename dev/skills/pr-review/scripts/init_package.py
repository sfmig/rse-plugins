#!/usr/bin/env python3
"""Start a PR review package in the reviewed repo, from the minimal example.

    init_package.py [FOLDER]    (default: pr-review, at the repo root)

Run from inside the reviewed repo, with the PR branch checked out. It copies the
files that are the same for every PR (the Quarto page and the difit scripts) from
example/, and 2-review/2-code.md with its session table emptied. The pages
that describe the PR are left for the agent to write.

It also:
  * points code-base-url in _quarto.yml at the branch tip on GitHub, if origin is there;
  * adds FOLDER to .git/info/exclude, so the package is never committed by mistake.

It stops if FOLDER exists. It changes no branch and no tracked file.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent / "example"
EXAMPLE_NAME = "pr-review-minimal"  # the folder name the example's pages use
FIXED = [
    "_quarto.yml", "index.qmd", "styles.css", "tab-sections.lua", "gh-alerts.lua",
    "mermaid.lua", "mermaid.html", ".gitignore",
    "scripts/review.py", "scripts/atomic.py", "scripts/comments.py",
    "scripts/links.py", "scripts/page.html",
]
SESSION_ROW = re.compile(r"^\|.*\| *\[[ x]\] *\|$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def github_blob_url(sha):
    """https://github.com/<owner>/<repo>/blob/<sha>/ if origin is on GitHub, else None."""
    try:
        url = git("remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        return None
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/(.+?)(?:\.git)?$", url)
    return f"https://github.com/{m[1]}/{m[2]}/blob/{sha}/" if m else None


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "pr-review"
    if len(sys.argv) > 2 or name.startswith("-"):
        sys.exit(__doc__)
    root = Path(git("rev-parse", "--show-toplevel"))
    target = root / name
    if target.exists():
        sys.exit(f"{target} exists: choose another folder, or remove it first.")

    for rel in FIXED:
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(EXAMPLE / rel, target / rel)
    (target / "1-general").mkdir()
    (target / "2-review").mkdir()

    # 2-code.md: the example's text, with this package's folder and no session rows
    text = (EXAMPLE / "2-review" / "2-code.md").read_text().replace(f"{EXAMPLE_NAME}/", f"{name}/")
    lines = [l for l in text.splitlines() if not SESSION_ROW.match(l)]
    (target / "2-review" / "2-code.md").write_text("\n".join(lines) + "\n")

    tip = git("rev-parse", "HEAD")
    url = github_blob_url(tip)
    quarto = target / "_quarto.yml"
    quarto.write_text(re.sub(r"^code-base-url: .*$",
                             f"code-base-url: {url or 'TODO: URL of the code at ' + tip}",
                             quarto.read_text(), flags=re.M))

    exclude = Path(git("rev-parse", "--git-path", "info/exclude"))
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    entries = exclude.read_text().splitlines() if exclude.exists() else []
    if f"/{name}/" not in entries:
        exclude.write_text("\n".join([*entries, f"/{name}/"]) + "\n")

    print(f"Created {target.relative_to(root)}/ at {tip[:7]}.")
    print(f"code-base-url: {url or 'not on GitHub: set it in _quarto.yml'}")
    print(f"Ignored locally in {exclude}.")
    print("To write: 1-general/1-aim.md, 2-review/1-atomic-branch.md, 2-review/3-tests.md,")
    print("          the session table in 2-review/2-code.md, 2-review/questions-*.json")


if __name__ == "__main__":
    main()
