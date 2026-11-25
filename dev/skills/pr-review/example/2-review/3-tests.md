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
| 4 | Labels layout and `main`: end to end, config, errors, metadata | `crabs/mask/mask_video.py`, `crabs/mask/config/mask_config.yaml`, `tests/test_unit/test_mask_video.py` | [ ] |


## Behaviours the tests check

| Step | Behaviour | Test |
|---|---|---|
| 1 | Float encoding moves `time` last | `tests/test_unit/test_float_encoding.py:19` |
| 1 | Float encoding is bit-identical, NaN included | `tests/test_unit/test_float_encoding.py:25` |
| 2 | Boxes = `position ± shape/2`, keyed by frame | `tests/test_unit/test_bbox_prompts.py:42` |
| 2 | Dask chunking does not change boxes | `tests/test_unit/test_bbox_prompts.py:71` |
| 2 | Sparse time axis raises | `tests/test_unit/test_bbox_prompts.py:110` |
| 2 | Whole video dataset raises | `tests/test_unit/test_bbox_prompts.py:149` |
| 2 | Copied boxes equal source, same chunks and dtype | `tests/test_unit/test_bbox_prompts.py:202` |
| 2 | Boxes NaN-padded when masks `time` longer | `tests/test_unit/test_bbox_prompts.py:247` |
| 2 | Boxes cut when masks `time` shorter, none lost | `tests/test_unit/test_bbox_prompts.py:270` |
| 2 | Box copy errors raise before any write | `tests/test_unit/test_bbox_prompts.py:317` |
| 3 | Copied measuring code matches script (PR #298) | `tests/test_unit/test_mask_props.py:139` |
| 3 | Known ellipse at π/4 gives expected values | `tests/test_unit/test_mask_props.py:169` |
| 3 | Measured frames = frames SAM2 is prompted on | `tests/test_unit/test_mask_props.py:196` |
| 3 | Only frames with finite `position` measured | `tests/test_unit/test_mask_props.py:207` |
| 3 | 8 variables: layout, codecs, values | `tests/test_unit/test_mask_props.py:241` |
| 3 | Values land at right individual, any `label_of` | `tests/test_unit/test_mask_props.py:318` |
| 3 | Bad inputs raise before any write | `tests/test_unit/test_mask_props.py:351` |
| 3 | Existing vars raise unless `overwrite=True` | `tests/test_unit/test_mask_props.py:371` |
| 3 | README snippet for old stores works | `tests/test_unit/test_mask_props.py:398` |
| 4 | Labels chunks, shards, transpose, zstd 15 | `tests/test_unit/test_mask_video.py:221` (asserts `:242-248`) |
| 4 | Labels written per frame, any batch size (renamed) | `tests/test_unit/test_mask_video.py:269` |
| 4 | `main`: masks match trajectories per frame | `tests/test_unit/test_mask_video.py:406` |
| 4 | Separate runs share one store | `tests/test_unit/test_mask_video.py:526` |
| 4 | Bad inputs raise before SAM2 loads (unchanged, not in the diff) | `tests/test_unit/test_mask_video.py:508` |
| 4 | Consolidated metadata lists new arrays | `tests/test_unit/test_mask_video.py:587` |
| 4 | `--no_consolidate` leaves root unconsolidated | `tests/test_unit/test_mask_video.py:614` |
| 4 | Short clip video raises | `tests/test_unit/test_mask_video.py:632` |
| 4 | `mask_config` attr holds run values | `tests/test_unit/test_mask_video.py:652` |
| 4 | Bad config file raises before SAM2 loads | `tests/test_unit/test_mask_video.py:695` |
| 4 | Works on store with stale consolidated root | `tests/test_unit/test_mask_video.py:718` |

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
