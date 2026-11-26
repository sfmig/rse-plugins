# Review tests with difit

This is the second part of the review: the test files, next to the code they test. The review page and the comment rules are the same as in the code review (tab *Review code with difit*).


## Quickstart

Install [`difit`](https://yoshiko-pg.github.io/difit/) if you haven't yet (see *Review code with difit*). Then, run the **helper script**:

```bash
pr-review-minimal/scripts/review.py tests
```

## Workflow

`review.py tests` shows one row of the *Review steps table* below at a time: a behaviour, with its tests and the code they test.

Each changed test has a 🔗 comment on its `def` line that jumps to the functions it calls, and each of those functions links back to its tests. 

`review.py` reads the files from the *Files* column. Edit the table to regroup the tests. If a changed test file is in no step, `review.py` prints it.

To **leave out the AI-suggested questions** (*Tests questions* below), add `--no-questions`: `pr-review-minimal/scripts/review.py tests --no-questions`.

<details open>
<summary><b>Review steps table</b></summary>

| Step | Behaviour | Files | Done |
|---|---|---|---|
| 1 | Float encoding: time last, lossless | `crabs/mask/utils/float_encoding.py`, `tests/test_unit/test_float_encoding.py` | [ ] |
| 2 | Boxes: from a trajectories clip, and copied into a masks store | `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `tests/test_unit/test_bbox_prompts.py`, `tests/test_unit/test_boxes_from_dataset.py`, `tests/fixtures/trajectories.py` | [ ] |
| 3 | Measuring masks and writing the 8 variables | `crabs/mask/mask_props.py`, `tests/test_unit/test_mask_props.py` | [ ] |
| 4 | Labels layout and `main`: end to end, config, errors, metadata | `crabs/mask/mask_video.py`, `crabs/mask/config/mask_config.yaml`, `tests/test_unit/test_mask_video.py` | [ ] |

</details>

<details>
<summary><b>Tests passes</b></summary>

* Each run starts a new **pass** of the tests review, saved to `pr-review-minimal/comments/tests/pass-N/comments.json`. Add to an earlier pass with `--pass N`. Leave out the preloaded questions (*Tests questions* below) with `--no-questions`.
* Comments here stay in the tests review, also those written on a source file of a step. They do not show in the code review.
* The prompts in *Review code with difit* → *After the review* work here too, with `comments/tests/`.

</details>

<details>
<summary><b>Tests questions</b></summary>

AI-suggested questions, from `2-review/questions-tests.json`.

| # | Question | Where | Step |
|---|---|---|---|
| T1 | Does this overwrite check fail before the fix in `bcefddd`? UNSURE | `tests/test_unit/test_mask_props.py:392` | 3 |
| T2 | No test reaches this `RuntimeError` (early frame read failure). Add one? | `crabs/mask/mask_video.py:384` | 4 |

</details>

<details>
<summary><b>Not tested (by grep of <code>tests/</code>)</b></summary>

Lines as of `1b9c04f`.

| Behaviour | Code |
|---|---|
| `RuntimeError` on early frame read failure | `crabs/mask/mask_video.py:389-393` |
| OpenCV timeouts passed to `VideoCapture` | `crabs/utils/io.py:15-30` |
| Empty config file → `{}` | `crabs/mask/mask_video.py:52` (UNSURE) |
| Rerun after crash mid `add_mask_props_to_group` | `crabs/mask/mask_props.py:259-262` |
| Bash script changes | `bash_scripts/run_mask_array.sh:149-166` |

</details>

<details>
<summary><b>Bug-fix commits: is there a test that fails before the fix?</b></summary>

| Fix | Fail-before test |
|---|---|
| `bcefddd` overwrite fix | `tests/test_unit/test_mask_props.py:392` (UNSURE fails before) |
| `62e8853` early read error | none found |

</details>
