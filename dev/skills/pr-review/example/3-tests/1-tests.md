# 3.1 Tests as the spec

## Test files to review

To review these files in difit, add them as a row of the session table in `2-review/2-difit.md`, or use `pr-review/scripts/review.py all`.

| # | Files | Lines | Done |
|---|---|---|---|
| 1 | `tests/test_unit/test_float_encoding.py` | 48 | [ ] |
| 2 | `tests/test_unit/test_bbox_prompts.py`, `tests/test_unit/test_boxes_from_dataset.py`, `tests/fixtures/trajectories.py` | 493 | [ ] |
| 3 | `tests/test_unit/test_mask_props.py` | 447 | [ ] |
| 4 | `tests/test_unit/test_mask_video.py` | 220 | [ ] |

Row 2 pairs the renamed test file with its old version.

## Behaviours the tests check

| Behaviour | Test |
|---|---|
| Float encoding moves `time` last | `tests/test_unit/test_float_encoding.py:19` |
| Float encoding is bit-identical, NaN included | `tests/test_unit/test_float_encoding.py:25` |
| Boxes = `position ± shape/2`, keyed by frame | `tests/test_unit/test_bbox_prompts.py:42` |
| Dask chunking does not change boxes | `tests/test_unit/test_bbox_prompts.py:71` |
| Sparse time axis raises | `tests/test_unit/test_bbox_prompts.py:110` |
| Whole video dataset raises | `tests/test_unit/test_bbox_prompts.py:149` |
| Copied boxes equal source, same chunks and dtype | `tests/test_unit/test_bbox_prompts.py:202` |
| Boxes NaN-padded when masks `time` longer | `tests/test_unit/test_bbox_prompts.py:247` |
| Boxes cut when masks `time` shorter, none lost | `tests/test_unit/test_bbox_prompts.py:270` |
| Box copy errors raise before any write | `tests/test_unit/test_bbox_prompts.py:317` |
| Copied measuring code matches script (PR #298) | `tests/test_unit/test_mask_props.py:139` |
| Known ellipse at π/4 gives expected values | `tests/test_unit/test_mask_props.py:171` |
| Label not in `label_of` raises | `tests/test_unit/test_mask_props.py:200` |
| Measured frames = frames SAM2 is prompted on | `tests/test_unit/test_mask_props.py:215` |
| Only frames with finite `position` measured | `tests/test_unit/test_mask_props.py:226` |
| 8 variables: layout, codecs, values | `tests/test_unit/test_mask_props.py:260` |
| Values land at right individual, any `label_of` | `tests/test_unit/test_mask_props.py:339` |
| Bad inputs raise before any write | `tests/test_unit/test_mask_props.py:372` |
| Existing vars raise unless `overwrite=True` | `tests/test_unit/test_mask_props.py:392` |
| README snippet for old stores works | `tests/test_unit/test_mask_props.py:419` |
| Labels chunks, shards, transpose, zstd 15 | `tests/test_unit/test_mask_video.py:221` (asserts `:242-248`) |
| `main`: masks match trajectories per frame | `tests/test_unit/test_mask_video.py:406` |
| Bad inputs raise before SAM2 loads | `tests/test_unit/test_mask_video.py:508` |
| Separate runs share one store | `tests/test_unit/test_mask_video.py:526` |
| Consolidated metadata lists new arrays | `tests/test_unit/test_mask_video.py:587` |
| Short clip video raises | `tests/test_unit/test_mask_video.py:614` |
| `mask_config` attr holds run values | `tests/test_unit/test_mask_video.py:634` |
| Bad config file raises before SAM2 loads | `tests/test_unit/test_mask_video.py:677` |
| Works on store with stale consolidated root | `tests/test_unit/test_mask_video.py:700` |

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
