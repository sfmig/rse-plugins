---
name: pr-review
description: Build a review package for a pull request - aim and diagrams, an atomic copy of the branch, and two difit reviews (code, then tests) with preloaded questions - so a person can review it in order. Maps and indexes only; the reviewer judges the code. Use when the user asks for help reviewing a large PR or branch, a "review package", "review aid" or "PR review". Do not use for an ordinary code review where the user wants Claude's own findings in the conversation.
argument-hint: "[PR branch, number or URL]"
allowed-tools:
  - Bash(${CLAUDE_SKILL_DIR}/scripts/init_package.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/check_package.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/facts.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/build_atomic.py *)
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/proposal/scripts/check-mermaid.sh *)
---

# PR review package

The PR to review: $ARGUMENTS

If that is empty, use the checked-out branch. If that is the main branch, ask the user which branch or PR to review.

Build **maps and indexes** of the PR, not judgments. The reviewer reads the code and decides. This skill only puts the PR in an order they can follow, and points at what deserves a second look.

The output is a folder in the reviewed repo, by default `pr-review/`. [`example/`](example/README.md) holds the pages of a package for a real PR: **use it as the model for every page**, for content, level of detail and format. [DECISIONS.md](DECISIONS.md) records why each choice was made; read it when a rule here seems arbitrary.

## Ground rules

- **Never change the PR.** Do not commit to, rebase, push or check out another branch. The working tree stays as it is. The only branch you create is the local atomic copy (step 2), and you never push it.
- **Verify every `file:line` before writing it** with `sed -n` or `grep -n`. Estimated line numbers are often off by a few lines.
- **Write "UNSURE" when you have not checked something.** Do not guess.
- **No quality words** ("robust", "clean", "elegant"). Say what the code does.
- Read `${CLAUDE_PLUGIN_ROOT}/skills/writing-style/SKILL.md` and follow it. Prefer tables, short bullets, diagrams and code blocks to paragraphs.

## Process

### 1. Collect the facts

Work out the branches from git; do not ask for what git can tell you.

```bash
${CLAUDE_SKILL_DIR}/scripts/facts.py [branch]    # default: the checked-out branch
```

