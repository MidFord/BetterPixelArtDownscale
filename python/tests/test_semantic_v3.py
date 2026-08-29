from __future__ import annotations

import numpy as np
from PIL import Image

from better_pixel_art_downscale.semantic import ContentHint, SemanticOptions, downscale_semantic
from better_pixel_art_downscale.semantic_v3 import (
    CutoutPolicy,
    analyze_cutout,
    downscale_cutout,
    downscale_semantic_v3,
)


def test_spanning_thin_lattice_preserves_subcell_thickness():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[:, 7:9] = (160, 190, 210, 255)
    source = Image.fromarray(data, mode="RGBA")

    analysis = analyze_cutout(source, (8, 8))
    assert analysis.policy == CutoutPolicy.SPANNING_COVERAGE

    result = np.asarray(downscale_cutout(source, (8, 8)))
    occupied = result[..., 3] > 0
    assert np.all(occupied[:, 3:5])
    assert int(occupied.sum()) == 16


def test_freestanding_thin_feature_uses_bbox_phase_only_when_nearest_erases_it():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[0, 1:8:2] = (80, 180, 90, 255)
    source = Image.fromarray(data, mode="RGBA")

    stable = source.resize((8, 8), resample=Image.Resampling.NEAREST)
    assert not np.any(np.asarray(stable)[..., 3] > 0)

    analysis = analyze_cutout(source, (8, 8))
    assert analysis.policy == CutoutPolicy.BBOX_PHASE_RESCUE
    result = np.asarray(downscale_cutout(source, (8, 8)))
    assert int(np.sum(result[..., 3] > 0)) == 4


def test_tiny_feature_keeps_stable_phase_when_it_already_survives():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[5, 6:10] = (0, 0, 0, 255)
    data[5, 7] = (255, 30, 20, 255)
    data[5, 9] = (20, 220, 255, 255)
    source = Image.fromarray(data, mode="RGBA")

    expected = source.resize((8, 8), resample=Image.Resampling.NEAREST)
    analysis = analyze_cutout(source, (8, 8))
    assert analysis.policy == CutoutPolicy.STABLE_PHASE
    actual = downscale_cutout(source, (8, 8))
    assert np.array_equal(np.asarray(actual), np.asarray(expected))


def test_ghost_alpha_overlay_preserves_low_alpha_information():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[..., :3] = (40, 40, 40)
    data[..., 3] = 1
    data[1::2, 1::2] = (230, 230, 230, 255)
    source = Image.fromarray(data, mode="RGBA")

    analysis = analyze_cutout(source, (8, 8))
    assert analysis.ghost_alpha_ratio > 0.02
    assert analysis.policy == CutoutPolicy.STABLE_PHASE

    expected = source.resize((8, 8), resample=Image.Resampling.NEAREST)
    actual = downscale_cutout(source, (8, 8))
    assert np.array_equal(np.asarray(actual), np.asarray(expected))
    assert np.all(np.asarray(actual)[..., 3] == 255)


def test_dense_cutout_uses_coverage_without_inventing_rgb():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    for y in range(16):
        for x in range(16):
            if (x + y) % 3 == 0:
                data[y, x] = (40, 130, 70, 255)
            elif (2 * x + y) % 7 == 0:
                data[y, x] = (120, 190, 80, 255)
    source = Image.fromarray(data, mode="RGBA")

    analysis = analyze_cutout(source, (8, 8))
    assert analysis.policy == CutoutPolicy.DENSE_COVERAGE
    result = np.asarray(downscale_cutout(source, (8, 8)))
    source_rgb = {tuple(rgb) for rgb in data[data[..., 3] > 0, :3]}
    assert all(tuple(rgb) in source_rgb for rgb in result[result[..., 3] > 0, :3])


def test_v3_is_identical_to_v2_for_items_and_opaque_surfaces():
    item_data = np.zeros((16, 16, 4), dtype=np.uint8)
    item_data[2:14, 7:9] = (220, 170, 50, 255)
    item = Image.fromarray(item_data, mode="RGBA")
    item_options = SemanticOptions(content_hint=ContentHint.ITEM)
    assert np.array_equal(
        np.asarray(downscale_semantic_v3(item, (8, 8), options=item_options)),
        np.asarray(downscale_semantic(item, (8, 8), options=item_options)),
    )

    rng = np.random.default_rng(12)
    surface_data = rng.integers(0, 256, size=(16, 16, 4), dtype=np.uint8)
    surface_data[..., 3] = 255
    surface = Image.fromarray(surface_data, mode="RGBA")
    surface_options = SemanticOptions(content_hint=ContentHint.BLOCK)
    assert np.array_equal(
        np.asarray(downscale_semantic_v3(surface, (8, 8), options=surface_options)),
        np.asarray(downscale_semantic(surface, (8, 8), options=surface_options)),
    )
