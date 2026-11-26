---
name: pr-review-lite
description: Review a large PR in difit, one atomic commit at a time - Claude rebuilds the branch as a local atomic copy, splits code from tests, preloads skeptical questions, and launches the review; comments are saved per pass. Use when the user asks for a "lite" or quick PR review in difit, an atomic review of a branch, or invokes it by name. Do not use for an ordinary code review where the user wants Claude's own findings in the conversation.
argument-hint: "[branch | PR] [atomic | all | tests | extend | answer] [--pass N] [--with-tests] [--no-questions]"
allowed-tools:
  - Bash(${CLAUDE_SKILL_DIR}/scripts/facts.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/build_atomic.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/review.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/atomic.py extend)
---

# PR review, lite

Arguments: $ARGUMENTS

- A branch, PR number or URL: the PR to review. None: the checked-out branch. If that is the main branch, ask which one.
- A mode: `atomic` (default), `all` or `tests`. Pass it, and `--pass N`, `--with-tests`, `--no-questions`, to `review.py` as given.
- `extend`: run `${CLAUDE_SKILL_DIR}/scripts/atomic.py extend`, report what it added, stop.
- `answer`: answer the last pass's comments (*After a pass*), stop.

You map the PR and launch the review. The user judges the code: do not review the PR in the chat unless asked.

## Ground rules

- **Never change the PR branch.** No commit, rebase, push or checkout. The only branch you write is the local `<branch>-atomic`, through the scripts. Never push it.
- For a PR number or URL, check it out only if the user agrees (`gh pr checkout N`).
- Run every script from the repo root. They run with uv; if one fails with `uv: No such file or directory`, ask the user to install it: <https://docs.astral.sh/uv/getting-started/installation/>.
- The package folder is `pr-review/` at the repo root, ignored in `.git/info/exclude`. It holds only data: `tests.md`, `questions-*.json`, `overview.md`, `comments/`.

## Fast path

If `<branch>-atomic` exists and `pr-review/tests.md` exists, go to step 6:

- `facts.py` says whether the atomic branch exists.
- If `review.py` says the atomic branch is behind, run `atomic.py extend` first.
- A rebased PR branch needs the atomic branch rebuilt (step 3 with `--force`): ask first, since this orphans the comments on commits.

## Steps

### 1. Facts

```bash
${CLAUDE_SKILL_DIR}/scripts/facts.py [branch]
```

It prints the base, the commits, and each changed file with a test/code guess and why.

### 2. Which files are tests

The guess follows common conventions: test folders (`tests/`, `__tests__/`, `spec/`, `src/test/`, …) and file names (`test_*.py`, `*.test.ts`, `*_test.go`, `*Test.java`, `*_spec.rb`, `test-*.R`, …). Check it against the repo's own layout (test config such as `pyproject.toml`, `jest.config.*` or `Cargo.toml`, and where the existing tests live).

- Ask the user (AskUserQuestion, one multi-select question) about every file marked **unsure**, and any guess you doubt: fixtures, test data, mocks, test helpers outside a test folder, benchmarks.
- A file that mixes code and tests (Rust `#[cfg(test)]`, doctests) counts as code. Say so to the user.
- Do not ask when nothing is in doubt.

The final answer goes in `pr-review/tests.md` (step 4). Every script uses it from then on.

### 3. Atomic branch

Regroup the PR as a short series of commits that each do one thing: plumbing (dependencies, helpers), then core, then wiring, then tests, then docs. Tests go in their own commits, after the code they test, so the code review skips them.

Write a plan to your scratchpad, oldest commit first:

```json
[{"message": "Add scikit-image dependency", "weight": "low", "files": ["pyproject.toml"]},
 {"message": "Labels: 8-frame chunks", "weight": "high",
  "files": [{"path": "crabs/mask/mask_video.py", "from": "stages/05/mask_video.py"}]}]
```

