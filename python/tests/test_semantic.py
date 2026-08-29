from __future__ import annotations

import numpy as np
from PIL import Image

from better_pixel_art_downscale import DownscaleOptions, downscale
from better_pixel_art_downscale.semantic import (
    ContentHint,
    SemanticMode,
    SemanticOptions,
    analyze,
    downscale_semantic,
)


def test_item_hint_routes_to_sprite_solver():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[2:14, 7:9] = (220, 180, 40, 255)
    data[3:5, 5:11] = (30, 30, 30, 255)
    image = Image.fromarray(data, mode="RGBA")
    analysis = analyze(image, options=SemanticOptions(content_hint=ContentHint.ITEM))
    assert analysis.mode == SemanticMode.SPRITE


def test_block_hint_splits_opaque_surface_from_cutout_pattern():
    opaque = Image.new("RGBA", (16, 16), (100, 130, 150, 255))
    assert analyze(
        opaque, options=SemanticOptions(content_hint=ContentHint.BLOCK)
    ).mode == SemanticMode.SURFACE

    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[::2, :, :] = (90, 180, 90, 255)
    cutout = Image.fromarray(data, mode="RGBA")
    assert analyze(
        cutout, options=SemanticOptions(content_hint=ContentHint.BLOCK)
    ).mode == SemanticMode.PATTERN


def test_surface_solver_is_source_palette_first():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    palette = np.array(
        [[64, 70, 75, 255], [86, 91, 94, 255], [110, 105, 96, 255], [135, 125, 110, 255]],
        dtype=np.uint8,
    )
    for y in range(16):
        for x in range(16):
            data[y, x] = palette[(x + 2 * y) % len(palette)]
    source = Image.fromarray(data, mode="RGBA")
    result = np.asarray(
        downscale_semantic(
            source,
            (8, 8),
            options=SemanticOptions(content_hint=ContentHint.BLOCK),
        )
    )
    source_colors = {tuple(c) for c in data.reshape(-1, 4)}
    assert all(tuple(c) in source_colors for c in result.reshape(-1, 4))


def test_cutout_block_policy_matches_stable_nearest_phase():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[1::2, 1::2] = (220, 220, 220, 255)
    data[::4, :, :] = (60, 110, 60, 255)
    source = Image.fromarray(data, mode="RGBA")
    expected = source.resize((8, 8), resample=Image.Resampling.NEAREST)
    actual = downscale_semantic(
        source,
        (8, 8),
        options=SemanticOptions(content_hint=ContentHint.BLOCK),
    )
    assert np.array_equal(np.asarray(actual), np.asarray(expected))


def test_sprite_mode_reuses_legacy_solver_with_minecraft_2x_tuning():
    data = np.zeros((16, 16, 4), dtype=np.uint8)
    data[1:15, 7:9] = (210, 180, 60, 255)
    data[5:7, 4:12] = (35, 35, 35, 255)
    source = Image.fromarray(data, mode="RGBA")
    expected = downscale(
        source,
        (8, 8),
        options=DownscaleOptions(alpha_threshold=0.05, internal_edge_weight=0.0),
    )
    actual = downscale_semantic(
        source,
        (8, 8),
        options=SemanticOptions(content_hint=ContentHint.ITEM),
    )
    assert np.array_equal(np.asarray(actual), np.asarray(expected))


def test_semantic_downscale_is_deterministic():
    rng = np.random.default_rng(123)
    data = rng.integers(0, 256, size=(16, 16, 4), dtype=np.uint8)
    data[..., 3] = 255
    image = Image.fromarray(data, mode="RGBA")
    options = SemanticOptions(content_hint=ContentHint.BLOCK)
    first = np.asarray(downscale_semantic(image, (8, 8), options=options))
    second = np.asarray(downscale_semantic(image, (8, 8), options=options))
    assert np.array_equal(first, second)
