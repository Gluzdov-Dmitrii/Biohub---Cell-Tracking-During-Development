"""EXP236 v2 source-only duplicate-window filter for the frozen Horaz loader."""

import hashlib
import json
from pathlib import Path

import numpy as np
import zarr


BASE_DATASETS_SHA256 = "063fc77e333d615bbb640f8e8062972cca0e25c3c26a95dbf675137263e7b0b3"
PAIR_MAP_NAME = "exp236_source_duplicate_pairs.json"


def window_crosses_duplicate(time_start, window_size, duplicate_starts):
    """A pair t,t+1 lies inside a window iff t is one of its transitions."""
    return any(time_start <= t < time_start + window_size - 1
               for t in duplicate_starts)


def source_duplicate_starts(dataset_id, zarr_path, frame_count, downsample):
    """Verify the pinned pair map against the exact Horaz loader view."""
    assert dataset_id.startswith("6bba_")
    assert tuple(downsample) == (1, 4, 4)
    document = json.loads(Path(__file__).with_name(PAIR_MAP_NAME).read_text())
    assert document["source_embryo"] == "6bba"
    assert document["loader_view"] == "float32_zarr_downsample_1_4_4"
    assert document["window_size"] == 2
    assert dataset_id in document["source_dataset_ids"]
    expected = document["duplicate_starts"].get(dataset_id, [])
    assert expected == sorted(set(expected))
    array = zarr.open(str(zarr_path), mode="r")["0"]
    dz, dy, dx = downsample
    images = array[:frame_count, ::dz, ::dy, ::dx].astype(np.float32)
    assert len(images) == frame_count
    repeated = np.all(images[1:] == images[:-1], axis=tuple(range(1, images.ndim)))
    observed = np.flatnonzero(repeated).tolist()
    if observed != expected:
        raise AssertionError(
            f"Source duplicate pair map mismatch in {dataset_id}: "
            f"expected={expected}, observed={observed}"
        )
    return frozenset(observed)


def patch_horaz_datasets(source):
    """Overlay only source window filtering; keep Horaz's runtime assertion."""
    assert hashlib.sha256(source).hexdigest() == BASE_DATASETS_SHA256
    body = source.decode("utf-8")
    original_import = "from const import VOXEL_SIZE_UM\n"
    assert body.count(original_import) == 1
    body = body.replace(
        original_import,
        original_import +
        "from exp236_duplicate_frame_safeguard import (\n"
        "    source_duplicate_starts, window_crosses_duplicate,\n"
        ")\n",
    )
    original_loop = "    windows = []\n    for time_start in range(image_shape[0] - window_size + 1):\n"
    assert body.count(original_loop) == 1
    body = body.replace(
        original_loop,
        "    duplicate_starts = source_duplicate_starts(\n"
        "        metadata.dataset_id, metadata.zarr_path, image_shape[0], downsample\n"
        "    )\n"
        "    windows = []\n"
        "    for time_start in range(image_shape[0] - window_size + 1):\n"
        "        if window_crosses_duplicate(time_start, window_size, duplicate_starts):\n"
        "            continue\n",
    )
    assert body.count("assert_no_consecutive_duplicate_frames(images, metadata.dataset_id, time_start)") == 1
    return body.encode("utf-8")
