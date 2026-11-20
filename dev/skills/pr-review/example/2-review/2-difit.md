# Review with difit

difit shows a GitHub-style diff in the browser, from local git. Checked version: `5.0.12`.

`pr-review/review.sh` opens one item per tab. Close the tab: the next item opens. Ctrl+C stops.

## Pick one option

| Option | Command | One tab = | Best for |
|---|---|---|---|
| A. Atomic branch | `pr-review/review.sh atomic` | one commit of `Atomic branch` | following the build order |
| B. Session plan | `pr-review/review.sh sessions` | one session of the table below | short sittings, files grouped by topic |

Resume at item N: `pr-review/review.sh atomic 5`. Tests are block 3.

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
| Show only changed lines (option A) | `DIFIT_EXTRA="--context 0" pr-review/review.sh atomic` |

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
