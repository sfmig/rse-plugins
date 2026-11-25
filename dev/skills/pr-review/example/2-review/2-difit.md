# Review with difit

[`difit`](https://yoshiko-pg.github.io/difit/) shows a GitHub-style diff in the browser, from local git. 

First, **install** `difit` (once only) with: 

```bash
npm i -g difit@5.0.12
``` 

Then, run the **helper script**:

```bash
pr-review/scripts/review.py
```

## Workflows

We support three possible workflows to review the files:

* **Whole PR**: 
    * `pr-review/scripts/review.py all` 
    * Shows the full diff between the PR branch and the commit where it split off from `main`, like GitHub's "Files changed".
* **Commit by commit**: 
    * `pr-review/scripts/review.py atomic` 
    * Shows one atomic commit at a time.
* **By session**: 
    * `pr-review/scripts/review.py sessions` 
    * Shows one session at a time. The sessions come from the table in [Session plan](#session-plan-table), so you can regroup files by editing the table directly.

To res**ume from a given item, add its number (or a commit hash in atomic mode):

* E.g. `pr-review/scripts/review.py sessions 5` starts at the 5th row of the session table.
* E.g. `pr-review/scripts/review.py atomic 501a731` starts at commit 501a731.
    * A short hash made of only digits may be read as a position - in that case please provide a longer hash.



## Review page

`review.py` opens one review page in the browser:

* The bar above the diff has **Prev** / **Next** buttons (or <kbd>Alt</kbd>+<kbd>↑</kbd> / <kbd>Alt</kbd>+<kbd>↓</kbd>). 
    * In commit-by-commit mode it also shows the commit's subject line (hover it for the full message).
* To stop the review, use the page's **Stop review** button or `CTRL+C` in the terminal.
    * The comments are saved first.

## Comments

`review.py` saves the comments once a second. As on GitHub, comments only move forward, to newer code:

* A comment written on an atomic commit stays on that commit. It also shows in whole-PR and session modes, at its line at the tip of the branch.
* If a later commit changed the line, the comment is **outdated**.
* **Resolving** a thread in `difit` moves it to the `resolved` list. Resolved threads are not loaded again.
    * "Delete all comments" in `difit`'s menu counts as resolving every thread. 
* To **delete** a thread, reply `delete` or edit its first message to `delete`. The thread stays visible until you open another item. To undo, you can delete the `delete` reply.
* The **"viewed" checkboxes are not kept** after reopening.
* Stop the review before editing `comments.json` by hand (or before asking an agent to). Otherwise the an automatic save can overwrite your edits.


## Review passes

* Each run starts a new review **pass**. Its comments are saved to `pr-review/comments/pass-N/comments.json`. 
* To add comments to an earlier pass, use `--pass N`
    * e.g. `pr-review/scripts/review.py atomic 7 --pass 2`.
* The AI-suggested questions ([Preloaded questions](#preloaded-questions)) are added to each new pass, except the ones an earlier pass resolved or deleted.

## After the review

When done with your comments, you can ask the agent to read the JSON file and address the comments and/or questions with replies. Example prompt:

> Have a look at the comments from the PR review here. Answer the questions briefly, clarify ambiguous things and for suggested changes determine whether to accept them or not. Can you add your comments to the json as replies to a thread?

Then you can review the answers by reloading `difit` for that pass. You can settle any open threads and resolve. Once you are happy, you can ask the agent to implement the suggestions. Example prompt:

> Have a look at the comments in /pr-review/comments/pass-N/comments.json and implement anything that is resolved in `<original-branch>` with atomic commits

You can optionally review the section on AI-specific red flags before finalising the review. 

You can optionally delete the atomic branch when done too:  

```bash
git branch -D smg/add-ellipse-params-to-tracks-atomic
```


## When the atomic branch is behind

If commits were added to the PR branch after the atomic branch was built, `review.py` will say so. Until the atomic branch is updated, comments written on a commit are not shown at the tip, and the preloaded questions are not placed on commits. 

## Session plan table

When reviewing **by session**, `review.py` reads the files from this table. You can edit it to regroup the files.

| Session | Files | Lines | Done |
|---|---|---|---|
| 1 | `crabs/mask/README.md`, `crabs/mask/config/mask_config.yaml` | 79 | [ ] |
| 2 | `crabs/mask/mask_video.py` | 172 | [ ] |
| 3 | `crabs/mask/utils/float_encoding.py`, `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `crabs/utils/io.py` | 377 | [ ] |
| 4 | `crabs/mask/mask_props.py` | 351 | [ ] |
| 5 | `bash_scripts/run_mask_array.sh`, `guides/MaskTrackedCrabsHPC.md`, `pyproject.toml` | 51 | [ ] |


## Preloaded questions

Below are some AI-suggested questions. Each question only appears on the commit that added its line (found with git blame).

| # | Question | Where | Commit | Session |
|---|---|---|---|---|
| 1 | Array jobs share one store; concurrent `consolidate_metadata` calls safe? | `crabs/mask/mask_video.py:684` | 11 | 2 |
| 2 | Rerun with `--zarr_mode_group a`: does box append fail on existing `position`? UNSURE | `crabs/mask/utils/bbox_prompts.py:203` | 9 | 3 |
| 3 | Region writes use `confidence` time chunk; `position` chunk may differ? | `crabs/mask/mask_props.py:317` | 10 | 4 |
| 4 | Both length checks trust header `total_frames`; is it exact? | `crabs/mask/mask_video.py:389` | 6 | 2 |
| 5 | `mask_config` attr hard-codes 5 keys; new yaml key silently unrecorded? | `crabs/mask/mask_video.py:633` | 7 | 2 |
| 6 | Crash after `del group[var]` leaves NaN-filled vars; detectable later? | `crabs/mask/mask_props.py:262` | 10 | 4 |
| 7 | Test imports `scripts.` without `scripts/__init__.py`; collected in CI? UNSURE | `tests/test_unit/test_mask_props.py:25` | 14 | tests |
| 8 | Guide output tree omits boxes and 8 new variables? | `guides/MaskTrackedCrabsHPC.md:134` | 16 | 5 |
| 9 | 300 s per read timeout: worst-case hang per job acceptable? | `crabs/utils/io.py:16` | 2 | 3 |
| 10 | Labels chunk straddling two time slices decoded twice? | `crabs/mask/mask_props.py:153` | 10 | 4 |

