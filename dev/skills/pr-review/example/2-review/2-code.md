# Review code with difit

The review is split in two parts:

1. **Code review** (this tab): the PR without the test files.
2. **Tests review** (tab *Review tests with difit*): the test files, next to the code they test.


## Quickstart 

[`difit`](https://yoshiko-pg.github.io/difit/) shows a GitHub-style diff in the browser, from local git. **Install** it once:

```bash
npm i -g difit@5.0.12
```

Then, run the **helper script**:

```bash
pr-review/scripts/review.py [all | atomic | sessions]
```

## Workflows

Three ways to go through the code. 



|  | CLI argument | Shows |
|---|---|---|
| **Whole PR** | `all` | The PR's diff from where it split off `main`, like GitHub's "Files changed" |
| **Commit by commit** | `atomic` | One atomic commit at a time. Commits with only tests are skipped |
| **By session** | `sessions` | One row of the *Session plan table* below at a time |

By default none of them shows the test files, that is:
* a file in a `tests/` folder, 
* or named `test_*.py`, `*_test.py` or `conftest.py`.

To **include the test files**, add `--with-tests`, e.g. `pr-review/scripts/review.py all --with-tests`. Comments written on them stay in the code review. In session mode, only test files listed in the *Session plan table* are shown.

To **leave out the AI-suggested questions**, add `--no-questions`, e.g. `pr-review/scripts/review.py atomic --no-questions`. By default they are added to each new pass as open threads (from `2-review/questions-code.json`). Questions already in a pass you reopen with `--pass N` stay.


<details>
<summary><b>Review page</b></summary>

`review.py` opens one page in the browser:

* **Prev** / **Next** buttons above the diff (or <kbd>Alt</kbd>+<kbd>↑</kbd> / <kbd>Alt</kbd>+<kbd>↓</kbd>). In commit mode the bar also shows the commit's subject (hover for the full message).
* **✎ Open in editor** in the sidebar lists the files of the item on screen. Click one to open it in your editor.
* **Stop review** button, or <kbd>Ctrl</kbd>+<kbd>C</kbd> in the terminal, to stop.

</details>

<details>
<summary><b>Comments</b></summary>

`review.py` saves the comments once a second. As on GitHub, comments only move forward, to newer code:

* A comment written on an atomic commit stays on that commit. It also shows in whole-PR and session modes, at its line at the tip of the branch.
* If a later commit changed the line, the comment is **outdated**: listed in the sidebar, not shown inline.
* **Resolving** a thread in `difit` moves it to the `resolved` list. Resolved threads are not loaded again. "Delete all comments" in `difit`'s menu counts as resolving every thread.
* To **delete** a thread, reply `delete`. The thread stays visible until you open another item. To undo, delete the `delete` reply.
* The "viewed" checkboxes are not kept.
* Stop the review before editing `comments.json` by hand (or before asking an agent to). Otherwise an automatic save can overwrite your edits.

</details>

<details>
<summary><b>Review passes</b></summary>

* Each run starts a new **pass** of the code review, saved to `pr-review/comments/code/pass-N/comments.json`.
* To add comments to an earlier pass, use `--pass N`, e.g. `pr-review/scripts/review.py atomic --pass 2`.
* The preloaded questions (`2-review/questions-code.json`) are added to each new pass, except the ones an earlier pass resolved or deleted. To leave them out, add `--no-questions`. Questions already in a pass you reopen with `--pass N` stay.
* The tests review has its own passes, in `comments/tests/`.
* To go on where you stopped, click the item in the sidebar: items already opened in the pass are greyed out.

</details>

<details>
<summary><b>After the review</b></summary>

Ask the agent to answer the open threads in the JSON file. Example prompt:

> Have a look at the comments in pr-review/comments/code/pass-N/comments.json. Answer the questions briefly, clarify ambiguous things, and for suggested changes say whether to accept them. Add your answers to the JSON as replies to each thread.

Reload the pass in `difit` (`--pass N`) to read the answers, settle open threads and resolve. Then ask the agent to implement what you agreed:

> Implement the resolved suggestions in pr-review/comments/code/pass-N/comments.json on `<original-branch>`, with atomic commits.

If commits are added to the PR branch after the atomic branch was built, `review.py` says so. Until the atomic branch is extended (tab *Atomic branch*), comments written on a commit are not shown at the tip, and the preloaded questions are not placed on commits.

</details>

<details open>
<summary><b>Session plan table</b></summary>

When reviewing **by session**, `review.py` reads the files from this table. Edit it to regroup the files. Test files in it are shown only with `--with-tests`.

| Session | Files | Lines | Done |
|---|---|---|---|
| 1 | `crabs/mask/README.md`, `crabs/mask/config/mask_config.yaml` | 79 | [ ] |
| 2 | `crabs/mask/mask_video.py` | 172 | [ ] |
| 3 | `crabs/mask/utils/float_encoding.py`, `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `crabs/utils/io.py` | 377 | [ ] |
| 4 | `crabs/mask/mask_props.py` | 351 | [ ] |
| 5 | `bash_scripts/run_mask_array.sh`, `guides/MaskTrackedCrabsHPC.md`, `pyproject.toml` | 51 | [ ] |

</details>