It prints the base (merge base with origin's default branch), the commits, each changed file with its lines and whether it is a test, and the functions and constants the PR adds, removes or changes (signature, value, or body only). Use the functions table for the boxes to mark as new or changed in the diagrams, and to group the atomic commits.

For a PR number or URL, check it out only if the user agrees (`gh pr checkout N`). A test file is one in a `tests/` folder, or named `test_*.py`, `*_test.py`, `conftest.py`: `facts.py` and the review scripts share this rule (`is_test` in `scripts/package/atomic.py`).

### 2. Build the atomic branch

A local branch `<branch>-atomic`, with the same final files as the PR branch, rebuilt as a short series of commits that each do one thing. Order: plumbing (dependencies, helpers) → core → wiring → tests → docs. Tests come after the code, in their own commits, so the code review can skip them.

You decide the grouping; `build_atomic.py` makes the commits. Write a plan in your scratchpad, one entry per commit, oldest first:

```json
[{"message": "Add scikit-image dependency", "files": ["pyproject.toml"]},
 {"message": "Labels: 8-frame chunks",
  "files": [{"path": "crabs/mask/mask_video.py", "from": "stages/05/mask_video.py"}]}]
```

- A plain path takes the file as it is at the PR tip (deleted, if the tip deletes it). List both paths of a renamed file.
- For a file whose changes are split over commits, give its content at that commit with `from` (relative to the plan). Write each stage from the previous one with exact string replacements.

```bash
${CLAUDE_SKILL_DIR}/scripts/build_atomic.py <scratchpad>/plan.json [--force]
```

It commits with a temporary index (the working tree is never touched), and creates `<branch>-atomic` only if the last commit has the same files as the PR tip. Otherwise it lists the files that differ: fix the plan and run it again. `--force` replaces an existing atomic branch and prints the old tip. Never push it.

If the PR branch gains commits later, the package's `scripts/atomic.py extend` appends them to the atomic branch. A rebased PR branch needs a rebuild.

### 3. Start the package

```bash
${CLAUDE_SKILL_DIR}/scripts/init_package.py [folder]     # default: pr-review
```

It copies the fixed files: the Quarto page from `template/`, the difit scripts from `scripts/package/`, and `2-review/2-code.md` with an empty session table. It also pins `code-base-url` to the branch tip on GitHub, and adds the folder to `.git/info/exclude`. It stops if the folder exists: then ask the user whether to replace it or use another name.

### 4. Write the pages

Four pages, one tab each. Write each one after its counterpart in `example/`, replacing every PR-specific part. The example's commands use the default folder, `pr-review/`; use the package's own folder name if it differs.

| Tab | File | Write |
|---|---|---|
| Aim and diagrams | `1-general/1-aim.md` | **Aim** (open): two bold-led paragraphs, "**Before this PR**" (what the code held and how it behaved) and "**With this PR**" (what is added, what it aligns with, what changes). Plain words; name real variables and files. Then, collapsed: **Components before and after** (two `flowchart LR`, each box a real file or function, green = new or changed) and **Flow diagram** of the main path (legend subgraph, `mv:538 to mv:55` call-site-to-definition labels, `click` links to the pinned GitHub URL, and a collapsed table of the same links) |
| Atomic branch | `2-review/1-atomic-branch.md` | Why the original branch is not atomic (table of signs, with commits); the scratch branch and the zero-diff check; the **commits table**; extending; limits (only the final tree is checked; middle commits not run) |
| Review code with difit | `2-review/2-code.md` | Written by `init_package.py`. Fill in the **session plan table** only: one row per sitting of about 50–400 changed lines, related files together, no test files |
| Review tests with difit | `2-review/3-tests.md` | The **test steps table**: one step per module under test, with its source files and test files (and shared fixtures); then, collapsed: passes, tests questions, not tested (by grep of `tests/`), bug-fix commits with or without a test that fails before the fix |

Tables that `review.py` reads must keep the example's columns exactly:

| Table | Row format |
|---|---|
| Commits (`1-atomic-branch.md`) | `` \| 5 \| `501a731` \| purpose \| files \| +49/-19 \| 🔴 high \| `` — weight last: `🔴 high`, `🟠 med` or `🟢 low` (how much a reviewer must think, not the line count) |
| Sessions (`2-code.md`) | `` \| 1 \| `path`, `path` \| 79 \| [ ] \| `` |
| Test steps (`3-tests.md`) | `` \| 1 \| behaviour \| `src.py`, `tests/test_src.py` \| [ ] \| `` |

Page format:

- **Exactly one `# ` heading per page, on its first line.** It becomes the tab's name. Nothing above it.
- **The first `##` section stays open; each later section is a `<details>` with `<summary><b>Title</b></summary>`.** No list of section links at the top, no "back to top" links.
- **Refer to another section by its name in italics** (*Session plan table* below). A link cannot open a closed `<details>`, and a tab's heading is not a link target.
- **Mermaid as plain ` ```mermaid ` fences**, not ` ```{mermaid} `. No `;` in labels (it ends a statement); avoid `{}`, `%` and `#`. Prefer plain boxes to diamonds in tall diagrams.
- **Code links relative to the page** (`../../crabs/x.py#L10` from a block folder). The Quarto page turns them into GitHub links at `code-base-url`.

### 5. Preloaded questions

Skeptical questions a reviewer should settle, shown as open difit threads. Two files, one per review:

- `2-review/questions-code.json`: about code. Never on a test file (the code review does not show test files).
- `2-review/questions-tests.json`: about the tests, or about code that no test reaches.

```json
[{"type": "thread", "filePath": "crabs/utils/io.py", "position": {"side": "new", "line": 17},
  "body": "Q4: 300 s per read timeout: worst-case hang per job acceptable?"}]
```

- Up to about 10 per file, each one line, numbered `Q1…` (code) or `T1…` (tests), "UNSURE" where unchecked.
- **Anchor each one to a line the PR adds**, on the new side, at the branch tip. difit may not show a comment on another line.
- Ask about behaviour a reader cannot see in the diff: concurrency, reruns, partial failure, untested paths, assumptions about inputs. Not style.
- List the same questions in a table on the page (*Tests questions* in `3-tests.md`); the code questions table is optional.

### 6. Check

```bash
${CLAUDE_SKILL_DIR}/scripts/check_package.py [folder]
${CLAUDE_PLUGIN_ROOT}/skills/proposal/scripts/check-mermaid.sh <folder>/1-general/1-aim.md
```

`check_package.py` checks the headings, every `` `path:N` `` anchor against the pinned commit, that every question is on an added line, and that `review.py` can read the three tables (and every changed test file is in a test step). Fix every `FAIL`. If `check-mermaid.sh` exits with status 2 (no renderer), say so and carry on.

Optionally render the page: `cd <folder> && quarto render`. It needs the sandbox off (it writes `~/Library/Caches/quarto`).

### 7. Present it

Give the user the folder and the two ways to read it:

- in the browser, one tab per page: `cd <folder> && quarto preview`;
- as plain Markdown, in the editor or on GitHub.

Then the reviews, which the user runs (each opens a browser page and saves comments as they go):

```bash
npm i -g difit@5.0.12                 # once
<folder>/scripts/review.py all        # or atomic, or sessions: the code review
<folder>/scripts/review.py tests      # the tests review
```

Do not run `review.py` yourself, and do not judge the PR in the chat unless asked.

## After a review pass

The reviewer's comments are in `<folder>/comments/code/pass-N/comments.json` and `<folder>/comments/tests/pass-N/comments.json`. When asked to answer them:

- Ask the user to stop the review first: `review.py` saves every second and would overwrite your edits.
- Answer each open thread in `threads` by appending a message to its `messages`: `{"id": "reply-<thread id>-<n>", "author": "Claude", "body": "…", "createdAt": "<ISO time>", "updatedAt": "<ISO time>"}` (difit writes the reviewer's replies with `"author": "User"`). Conclusion first, then the reason, with `file:line`.
- For a suggested change, say whether to accept it and why. Change no code until the user resolves the thread and asks.
- Leave `resolved` and `deleted` as they are.

The user reloads the pass with `review.py <mode> --pass N` to read the replies. When asked to implement resolved threads, do it on the PR branch with atomic commits, after confirming the branch with the user.
