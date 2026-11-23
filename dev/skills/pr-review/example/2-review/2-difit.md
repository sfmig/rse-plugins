# Review with difit

`difit` shows a GitHub-style diff in the browser, from local git. We provide a convenience script `review.sh` to use `difit` in the review of the atomic branch.


## Workflows

There are four possible workflows to
* Whole PR: `pr-review/scripts/review.sh all` opens the full diff (`d005d99` to the branch tip) in one tab, like GitHub's "Files changed".
* Commit by commit: `pr-review/scripts/review.sh atomic` opens one tab per atomic commit. Closing the tab opens the next commit, so you never run `difit` by hand.
* By session: `pr-review/scripts/review.sh sessions` opens one tab per session. The sessions come from the table in 2-difit.md, so you can regroup files by editing it.
* By test files: `pr-review/scripts/review.sh tests` works the same way, one test file per tab.

> [!TIP]
> * To resume from where you left off, add a number to the relevant command. E.g. `pr-review/scripts/review.sh atomic 5` will start from the 5th commit. 
> * In atomic mode, you can pass a commit hash instead, e.g. `pr-review/scripts/review.sh atomic 501a731`. Note that a short hash made of only digits may be read as a position - in that case please provide a longer hash.
> * You can check the number (or hash) of the item you last reviewed from the filenames in `pr-review/comments/`.
> * If you've committed to the PR branch since the atomic branch was built, `atomic` mode warns you. Run `pr-review/scripts/extend-atomic.sh` to add the new commits to the end (see [1-atomic-branch.md](1-atomic-branch.md#keep-it-up-to-date)).

## Managing tabs
* For each review item (i.e. a commit or a session), the `run_one` function in the `review.sh` script starts `difit` in the background. 
* While the `difit` process is alive, it does nothing else except save your comments to `comments/<item>.json` every 2 s.
* When you close the tab, `run_one` returns and the for-loop starts `difit` for the next item, which opens a new tab.
* To stop the whole run, do `CTRL+C` in the terminal that ran the `review.sh` script.

> [!NOTE]
> Closing a tab or reloading it have the same effect! It signals that review item is complete, the comments are saved and the next item opens in a new tab.


## Comments: where they are saved

| Where | When | Source |
|---|---|---|
| Browser localStorage | always, per diff | difit README "Persistent Storage" |
| difit server memory | while the tab is open | `difit comment get --port <port> --format json` |
| `pr-review/comments/<item>.json` | every 2 s, by `review.sh` | polls `/api/comments-json` |
| `pr-review/comments/<item>.log` | when the tab closes | difit prints all comments on exit |

- Without `review.sh`, comments live only in the browser.
- `comments/*.json` is what the AI agent reads later.
- Option B diffs come from stdin. They share one browser key, so `review.sh` starts each with `--clean`, then reloads that session's saved notes.
- Reloading the page ends the difit server; closing the tab is the signal to move on.

## In the tab

| Action | How |
|---|---|
| Mark file viewed | checkbox on the file header |
| Add a note | click a line number, or drag over a range |
| Reply to a preloaded question | reply in its thread |
| Show only changed lines (option A) | `DIFIT_EXTRA="--context 0" pr-review/scripts/review.sh atomic` |

## Session plan (option B)

Lines = added + removed (`git diff --numstat d005d99 smg/add-ellipse-params-to-tracks`). `review.sh` reads the files from this table; edit it to regroup.

| Session | Files | Lines | Done |
|---|---|---|---|
| 1 | `crabs/mask/README.md`, `crabs/mask/config/mask_config.yaml` | 79 | [ ] |
| 2 | `crabs/mask/mask_video.py` | 172 | [ ] |
| 3 | `crabs/mask/utils/float_encoding.py`, `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `crabs/utils/io.py` | 377 | [ ] |
| 4 | `crabs/mask/mask_props.py` | 351 | [ ] |
| 5 | `bash_scripts/run_mask_array.sh`, `guides/MaskTrackedCrabsHPC.md`, `pyproject.toml` | 51 | [ ] |

Before session 1: read block 1.

## Preloaded questions

Source: `pr-review/2-review/questions.json`. Commit = atomic commit that adds the line (`git blame` on the atomic branch).



* Preloaded questions: each question only appears on the commit that added its line, found with git blame.


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

## After the review

Next: `AI-specific red flags`. Then ask the agent: "read `pr-review/comments/*.json` and answer my notes".


## Keep it up to date

In the next step, `pr-review/scripts/review.sh atomic` warns when the atomic branch no longer matches the original branch.

To add new commits from the original branch to the tip of the atomic branch, run:
```bash
pr-review/scripts/extend-atomic.sh
```

- Adds each commit made on the original branch after the matching one to the end of the atomic branch, as items 17, 18, …. Same message, author and date.
- Finds the matching commit by itself: the commit on the original branch with the same files as the atomic tip.
- Doesn't touch your working tree. Earlier commits, their numbers and their saved comments stay as they are.
- New commits go at the end, out of the plumbing → docs order. After a big change, ask the agent for a full rebuild.
- If the original branch was rebased or amended, no commit has the same files as the atomic tip. It stops and asks for a rebuild.
