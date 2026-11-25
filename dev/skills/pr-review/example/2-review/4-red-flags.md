# AI red flags

## CI changes

| Check | Result | Evidence |
|---|---|---|
| CI workflow changed? | no | `git diff d005d99 HEAD -- .github` empty |
| Coverage threshold changed? | no | `pyproject.toml` diff only adds `scikit-image` (`:45`) |
| Tests removed? | file renamed, 4 tests kept | `test_boxes_from_dataset.py` → `test_bbox_prompts.py:42,71,110,149` |
| Tests skipped or xfail added? | no | grep `skip|xfail` over test diff: no hits |

```bash
git diff d005d99 HEAD --stat -- .github pyproject.toml
git diff d005d99 HEAD -- tests | grep -n "^[+-].*\(skip\|xfail\)"
```

## Reinvented helpers

| New helper | Similar existing code | Relation |
|---|---|---|
| `compute_clip_mask_props_dataset` `crabs/mask/mask_props.py:72` | `compute_mask_props_dataset` `scripts/generate_masks_from_bboxes.py:434` | Stated copy (`mask_props.py:3-6`); agreement test `test_mask_props.py:139` |
| `add_mask_props_to_group` `crabs/mask/mask_props.py:199` | `append_mask_props` `scripts/generate_masks_from_bboxes.py:518` | UNSURE overlap; compare |
| `_read_yaml` `crabs/mask/mask_video.py:50` | inline `yaml.safe_load` in `crabs/tracker/track_video.py:91`, `crabs/detector/train_model.py:85`, `crabs/detector/utils/evaluate.py:206` | No shared loader exists |
| `frames_with_boxes` `crabs/mask/mask_props.py:62` | presence test in `extract_bboxes_from_clip` `crabs/mask/utils/bbox_prompts.py:71` | Same rule, two places: `notnull().any(space, individual)` vs `~isnan(x)` |
| `_invert_label_of` `crabs/mask/mask_props.py:192` | README reverse lookup `crabs/mask/README.md:74` | No code duplicate found |
| `float_var_encoding` `crabs/mask/utils/float_encoding.py:23` | none | No other codec helper in `crabs/` |
| `_check_clip_lengths` `crabs/mask/mask_video.py:497` | `_get_frame_shape_and_max_frames_in_video` `crabs/mask/mask_video.py:470` | Both read video headers per clip |

```bash
grep -rn "yaml.safe_load\|regionprops\|TransposeCodec\|BloscCodec" --include='*.py' crabs scripts
```

