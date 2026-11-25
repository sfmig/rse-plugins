# Review tests with difit

## Review steps

You can review the tests like in the workflow before, or you can follow the approach suggested here.

To show a group of tests that check one behaviour, with the code they test, one at a time, run:
```bash
pr-review/scripts/review.py tests
```

You can switch between the files in `difit`'s file list.


Each changed test has a link comment on its `def` line, which jumps to the function it calls. Each function has one equivalent backlink to the test that tests it.

To regroup the tests, edit the table below. `review.py` reads the files from the *Files* column.

| Step | Behaviour | Files | Done |
|---|---|---|---|
| 1 | Float encoding: time last, lossless | `crabs/mask/utils/float_encoding.py`, `tests/test_unit/test_float_encoding.py` | [ ] |
| 2 | Boxes: from a trajectories clip, and copied into a masks store | `crabs/mask/utils/bbox_prompts.py`, `crabs/mask/utils/boxes_from_dataset.py`, `tests/test_unit/test_bbox_prompts.py`, `tests/test_unit/test_boxes_from_dataset.py`, `tests/fixtures/trajectories.py` | [ ] |
| 3 | Measuring masks and writing the 8 variables | `crabs/mask/mask_props.py`, `tests/test_unit/test_mask_props.py` | [ ] |
| 4 | Labels layout and `main`: end to end, config, errors, metadata (also see unchanged `tests/test_unit/test_mask_video.py:508`; per-frame labels test renamed, `:269`) | `crabs/mask/mask_video.py`, `crabs/mask/config/mask_config.yaml`, `tests/test_unit/test_mask_video.py` | [ ] |


## Not tested (by grep of `tests/`)

| Behaviour | Code |
|---|---|
| `RuntimeError` on early frame read failure | `crabs/mask/mask_video.py:389-393` |
| OpenCV timeouts passed to `VideoCapture` | `crabs/utils/io.py:15-30` |
| Empty config file → `{}` | `crabs/mask/mask_video.py:52` (UNSURE) |
| Rerun after crash mid `add_mask_props_to_group` | `crabs/mask/mask_props.py:259-262` |
| Concurrent array jobs on one store | `crabs/mask/mask_video.py:684` |
| `position` and `confidence` time chunks differ | `crabs/mask/mask_props.py:268-269` (UNSURE) |
| Bash script changes | `bash_scripts/run_mask_array.sh:149-166` |

## Bug-fix commits: is there a test that fails before the fix?

| Fix | Fail-before test |
|---|---|
| `bcefddd` overwrite fix | `tests/test_unit/test_mask_props.py:392` (UNSURE fails before) |
| `62e8853` early read error | none found |
