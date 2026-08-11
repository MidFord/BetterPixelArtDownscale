from __future__ import annotations

import numpy as np
from PIL import Image

import image_resize
import image_resize_edge
import pattern_noise


def test_legacy_process_image_accepts_historical_signature(tmp_path):
    data = np.zeros((8, 8, 4), dtype=np.uint8)
    data[1:7, 1:7] = (0, 0, 0, 255)
    data[2:6, 2:6] = (255, 180, 20, 255)
    path = tmp_path / "input.png"
    Image.fromarray(data, mode="RGBA").save(path)
    result = image_resize_edge.processImage(path, 2, 2)
    assert result.size == (4, 4)


def test_simplify_colors_returns_the_new_image():
    image = Image.new("RGBA", (1, 1), (100, 100, 100, 255))
    simplified = image_resize.SimplifyColors(image, 2)
    assert simplified.getpixel((0, 0)) != image.getpixel((0, 0))


def test_pattern_has_exact_sum_and_length():
    pattern = pattern_noise.create_pattern(17, 6)
    assert len(pattern) == 6
    assert sum(pattern) == 17
    assert max(pattern) - min(pattern) <= 1
