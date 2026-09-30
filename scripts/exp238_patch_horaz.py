"""Derive the EXP238 peak side channel from exact frozen Horaz source bytes.

This has no SSH, queue, label, or inference operation. It refuses other parents.
"""

import argparse
import hashlib
from pathlib import Path


ENGINE_SHA = "4db02fd767ee0e55e4a1ee902fb6ebc2d8683e07c0fe424ee85f7ef906c6dc44"
DETECTION_SHA = "5dfb5c790c50665a5c3f6f46a53e249d92a40a74d860235513a08db0a0153cd3"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(body: str, old: str, new: str) -> str:
    if body.count(old) != 1:
        raise AssertionError(f"Expected one exact patch anchor, found {body.count(old)}: {old[:90]!r}")
    return body.replace(old, new)


def patch_engine(data: bytes) -> bytes:
    assert sha_bytes(data) == ENGINE_SHA, "Unpinned Horaz engine"
    body = data.decode("utf-8")
    body = replace_once(body, "    detect_cells,\n    pool_kernel_from_um,\n",
                        "    detect_cells,\n    emit_exp238_selected_peaks,\n    pool_kernel_from_um,\n")
    old = """        for frame_index, time in enumerate(frame_indices):
            if time in seen_frames:
                continue
            coords = detect_cells(
"""
    new = """        for frame_index, time in enumerate(frame_indices):
            if time in seen_frames:
                continue
            emit_exp238_selected_peaks(
                detection_logits[frame_index][0],
                time,
                detection_threshold,
                detection_pool_kernel,
                bool(adaptive_mode),
                tuple(model_config.downsample),
                float(adaptive_intensity_gamma if adaptive_mode else 1.0),
                bool(detection_config.use_tta),
            )
            coords = detect_cells(
"""
    body = replace_once(body, old, new)
    assert body.count("coords = detect_cells(") == data.decode("utf-8").count("coords = detect_cells(")
    return body.encode("utf-8")


def patch_detection(data: bytes) -> bytes:
    assert sha_bytes(data) == DETECTION_SHA, "Unpinned Horaz detection"
    body = data.decode("utf-8")
    marker = "\n\ndef _flip(\n"
    addition = '''\n\n# EXP238 side channel. The hook is set for one source movie by the derived runner.
# No code in the original detector depends on it, and its default is inert.
EXP238_PEAK_HOOK = None
EXP238_FLOOR = 0.075
EXP238_MAX_PEAKS_PER_FRAME = 16384


def emit_exp238_selected_peaks(
    logits: torch.Tensor,
    time: int,
    selected_threshold: float,
    pool_kernel: tuple[int, int, int],
    adaptive_mode: bool,
    downsample: tuple[int, int, int],
    gamma: float,
    use_tta: bool,
) -> None:
    """Export low-resolution maxima after the original branch decision only."""
    hook = EXP238_PEAK_HOOK
    if hook is None:
        return
    if logits.shape[0] != 1:
        raise ValueError(f"Expected (1,Z,Y,X), got {tuple(logits.shape)}")
    batched = logits.unsqueeze(0)
    probabilities = torch.sigmoid(batched)
    padding = tuple(size // 2 for size in pool_kernel)
    pooled = F.max_pool3d(batched, pool_kernel, stride=1, padding=padding)
    mask = (batched == pooled) & (probabilities > EXP238_FLOOR)
    lowres = torch.nonzero(mask[0, 0])
    if len(lowres) > EXP238_MAX_PEAKS_PER_FRAME:
        raise RuntimeError("EXP238 peak-per-frame cap exceeded; refusing truncation")
    scores = probabilities[0, 0][mask[0, 0]]
    hook(
        int(time),
        lowres.cpu().numpy().astype(np.uint16, copy=False),
        scores.cpu().numpy().astype(np.float32, copy=False),
        {
            "adaptive_mode": bool(adaptive_mode),
            "selected_threshold": float(selected_threshold),
            "floor": EXP238_FLOOR,
            "pool_kernel_zyx": [int(value) for value in pool_kernel],
            "downsample_zyx": [int(value) for value in downsample],
            "gamma": float(gamma),
            "tta": bool(use_tta),
            "logit_shape_zyx": [int(value) for value in logits.shape[1:]],
        },
    )
'''
    body = replace_once(body, marker, addition + marker)
    return body.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--detection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    engine = patch_engine(args.engine.read_bytes())
    detection = patch_detection(args.detection.read_bytes())
    (output / "engine.py").write_bytes(engine)
    (output / "detection.py").write_bytes(detection)
    print(f"engine.py {sha_bytes(engine)}")
    print(f"detection.py {sha_bytes(detection)}")


if __name__ == "__main__":
    main()
