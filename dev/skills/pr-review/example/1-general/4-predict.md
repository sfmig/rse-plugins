# Predict (optional)

Fill in "My sketch" before reading on. Then compare with "PR does".

| Question | My sketch | PR does | Same? |
|---|---|---|---|
| Where do boxes enter the masks store? | | `crabs/mask/utils/bbox_prompts.py:110` | |
| When are masks measured: per frame or after the video? | | after last clip, `crabs/mask/mask_video.py:681` | |
| Read labels from memory or from the store? | | from the store, `crabs/mask/mask_props.py:314-316` | |
| How is label → individual mapped? | | `crabs/mask/mask_props.py:192` | |
| How is memory bounded while measuring? | | one time chunk, `crabs/mask/mask_props.py:317-323` | |
| Where do config defaults live? | | `crabs/mask/config/mask_config.yaml` | |
| How is the run's config recorded? | | group attr, `crabs/mask/mask_video.py:633` | |
| What happens on a bad clip video? | | error, `crabs/mask/mask_video.py:389`, `:497` | |

Rows marked "no": look at them first in block 2.
