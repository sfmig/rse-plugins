# Aim and diagrams

* [Aim](#aim)
* [Components before and after](#components-before-and-after)
* [Flow diagram](#flow-diagram)

## Aim
[↑ Back to top](#top)

**Before this PR**: the masks store from `mask-tracked-crabs` held only the mask labels. Also: cluster runs needed a config file, wrote one frame per chunk, ignored unknown config keys, and copied the config YAML next to the store.

**With this PR**: the masks store now also holds the bounding boxes used as prompts, and 8 shape parameters (from the ellipse fitted to each mask) for every frame. These use the same `(clip_id, time, individual)` dimensions as the trajectories store. Cluster runs also use less disk space, stop with an error on bad video inputs, and save their config inside the store (`attrs.mask_config`).

## Components before and after
[↑ Back to top](#top)

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

## Flow diagram
[↑ Back to top](#top)

* `mv` = `crabs/mask/mask_video.py`
* `bp` = `crabs/mask/utils/bbox_prompts.py`
* `mp` = `crabs/mask/mask_props.py`

Numbers are line numbers. "a to b" means the call site, then the definition.

Click a box to open its code on GitHub, pinned to commit `1b9c04f`. If clicks do not work in your viewer, use the table below the diagram.

```mermaid
flowchart TD
    subgraph LEG["Legend"]
        direction LR
        L1["Step"] ~~~ L2{"Check"} ~~~ L3["Error"] ~~~ L4["NEW or changed in this PR"]
    end

    A["<b>Load config</b><br/>NEW: load config, merged with defaults<br/>error on unknown key<br/>mv:538 to mv:55"] --> B{"<b>Shard check</b><br/>NEW: shard multiple of chunk?<br/>mv:543"}
    B -- no --> X1["ValueError"]
    B -- yes --> V["For each video"]

    V --> C{"<b>Clip lengths</b><br/>NEW: clip videos long enough?<br/>mv:607 to mv:497"}
    C -- no --> X2["ValueError"]
    C -- yes --> D["<b>Masks group</b><br/>NEW: create masks group<br/>chunks, codecs, mask_config attr<br/>mv:610 to mv:96"]
    D --> E["<b>Copy boxes</b><br/>NEW: copy boxes into masks group<br/>mv:647 to bp:110"]
    E --> F["<b>Read label_of</b><br/>mv:651"]
    F --> LC["For each clip"]

    LC --> G["<b>Extract boxes</b><br/>Extract boxes per frame<br/>mv:660 to bp:14"]
    G --> H{"any boxes?"}
    H -- no --> LC
    H -- yes --> I["<b>Write labels</b><br/>Predict masks with SAM2, write labels<br/>mv:670 to mv:306"]
    I --> J{"<b>Read check</b><br/>NEW: frame read failed early?<br/>mv:389"}
    J -- yes --> X3["RuntimeError"]
    J -- no, next clip --> LC

    LC -- clips done --> K["<b>Mask props</b><br/>NEW: measure masks, write 8 variables<br/>mv:681 to mp:199"]
    K --> K1["<b>Empty vars</b><br/>NEW: write empty variables<br/>mp:301"]
    K1 --> K2["<b>Region write</b><br/>NEW: per clip and time chunk<br/>read labels, measure, region write<br/>mp:330, mp:339"]
    K2 -- next video --> V

    V -- videos done --> Z["<b>Consolidate</b><br/>NEW: consolidate metadata once<br/>mv:684"]

    classDef new fill:#d4edda,stroke:#2e7d32,color:#000
    classDef err fill:#f8d7da,stroke:#c62828,color:#000
    class L4,A,B,C,D,E,J,K,K1,K2,Z new
    class L3,X1,X2,X3 err

    click A href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L55" "crabs/mask/mask_video.py:55" _blank
    click B href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L543" "crabs/mask/mask_video.py:543" _blank
    click C href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L497" "crabs/mask/mask_video.py:497" _blank
    click D href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L96" "crabs/mask/mask_video.py:96" _blank
    click E href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/utils/bbox_prompts.py#L110" "crabs/mask/utils/bbox_prompts.py:110" _blank
    click F href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L651" "crabs/mask/mask_video.py:651" _blank
    click G href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/utils/bbox_prompts.py#L14" "crabs/mask/utils/bbox_prompts.py:14" _blank
    click I href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L306" "crabs/mask/mask_video.py:306" _blank
    click J href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L389" "crabs/mask/mask_video.py:389" _blank
    click K href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_props.py#L199" "crabs/mask/mask_props.py:199" _blank
    click K1 href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_props.py#L301" "crabs/mask/mask_props.py:301" _blank
    click K2 href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_props.py#L330" "crabs/mask/mask_props.py:330" _blank
    click Z href "https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/crabs/mask/mask_video.py#L684" "crabs/mask/mask_video.py:684" _blank
```

<details>
<summary>Links to code for each box</summary>

| Step | Code |
|---|---|
| **Load config**: Load config, merged with defaults | [mv:538](../../crabs/mask/mask_video.py#L538), [mv:55](../../crabs/mask/mask_video.py#L55) |
| **Shard check**: Shard multiple of chunk? | [mv:543](../../crabs/mask/mask_video.py#L543) |
| **Clip lengths**: Clip videos long enough? | [mv:607](../../crabs/mask/mask_video.py#L607), [mv:497](../../crabs/mask/mask_video.py#L497) |
| **Masks group**: Create masks group | [mv:610](../../crabs/mask/mask_video.py#L610), [mv:96](../../crabs/mask/mask_video.py#L96) |
| **Copy boxes**: Copy boxes into masks group | [mv:647](../../crabs/mask/mask_video.py#L647), [bp:110](../../crabs/mask/utils/bbox_prompts.py#L110) |
| **Read label_of** | [mv:651](../../crabs/mask/mask_video.py#L651) |
| **Extract boxes**: Extract boxes per frame | [mv:660](../../crabs/mask/mask_video.py#L660), [bp:14](../../crabs/mask/utils/bbox_prompts.py#L14) |
| **Write labels**: Predict masks, write labels | [mv:670](../../crabs/mask/mask_video.py#L670), [mv:306](../../crabs/mask/mask_video.py#L306) |
| **Read check**: Frame read failed early? | [mv:389](../../crabs/mask/mask_video.py#L389) |
| **Mask props**: Measure masks, write 8 variables | [mv:681](../../crabs/mask/mask_video.py#L681), [mp:199](../../crabs/mask/mask_props.py#L199) |
| **Empty vars**: Write empty variables | [mp:301](../../crabs/mask/mask_props.py#L301) |
| **Region write**: Read labels, measure, region write | [mp:330](../../crabs/mask/mask_props.py#L330), [mp:339](../../crabs/mask/mask_props.py#L339) |
| **Consolidate**: Consolidate metadata once | [mv:684](../../crabs/mask/mask_video.py#L684) |

</details>