- A plain path takes the file as at the PR tip (deleted if the tip deletes it). List both paths of a renamed file.
- For a file whose changes are split over commits, write each stage from the previous one with exact string replacements, and give it with `from` (relative to the plan).
- `weight`: `high`, `med` or `low`. It says how much a reviewer must think, not the line count.

```bash
${CLAUDE_SKILL_DIR}/scripts/build_atomic.py <scratchpad>/plan.json [--force]
```

It creates `<branch>-atomic` only if the last commit has the same files as the PR tip. Otherwise it lists the differing files: fix the plan and rerun it.

### 4. Tests file and questions

`pr-review/tests.md` sets both which files are tests and the steps of the tests review. Write one `## ` step per module under test, with one bullet per file:

- `code:` for a source file;
- `test:` for a test file or a shared fixture.

```markdown
# Tests

## 1. Float encoding: time last, lossless

- code: `crabs/mask/utils/float_encoding.py`
- test: `tests/test_unit/test_float_encoding.py`

## 2. Boxes from a trajectories clip

- code: `crabs/mask/utils/bbox_prompts.py`
- test: `tests/test_unit/test_bbox_prompts.py`
- test: `tests/fixtures/trajectories.py`
```

- **The `test:` files are the test files:** the code review leaves them out.
- **Put every changed test file in a step.** A file that is in no step counts as code.
- **Repeat a shared fixture in each step that uses it.**

Preloaded questions are things a reviewer should settle, shown as open difit threads. Write `pr-review/questions-code.json` (never on a test file) and `pr-review/questions-tests.json` (about tests, or code no test reaches):

```json
[{"type": "thread", "filePath": "crabs/utils/io.py", "position": {"side": "new", "line": 17},
  "body": "Q4: 300 s per read timeout: worst-case hang per job acceptable?"}]
```

- Up to about 10 questions per file, one line each, numbered `Q1…` or `T1…`.
- Anchor each to a line the PR adds, new side, at the tip. Check the line with `sed -n`: `review.py` warns about questions on other lines.
- Ask about what the diff does not show: concurrency, reruns, partial failure, untested paths, assumptions about inputs. Not style. Write "UNSURE" where you have not checked.

### 5. Overview (short)

`pr-review/overview.md` holds:

- a `# ` title;
- **Before this PR** and **With this PR**, a short paragraph each, naming real files and functions;
- one ` ```mermaid ` `flowchart LR` of the main path, with the new or changed boxes in green. No `;` in labels.

It renders in VS Code's Markdown preview and on GitHub. Nothing else to write.

### 6. Launch the review

Check that `difit` is on the PATH. If it is not, ask the user to run `npm i -g difit@5.0.12` and stop.

Run the review **in the background** (`run_in_background: true`), with the mode from the arguments (default `atomic`):

```bash
${CLAUDE_SKILL_DIR}/scripts/review.py [atomic | all | tests] [--pass N] [--with-tests] [--no-questions]
```

It opens the review page in the browser and saves comments every second. If it fails to bind a port or start difit inside the sandbox, rerun it with the sandbox off. Read its first lines of output, then give the user:

- the review page URL, and the pass's comments file;
- any `Note:` lines it printed;
- what comes next: stop with the page's Stop button, then `/pr-review-lite tests` for the tests review, or `/pr-review-lite answer` to get replies.

When the background run exits, say so in one line and offer to answer the comments.

## After a pass

The comments are in `pr-review/comments/<code|tests>/pass-N/comments.json`, the highest N being the last pass. To answer them:

- Make sure no `review.py` is running: it saves every second and would overwrite your edits.
- For each open thread in `threads`, append to its `messages`: `{"id": "reply-<thread id>-<n>", "author": "Claude", "body": "…", "createdAt": "<ISO time>", "updatedAt": "<ISO time>"}`. Conclusion first, then the reason, with `file:line`.
- For a suggested change, say whether to accept it and why. Leave `resolved` and `deleted` as they are. Change no code.

Then relaunch that pass in the background so the user can read the replies: `review.py <mode> --pass N`. When the user asks you to implement resolved threads, confirm the branch first, then commit atomically on the PR branch.
