from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from better_pixel_art_downscale import DownscaleOptions, downscale, downscale_by_factor


def _bbox_alpha(image: Image.Image):
    alpha = np.asarray(image.convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(alpha)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _outlined_square(size=16) -> Image.Image:
    data = np.zeros((size, size, 4), dtype=np.uint8)
    data[2:14, 2:14] = (20, 20, 20, 255)
    data[3:13, 3:13] = (220, 60, 80, 255)
    return Image.fromarray(data, mode="RGBA")


def test_outline_never_expands_beyond_silhouette():
    result = downscale(_outlined_square(), (8, 8))
    assert _bbox_alpha(result) == (1, 1, 7, 7)
    pixels = np.asarray(result)
    alpha = pixels[..., 3] > 0
    dark = (np.max(pixels[..., :3], axis=-1) < 80) & alpha
    assert np.all(pixels[~alpha] == 0)
    assert np.all(dark[1, 1:7])
    assert np.all(dark[6, 1:7])
    assert np.all(dark[1:7, 1])
    assert np.all(dark[1:7, 6])


def test_asymmetric_shape_keeps_alignment_at_non_integer_scale():
    data = np.zeros((13, 11, 4), dtype=np.uint8)
    data[2:11, 1:8] = (10, 10, 10, 255)
    data[3:10, 2:7] = (80, 180, 240, 255)
    data[7:11, 8:10] = (10, 10, 10, 255)
    source = Image.fromarray(data, mode="RGBA")
    result = downscale(source, (7, 5))
    bbox = _bbox_alpha(result)
    assert bbox is not None
    assert bbox[0] <= 1
    assert bbox[2] >= 6
    # The extension is on the right in the source and must remain on the right.
    alpha = np.asarray(result)[..., 3] > 0
    assert alpha[:, -1].sum() >= alpha[:, 0].sum()


def test_transparent_rgb_does_not_bleed_into_opaque_pixels():
    data = np.zeros((8, 8, 4), dtype=np.uint8)
    data[..., :3] = (255, 0, 0)  # hidden RGB in transparent pixels
    data[2:6, 2:6] = (0, 90, 255, 255)
    result = downscale(Image.fromarray(data, mode="RGBA"), (4, 4))
    pixels = np.asarray(result)
    opaque = pixels[..., 3] > 0
    assert np.all(pixels[..., 0][opaque] == 0)
    assert np.all(pixels[..., 2][opaque] == 255)


def test_result_is_deterministic():
    rng = np.random.default_rng(42)
    data = rng.integers(0, 256, size=(32, 32, 4), dtype=np.uint8)
    data[..., 3] = np.where(data[..., 3] > 100, 255, 0)
    image = Image.fromarray(data, mode="RGBA")
    first = np.asarray(downscale(image, (11, 13)))
    second = np.asarray(downscale(image, (11, 13)))
    assert np.array_equal(first, second)


def test_factor_api_and_validation():
    image = _outlined_square()
    assert downscale_by_factor(image, 2).size == (8, 8)
    with pytest.raises(ValueError):
        downscale_by_factor(image, 0.5)
    with pytest.raises(ValueError):
        downscale(image, (32, 32))


def test_semitransparent_alpha_is_area_aware():
    data = np.zeros((4, 4, 4), dtype=np.uint8)
    data[:, :2] = (100, 150, 200, 128)
    options = DownscaleOptions(alpha_threshold=0.1, binary_alpha=False)
    result = downscale(Image.fromarray(data, mode="RGBA"), (2, 2), options=options)
    alpha = np.asarray(result)[..., 3]
    assert 60 <= int(alpha[:, 0].mean()) <= 130


def test_fully_opaque_texture_does_not_invent_a_silhouette_outline():
    data = np.zeros((8, 8, 4), dtype=np.uint8)
    data[..., :] = (180, 80, 30, 255)
    data[2:6, 2:6, :3] = (40, 160, 220)
    result = downscale(Image.fromarray(data, mode="RGBA"), (4, 4))
    pixels = np.asarray(result)
    assert np.all(pixels[..., 3] == 255)
    assert np.any(np.all(pixels[..., :3] == (180, 80, 30), axis=-1))


def test_rgb_images_are_supported():
    image = Image.new("RGB", (8, 8), (30, 70, 120))
    result = downscale(image, (4, 4))
    assert result.mode == "RGBA"
    assert result.size == (4, 4)
    assert np.all(np.asarray(result)[..., 3] == 255)
