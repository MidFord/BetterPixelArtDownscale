"""Experimental semantic pixel-art downscaling.

The v2 path separates silhouette-sensitive sprites from surface textures. It is
source-palette-first: block reconstruction selects colors that exist in each
source cell instead of inventing BOX-style blends.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import BinaryIO, TypeAlias

import numpy as np
from PIL import Image

from .core import downscale as _legacy_downscale
from .options import DownscaleOptions

ImageInput: TypeAlias = Image.Image | str | Path | BinaryIO


class SemanticMode(str, Enum):
    AUTO = "auto"
    SPRITE = "sprite"
    SURFACE = "surface"
    PATTERN = "pattern"


class ContentHint(str, Enum):
    AUTO = "auto"
    ITEM = "item"
    BLOCK = "block"
    ENTITY = "entity"


@dataclass(frozen=True, slots=True)
class SemanticOptions:
    mode: SemanticMode = SemanticMode.AUTO
    content_hint: ContentHint = ContentHint.AUTO
    sprite_alpha_threshold: float = 0.05
    sprite_thin_feature_threshold: float = 0.125
    surface_phase_weight: float = 0.40
    surface_anchor_weight: float = 0.02
    surface_coverage_weight: float = 0.08
    surface_dark_noise_penalty: float = 0.18
    surface_structure_weight: float = 0.0
    surface_dither_suppression: float = 0.80
    tile_aware: bool = True


@dataclass(slots=True)
class SemanticAnalysis:
    rgba: np.ndarray
    alpha: np.ndarray
    opaque: np.ndarray
    luminance: np.ndarray
    structure: np.ndarray
    texture: np.ndarray
    dither: np.ndarray
    opaque_ratio: float
    bbox_fill_ratio: float
    bbox_area_ratio: float
    edge_touch_count: int
    mode: SemanticMode


def _open_rgba(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGBA")
    with Image.open(image) as opened:
        return opened.convert("RGBA")


def _shift(array: np.ndarray, dy: int, dx: int, *, wrap: bool) -> np.ndarray:
    if wrap:
        return np.roll(array, shift=(dy, dx), axis=(0, 1))
    py, px = abs(dy), abs(dx)
    padded = np.pad(array, ((py, py), (px, px)), mode="edge")
    y0, x0 = py - dy, px - dx
    return padded[y0 : y0 + array.shape[0], x0 : x0 + array.shape[1]]


def _box3(array: np.ndarray, *, wrap: bool) -> np.ndarray:
    mode = "wrap" if wrap else "edge"
    padded = np.pad(array, 1, mode=mode)
    result = np.zeros_like(array, dtype=np.float64)
    for dy in range(3):
        for dx in range(3):
            result += padded[dy : dy + array.shape[0], dx : dx + array.shape[1]]
    return result / 9.0


def _luminance(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(np.float64) / 255.0
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def _feature_maps(rgba: np.ndarray, tile_aware: bool):
    alpha = rgba[..., 3].astype(np.float64) / 255.0
    opaque = alpha > (1.0 / 255.0)
    luminance = _luminance(rgba[..., :3])
    wrap = bool(tile_aware and opaque.mean() > 0.98)

    left = _shift(luminance, 0, -1, wrap=wrap)
    right = _shift(luminance, 0, 1, wrap=wrap)
    up = _shift(luminance, -1, 0, wrap=wrap)
    down = _shift(luminance, 1, 0, wrap=wrap)
    gx, gy = 0.5 * (right - left), 0.5 * (down - up)

    jxx = _box3(gx * gx, wrap=wrap)
    jyy = _box3(gy * gy, wrap=wrap)
    jxy = _box3(gx * gy, wrap=wrap)
    coherence = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy**2) / (jxx + jyy + 1e-9)
    gradient = np.sqrt(gx * gx + gy * gy)

    one_step = (
        np.abs(luminance - left)
        + np.abs(luminance - right)
        + np.abs(luminance - up)
        + np.abs(luminance - down)
    ) / 4.0
    two_step = (
        np.abs(luminance - _shift(luminance, 0, -2, wrap=wrap))
        + np.abs(luminance - _shift(luminance, 0, 2, wrap=wrap))
        + np.abs(luminance - _shift(luminance, -2, 0, wrap=wrap))
        + np.abs(luminance - _shift(luminance, 2, 0, wrap=wrap))
    ) / 4.0
    recurrence = np.clip(1.0 - 4.0 * two_step, 0.0, 1.0)
    dither = np.clip(4.0 * one_step, 0.0, 1.0) * recurrence * (1.0 - 0.55 * coherence)

    mean = _box3(luminance, wrap=wrap)
    variance = np.maximum(0.0, _box3(luminance * luminance, wrap=wrap) - mean * mean)
    texture = np.clip(4.0 * np.sqrt(variance), 0.0, 1.0)
    structure = np.clip(5.0 * gradient, 0.0, 1.0) * coherence * (1.0 - 0.80 * dither)
    return luminance, structure * opaque, texture * opaque, dither * opaque


def _bbox_stats(opaque: np.ndarray) -> tuple[float, float, int]:
    h, w = opaque.shape
    ys, xs = np.nonzero(opaque)
    if not len(xs):
        return 0.0, 0.0, 0
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    bbox_area = max(1, int((x1 - x0) * (y1 - y0)))
    fill = float(opaque[y0:y1, x0:x1].mean())
    touches = sum((opaque[0].any(), opaque[-1].any(), opaque[:, 0].any(), opaque[:, -1].any()))
    return fill, bbox_area / float(w * h), int(touches)


def analyze(image: ImageInput, *, options: SemanticOptions | None = None) -> SemanticAnalysis:
    options = options or SemanticOptions()
    rgba = np.asarray(_open_rgba(image), dtype=np.uint8)
    alpha = rgba[..., 3].astype(np.float64) / 255.0
    opaque = alpha > (1.0 / 255.0)
    luminance, structure, texture, dither = _feature_maps(rgba, options.tile_aware)
    opaque_ratio = float(opaque.mean())
    fill, bbox_area, touches = _bbox_stats(opaque)

    if options.mode != SemanticMode.AUTO:
        mode = options.mode
    elif options.content_hint == ContentHint.ITEM:
        mode = SemanticMode.SPRITE
    elif options.content_hint == ContentHint.BLOCK:
        mode = SemanticMode.SURFACE if opaque_ratio > 0.98 else SemanticMode.PATTERN
    elif options.content_hint == ContentHint.ENTITY:
        mode = SemanticMode.SURFACE if opaque_ratio > 0.98 else SemanticMode.SPRITE
    elif opaque_ratio > 0.94:
        mode = SemanticMode.SURFACE
    elif bbox_area > 0.82 and touches >= 2 and fill < 0.72:
        mode = SemanticMode.PATTERN
    else:
        mode = SemanticMode.SPRITE

    return SemanticAnalysis(
        rgba=rgba,
        alpha=alpha,
        opaque=opaque,
        luminance=luminance,
        structure=structure,
        texture=texture,
        dither=dither,
        opaque_ratio=opaque_ratio,
        bbox_fill_ratio=fill,
        bbox_area_ratio=bbox_area,
        edge_touch_count=touches,
        mode=mode,
    )


def _rgb_to_oklab(rgb_u8: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb_u8, dtype=np.float64) / 255.0
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    r, g, b = linear[..., 0], linear[..., 1], linear[..., 2]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack(
        (
            0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
        ),
        axis=-1,
    )


def _axis_cells(source_length: int, target_length: int):
    scale = source_length / target_length
    cells = []
    for index in range(target_length):
        start, end = index * scale, (index + 1) * scale
        indices = np.arange(int(np.floor(start)), int(np.ceil(end)), dtype=np.intp)
        weights = np.maximum(
            0.0,
            np.minimum(indices + 1.0, end) - np.maximum(indices.astype(np.float64), start),
        )
        cells.append((indices, weights))
    return cells


def _sprite_downscale(image: Image.Image, size: tuple[int, int], options: SemanticOptions):
    return _legacy_downscale(
        image,
        size,
        options=DownscaleOptions(
            alpha_threshold=options.sprite_alpha_threshold,
            thin_feature_threshold=options.sprite_thin_feature_threshold,
            preserve_thin_features=True,
            preserve_outline=True,
            preserve_internal_edges=True,
            internal_edge_weight=0.0,
        ),
    )


def _surface_downscale(analysis: SemanticAnalysis, size: tuple[int, int], options: SemanticOptions):
    rgba, alpha = analysis.rgba, analysis.alpha
    source_h, source_w = alpha.shape
    target_w, target_h = size
    x_cells = _axis_cells(source_w, target_w)
    y_cells = _axis_cells(source_h, target_h)
    output = np.zeros((target_h, target_w, 4), dtype=np.uint8)
    binary_alpha = bool(np.all((rgba[..., 3] == 0) | (rgba[..., 3] == 255)))

    for ty, (ys, yw) in enumerate(y_cells):
        for tx, (xs, xw) in enumerate(x_cells):
            weights = np.multiply.outer(yw, xw)
            region = np.ix_(ys, xs)
            alpha_region = alpha[region]
            effective = weights * alpha_region
            valid = effective > 0
            if not np.any(valid):
                continue

            colors = rgba[region][valid]
            color_weights = effective[valid]
            labs = _rgb_to_oklab(colors[:, :3])
            desired = np.average(labs, axis=0, weights=color_weights)

            packed = (
                colors[:, 0].astype(np.uint32) << 16
                | colors[:, 1].astype(np.uint32) << 8
                | colors[:, 2].astype(np.uint32)
            )
            unique, inverse = np.unique(packed, return_inverse=True)
            candidates = np.stack(((unique >> 16) & 255, (unique >> 8) & 255, unique & 255), axis=-1)
            candidate_lab = _rgb_to_oklab(candidates)
            coverage = np.bincount(inverse, weights=color_weights, minlength=len(unique))
            coverage /= max(float(coverage.sum()), 1e-12)

            structure = analysis.structure[region][valid]
            texture = analysis.texture[region][valid]
            dither = analysis.dither[region][valid]
            structure_support = np.bincount(
                inverse, weights=color_weights * structure, minlength=len(unique)
            ) / max(float(color_weights.sum()), 1e-12)
            cell_structure = float(np.average(structure, weights=color_weights))
            cell_texture = float(np.average(texture, weights=color_weights))
            cell_dither = float(np.average(dither, weights=color_weights))

            sx = min(source_w - 1, int((tx + 0.5) * source_w / target_w))
            sy = min(source_h - 1, int((ty + 0.5) * source_h / target_h))
            anchor = rgba[sy, sx, :3]
            anchor_lab = _rgb_to_oklab(anchor)
            desired = (1.0 - options.surface_phase_weight) * desired + options.surface_phase_weight * anchor_lab

            difference = candidate_lab - desired
            score = np.sqrt(
                1.35 * difference[:, 0] ** 2 + difference[:, 1] ** 2 + difference[:, 2] ** 2
            )
            score -= options.surface_coverage_weight * coverage
            anchor_code = (int(anchor[0]) << 16) | (int(anchor[1]) << 8) | int(anchor[2])
            score -= options.surface_anchor_weight * (unique == anchor_code)

            coherent = cell_structure * (1.0 - options.surface_dither_suppression * cell_dither)
            score -= options.surface_structure_weight * coherent * structure_support

            median_lightness = float(np.median(labs[:, 0]))
            darkness = np.clip(median_lightness - candidate_lab[:, 0], 0.0, None)
            score += (
                options.surface_dark_noise_penalty
                * cell_texture
                * (1.0 - cell_structure)
                * (1.0 - coverage)
                * darkness
            )

            chosen = candidates[int(np.argmin(score))].astype(np.uint8)
            output[ty, tx, :3] = chosen
            alpha_coverage = float((weights * alpha_region).sum() / max(weights.sum(), 1e-12))
            output[ty, tx, 3] = (
                255
                if binary_alpha and alpha_coverage >= 0.5
                else int(np.clip(round(alpha_coverage * 255), 0, 255))
            )

    return Image.fromarray(output, mode="RGBA")


def _infer_content_hint(image: ImageInput) -> ContentHint:
    if not isinstance(image, (str, Path)):
        return ContentHint.AUTO
    normalized = str(image).replace("\\", "/").lower()
    if "/textures/item/" in normalized:
        return ContentHint.ITEM
    if "/textures/block/" in normalized:
        return ContentHint.BLOCK
    if "/textures/entity/" in normalized:
        return ContentHint.ENTITY
    return ContentHint.AUTO


def downscale_semantic(
    image: ImageInput,
    size: tuple[int, int],
    *,
    options: SemanticOptions | None = None,
) -> Image.Image:
    options = options or SemanticOptions()
    if options.content_hint == ContentHint.AUTO:
        hint = _infer_content_hint(image)
        if hint != ContentHint.AUTO:
            options = replace(options, content_hint=hint)

    source = _open_rgba(image)
    target = (int(size[0]), int(size[1]))
    if min(target) <= 0 or target[0] > source.width or target[1] > source.height:
        raise ValueError(f"invalid downscale target {target!r} for source {source.size!r}")
    analysis = analyze(source, options=options)
    if analysis.mode == SemanticMode.PATTERN:
        return source.resize(target, resample=Image.Resampling.NEAREST)
    if analysis.mode == SemanticMode.SPRITE:
        return _sprite_downscale(source, target, options)
    return _surface_downscale(analysis, target, options)


def downscale_semantic_by_factor(
    image: ImageInput,
    factor: float = 2.0,
    *,
    options: SemanticOptions | None = None,
) -> Image.Image:
    if factor < 1.0:
        raise ValueError("factor must be at least 1")
    source = _open_rgba(image)
    size = (max(1, int(np.floor(source.width / factor))), max(1, int(np.floor(source.height / factor))))
    return downscale_semantic(source, size, options=options)
