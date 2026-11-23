# Signatures change

This file shows some of the key diffs and where each change sits in the pipeline. Section names match the bold box names  in `Workflow` (`2-flow.md`).

Selection: every top-level function or UPPER_CASE constant added, removed or with changed parameters, plus config keys and two behaviour-only changes (`load_mask_config`, `open_video`) picked by reading the diff.

## Load config, shard check

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class C,D,E,F,G,I,J,K,Z other
    class A,B here
```

```diff
 # crabs/mask/mask_video.py
+def _read_yaml(path: str | Path) -> dict                          # :50

 def load_mask_config(config_file: str) -> dict                    # :55
+    # now merges DEFAULT_MASK_CONFIG; raises ValueError on unknown keys
```

```diff
 # crabs/mask/config/mask_config.yaml
+n_frames_per_chunk: 8          # :22
-n_frames_per_shard: 32
+n_frames_per_shard: 16         # :33

 # bash_scripts/run_mask_array.sh
-MASK_CONFIG_FILE="/ceph/zoo/users/sminano/cluster_mask_config.yaml"
+MASK_CONFIG_FILE=""            # :37
-    --mask_config_file $MASK_CONFIG_FILE
+    "${CONFIG_ARGS[@]}"        # :149-153, :166
-cp "$MASK_CONFIG_FILE" "$MASK_ZARR_STORE_OUTPUT"/"$VIDEO_ID"_mask_config.yaml
```

`--mask_config_file` default unchanged: `DEFAULT_MASK_CONFIG` (`crabs/mask/mask_video.py:744-746`).

<a id="sig-c"></a>

## Clip lengths

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,D,E,F,G,I,J,K,Z other
    class C here
```

```diff
 # crabs/mask/mask_video.py
+def _check_clip_lengths(ds_video: xr.Dataset, clip_paths: list[Path]) -> None   # :497
```

<a id="sig-d"></a>

## Masks group

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,C,E,F,G,I,J,K,Z other
    class D here
```

```diff
 # crabs/mask/mask_video.py
+LABELS_COMPRESSOR = ZstdCodec(level=15)                           # :39
+LABELS_TIME_LAST = TransposeCodec(order=(0, 2, 3, 1))             # :44

 def create_mask_store(                                            # :96
     store_path, video_id, clip_ids, n_frames, individuals,
     image_shape, metadata_dict,
+    n_frames_per_chunk: int,
     n_frames_per_shard: int | None,
     zarr_mode_group: str,
 ) -> zarr.Array
```

<a id="sig-e"></a>

## Copy boxes

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,C,D,F,G,I,J,K,Z other
    class E here
```

```diff
 # crabs/mask/utils/bbox_prompts.py
+BBOX_VARS = ["position", "shape", "confidence"]                  # :11
+def copy_video_bboxes_to_masks(
+    mask_store_path: str | Path, ds_video: xr.Dataset
+) -> None                                                          # :110
```

Uses `float_var_encoding` (section Mask props).

<a id="sig-g"></a>

## Extract boxes

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,C,D,E,F,I,J,K,Z other
    class G here
```

```diff
 # crabs/mask/utils/boxes_from_dataset.py → crabs/mask/utils/bbox_prompts.py
 def extract_bboxes_from_clip(ds_clip: xr.Dataset) -> dict          # moved, :14
 def _validate_time_axis_is_dense(ds, clip_id, n_frames_in_clip)    # moved, :87
```

<a id="sig-i"></a>

## Write labels, read check

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,C,D,E,F,G,K,Z other
    class I,J here
```

```diff
 # crabs/mask/mask_video.py
 def write_clip_masks_to_store(                                    # :306
     video_clip_path, tracked_bboxes_dict, labels_array,
     clip_index, label_of, predictor, max_prompts_per_batch,
-    n_frames_per_shard: int | None,
 ) -> int
+    # now raises RuntimeError on early read failure (:389-393)
```

```diff
 # crabs/utils/io.py
+VIDEO_OPEN_TIMEOUT_MS = 300_000                                   # :15
+VIDEO_READ_TIMEOUT_MS = 300_000                                   # :16
 def open_video(video_path: str) -> cv2.VideoCapture               # :19
-    cv2.VideoCapture(video_path)
+    cv2.VideoCapture(video_path, cv2.CAP_ANY, [open/read timeouts])  # :21-30
```

<a id="sig-k"></a>

## Mask props

```mermaid
flowchart LR
    A["Load config"] --> B["Shard check"] --> C["Clip lengths"] --> D["Masks group"] --> E["Copy boxes"] --> F["Read label_of"] --> G["Extract boxes"] --> I["Write labels"] --> J["Read check"] --> K["Mask props"] --> Z["Consolidate"]
    classDef here fill:#0969da,color:#fff,stroke:#0969da
    classDef other fill:#f6f8fa,color:#57606a,stroke:#d0d7de
    class A,B,C,D,E,F,G,I,J,Z other
    class K here
```

```diff
 # crabs/mask/mask_props.py (new)
+PROPS_TO_VARS, SCALAR_VARS, MASK_PROPS_VARS                       # :22, :32, :35 (6 / 7 / 8 vars)
+def measure_label_frame(label_frame: np.ndarray) -> dict[str, np.ndarray]   # :38
+def frames_with_boxes(ds_clip: xr.Dataset) -> np.ndarray                    # :62
+def compute_clip_mask_props_dataset(                                        # :72
+    labels_array: zarr.Array | np.ndarray,
+    clip_index: int,
+    time_slice: slice,
+    frames: np.ndarray,
+    individual_of_label: np.ndarray,
+) -> xr.Dataset
+def _invert_label_of(label_of: np.ndarray) -> np.ndarray                    # :192
+def add_mask_props_to_group(                                                # :199
+    store_path: str | Path, video_id: str, overwrite: bool = False
+) -> None
```

```diff
 # crabs/mask/utils/float_encoding.py (new)
+def float_var_encoding(dims: tuple[str, ...]) -> dict                       # :23
```
