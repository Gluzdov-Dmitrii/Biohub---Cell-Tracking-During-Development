"""Train-only photometric domain randomization; never changes spatial targets."""
import numpy as np
import torch


def domain_augment(imgs, coords, masks, *, rng):
    """One photometric draw per temporal window, with shared spatial noise.

    Intensities are normalized upstream but can exceed one. Preserve that range;
    bounded gamma and signed power preserve upstream additive-shift negatives.
    No interpolation, geometry, time reversal or target/label changes occur.
    """
    assert imgs.ndim == 4 and imgs.is_floating_point()
    gain = float(rng.uniform(0.8, 1.2))
    gamma = float(rng.uniform(0.85, 1.15))
    attenuation = float(rng.uniform(0.0, 0.25))
    sigma = float(rng.uniform(0.0, 0.015))
    depth = torch.linspace(0, 1, imgs.shape[1], dtype=imgs.dtype, device=imgs.device)
    if rng.random() < 0.5:
        depth = 1 - depth
    profile = torch.exp(-attenuation * depth)[None, :, None, None]
    noise = torch.as_tensor(rng.standard_normal((1, *imgs.shape[1:])).astype(np.float32),
                            dtype=imgs.dtype, device=imgs.device)
    out = gain * imgs.sign() * imgs.abs().pow(gamma) * profile + sigma * noise
    return out, coords, masks


def test_contract():
    imgs = torch.linspace(-0.1, 2, 7*9*11).reshape(1, 7, 9, 11).repeat(2, 1, 1, 1)
    coords = torch.zeros(2, 5, 3)
    masks = torch.ones(2, 5, dtype=torch.bool)
    original = imgs.clone()
    a, c, m = domain_augment(imgs, coords, masks, rng=np.random.default_rng(123))
    b, _, _ = domain_augment(imgs, coords, masks, rng=np.random.default_rng(123))
    assert a.shape == imgs.shape and a.dtype == imgs.dtype
    assert torch.isfinite(a).all() and torch.equal(a, b)
    assert torch.allclose(a[0], a[1], atol=3e-7, rtol=1e-6), 'Temporal parameters/noise must be shared'
    assert torch.equal(imgs, original) and c is coords and m is masks
    assert not torch.equal(a, imgs)
    return {'status': 'PASS_SHAPE_FINITE_REPRODUCIBLE_TEMPORAL_LABEL_IMMUTABILITY'}


if __name__ == '__main__':
    import json
    print(json.dumps(test_contract()))
