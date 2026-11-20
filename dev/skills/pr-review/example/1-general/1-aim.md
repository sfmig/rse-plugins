#  Aim

## Aim

**Before this PR**: the masks store from `mask-tracked-crabs` held only the mask labels. Also: cluster runs needed a config file, wrote one frame per chunk, ignored unknown config keys, and copied the config YAML next to the store.

**With this PR**: the masks store now also holds the bounding boxes used as prompts, and 8 shape parameters (from the ellipse fitted to each mask) for every frame. These use the same `(clip_id, time, individual)` dimensions as the trajectories store. Cluster runs also use less disk space, stop with an error on bad video inputs, and save their config inside the store (`attrs.mask_config`).

## Components: before → after

Green = new or changed. Grey = unchanged. Each box names a real file or function.

### Before (`d005d99`)

```mermaid
flowchart LR
    SH["run_mask_array.sh<br/>config file required"] --> M["mask_video.main"]
    SH --> CP["cp config yaml<br/>to store root"]
    M --> LC["load_mask_config<br/>.get with inline defaults"]
    M --> EX["boxes_from_dataset<br/>extract_bboxes_from_clip"]
    M --> CS["create_mask_store<br/>1 frame per chunk, default zstd"]
    M --> W["write_clip_masks_to_store"]
    W --> OV["io.open_video<br/>default timeouts"]
    CS --> ST[("masks group<br/>labels, label_of")]
    W --> ST
```

### After (`1b9c04f`)

```mermaid
flowchart LR
    SH["run_mask_array.sh<br/>config file optional, time -v"] --> M["mask_video.main"]
    M --> LC["load_mask_config<br/>defaults from mask_config.yaml<br/>unknown keys error"]
    M --> CL["_check_clip_lengths"]
    M --> EX["bbox_prompts<br/>extract_bboxes_from_clip"]
    M --> CS["create_mask_store<br/>8-frame chunks, time last, zstd 15"]
    M --> CB["bbox_prompts<br/>copy_video_bboxes_to_masks"]
    M --> W["write_clip_masks_to_store<br/>error on early read fail"]
    M --> MP["mask_props<br/>add_mask_props_to_group"]
    M --> CON["zarr.consolidate_metadata"]
    W --> OV["io.open_video<br/>300 s timeouts"]
    MP --> SK["skimage regionprops_table"]
    CB --> FE["float_encoding<br/>float_var_encoding"]
    MP --> FE
    CS --> ST[("masks group<br/>labels, label_of<br/>position, shape, confidence<br/>8 mask and ellipse vars<br/>attrs.mask_config")]
    CB --> ST
    W --> ST
    MP --> ST

    classDef new fill:#d4edda,stroke:#2e7d32,color:#000
    class SH,LC,CL,EX,CS,CB,W,MP,CON,OV,FE,ST new
```
