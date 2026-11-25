# Review code with difit

The review is in two parts, each with its own comments:

1. **Code review** (this tab): the PR without its test files.
2. **Tests review** (tab *Review tests with difit*): the test files, next to the code they test.


[`difit`](https://yoshiko-pg.github.io/difit/) shows a GitHub-style diff in the browser, from local git. **Install** it once:

```bash
npm i -g difit@5.0.12
```

## Workflows
[↑ Back to top](#top)

Three ways to go through the code. None of them shows the test files: a file in a `tests/` folder, or named `test_*.py`, `*_test.py` or `conftest.py`.

| Workflow | Command | Shows |
|---|---|---|
| Whole PR | `pr-review-minimal/scripts/review.py all` | The PR's diff from where it split off `main`, like GitHub's "Files changed" |
| Commit by commit | `pr-review-minimal/scripts/review.py atomic` | One atomic commit at a time. Commits with only tests are skipped |
| By session | `pr-review-minimal/scripts/review.py sessions` | One row of the [Session plan table](#session-plan-table) at a time |

To **resume** from an item, add its number from the tables, or a commit hash in atomic mode:

* `pr-review-minimal/scripts/review.py sessions 3` starts at session 3.
* `pr-review-minimal/scripts/review.py atomic 501a731` starts at that commit. A short hash of only digits is read as a number: give a longer hash.

## Review page
[↑ Back to top](#top)

`review.py` opens one page in the browser:

* **Prev** / **Next** buttons above the diff (or <kbd>Alt</kbd>+<kbd>↑</kbd> / <kbd>Alt</kbd>+<kbd>↓</kbd>). In commit mode the bar also shows the commit's subject (hover for the full message).
* **✎ Open in editor** in the sidebar lists the files of the item on screen. Click one to open it in your editor.
* **Stop review** button, or <kbd>Ctrl</kbd>+<kbd>C</kbd> in the terminal, to stop.

## Comments
[↑ Back to top](#top)

`review.py` saves the comments once a second. As on GitHub, comments only move forward, to newer code:

* A comment written on an atomic commit stays on that commit. It also shows in whole-PR and session modes, at its line at the tip of the branch.
* If a later commit changed the line, the comment is **outdated**: listed in the sidebar, not shown inline.
* **Resolving** a thread in `difit` moves it to the `resolved` list. Resolved threads are not loaded again. "Delete all comments" in `difit`'s menu counts as resolving every thread.
* To **delete** a thread, reply `delete`. The thread stays visible until you open another item. To undo, delete the `delete` reply.
* The "viewed" checkboxes are not kept.
* Stop the review before editing `comments.json` by hand (or before asking an agent to). Otherwise an automatic save can overwrite your edits.

## Review passes
[↑ Back to top](#top)

* Each run starts a new **pass** of the code review, saved to `pr-review-minimal/comments/code/pass-N/comments.json`.
* To add comments to an earlier pass, use `--pass N`, e.g. `pr-review-minimal/scripts/review.py atomic 7 --pass 2`.
* The [Preloaded questions](#preloaded-questions) are added to each new pass, except the ones an earlier pass resolved or deleted.
* The tests review has its own passes, in `comments/tests/`.

## After the review
[↑ Back to top](#top)

Ask the agent to answer the open threads in the JSON file. Example prompt:

> Have a look at the comments in pr-review-minimal/comments/code/pass-N/comments.json. Answer the questions briefly, clarify ambiguous things, and for suggested changes say whether to accept them. Add your answers to the JSON as replies to each thread.

Reload the pass in `difit` (`--pass N`) to read the answers, settle open threads and resolve. Then ask the agent to implement what you agreed:

> Implement the resolved suggestions in pr-review-minimal/comments/code/pass-N/comments.json on `<original-branch>`, with atomic commits.

If commits are added to the PR branch after the atomic branch was built, `review.py` says so. Until the atomic branch is extended (tab *Atomic branch*), comments written on a commit are not shown at the tip, and the preloaded questions are not placed on commits.

## Session plan table
[↑ Back to top](#top)

When reviewing **by session**, `review.py` reads the files from this table. Edit it to regroup the files. Test files in it are ignored.

| Session | Files | Lines | Done |
|---|---|---|---|
| 1 | `crabs/mask/README.md`, `crabs/mask/config/mask_config.yaml` | 79 | [ ] |
| 2 | `crabs/mask/mask_video.py` | 172 | [ ] |
| 3 | `crabs/mask/utils/float_encoding.py`, `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `crabs/utils/io.py` | 377 | [ ] |
| 4 | `crabs/mask/mask_props.py` | 351 | [ ] |
| 5 | `bash_scripts/run_mask_array.sh`, `guides/MaskTrackedCrabsHPC.md`, `pyproject.toml` | 51 | [ ] |

