# Atomic branch

## Original branch: not atomic

`smg/add-ellipse-params-to-tracks`, 27 commits from `d005d99`.

<details>
<summary>Why?</summary>

| Sign | Example commits |
|---|---|
| Add then remove the same file | `1c38e9c` adds proposal, `0e68fe2` removes it (931 lines) |
| Follow-up edits of earlier commits | `96390ef`, `763f0a9`, `67c97bc`, `bcefddd`, `5063fe0` |
| One-line comment edits | `03f9788`, `da32599` (`pyproject.toml`) |
| One concern spread over commits | config: `10f406f`, `7f8cd95`, `1286f95`, `1b9c04f` |

</details>

## Scratch branch: atomic

* Local branch `smg/add-ellipse-params-to-tracks-atomic`. 
* Not pushed. 
* Zero diff with the original branch up to `1b9c04f`, the commit whose files match the atomic tip. New commits on the original branch make it stale: see "Keep it up to date".
* Commits ordered by: plumbing → core → wiring → tests → docs.

<details>
<summary>Check zero diff</summary>

```bash
# To check same final code as the original branch: this should return empty output
git diff smg/add-ellipse-params-to-tracks smg/add-ellipse-params-to-tracks-atomic
```

</details>


## List of commits
To list the atomic commits, oldest first
```bash
git log --reverse --oneline d005d99..smg/add-ellipse-params-to-tracks-atomic
```


Weight rule: 🔴 **high** = changes data written to the store; 🟠 **med** = changes run behaviour; 🟢 **low** = deps, tests, docs, logging.

| # | Commit | Purpose | Files | +/- | Weight |
|---|---|---|---|---|---|
| 1 | `3b07d9c` | Add `scikit-image` dependency | `pyproject.toml` | +2/-1 | 🟢 low |
| 2 | `978488a` | OpenCV open/read timeouts 300 s | `crabs/utils/io.py` | +16/-1 | 🟠 med |
| 3 | `8a30314` | Rename `boxes_from_dataset` → `bbox_prompts` | module, test, import | +3/-7 | 🟢 low |
| 4 | `b8fe1a2` | Log peak memory with `/usr/bin/time -v` | `run_mask_array.sh` | +4/-1 | 🟢 low |
| 5 | `501a731` | Labels: 8-frame chunks, time last, zstd 15 | `mask_video.py`, `mask_config.yaml` | +49/-19 | 🔴 high |
| 6 | `038b04b` | Fail on short or unreadable clip videos | `mask_video.py` | +45/-0 | 🟠 med |
| 7 | `737101a` | Config defaults from yaml, unknown keys error, `mask_config` attr | `mask_video.py`, `run_mask_array.sh` | +54/-25 | 🟠 med |
| 8 | `cfdb81b` | Add `float_var_encoding` | `float_encoding.py` | +44/-0 | 🔴 high |
| 9 | `dc8fabd` | Add `copy_video_bboxes_to_masks` | `bbox_prompts.py` | +112/-0 | 🔴 high |
| 10 | `b13bcd0` | Add `mask_props` module | `mask_props.py` | +351/-0 | 🔴 high |
| 11 | `750c319` | Wire box copy, mask props, consolidation into `main` | `mask_video.py` | +24/-5 | 🔴 high |
| 12 | `3b0ce35` | Tests: `float_encoding` | `test_float_encoding.py` | +48/-0 | 🟢 low |
| 13 | `aecc455` | Tests: box copy, plus `confidence` fixture | `test_bbox_prompts.py`, `fixtures/trajectories.py` | +206/-1 | 🟢 low |
| 14 | `064a9a9` | Tests: `mask_props` | `test_mask_props.py` | +447/-0 | 🟢 low |
| 15 | `b493975` | Tests: `mask_video` | `test_mask_video.py` | +198/-22 | 🟢 low |
| 16 | `a70f978` | Docs: README and HPC guide | `README.md`, `MaskTrackedCrabsHPC.md` | +65/-12 | 🟢 low |

## Limits

- Only the final tree is checked equal. Middle commits were not run.
- Tests come after code, so commits 5–11 may fail old tests.
- Comments were not stripped. That would make the diff non-empty.
- Built with `/private/tmp/claude-501/-Users-sofia-arc-project-Zoo-crabs-crabs-exploration/a9bea622-a385-4e05-b355-6934d0117455/scratchpad/build_stages.py`.

