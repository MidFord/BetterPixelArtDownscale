"""Topology-aware cutout extension for the semantic pixel-art downscaler.

Semantic v2 separated sprite silhouettes from opaque surface reconstruction, but
routed every transparent block through one fixed nearest-neighbor phase.  That
works surprisingly well for many Minecraft cutouts, yet it conflates several
very different authored topologies: spanning lattices, freestanding thin
features, dense masks, and soft-alpha overlays.

This module keeps the mature v2 sprite and surface solvers unchanged and adds a
source-only cutout policy router.  No texture names or reference-pack data are
used at inference time.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math
from pathlib import Path

import numpy as np
from PIL import Image

from .semantic import (
    ContentHint,
    ImageInput,
    SemanticMode,
    SemanticOptions,
    _infer_content_hint,
    _open_rgba,
    _sprite_downscale,
    _surface_downscale,
    analyze,
)


class CutoutPolicy(str, Enum):
    """Source-only policy selected for a transparent texture."""

    STABLE_PHASE = "stable_phase"
    BBOX_PHASE_RESCUE = "bbox_phase_rescue"
    SPANNING_COVERAGE = "spanning_coverage"
    DENSE_COVERAGE = "dense_coverage"
    SPRITE_TOPOLOGY = "sprite_topology"


@dataclass(frozen=True, slots=True)
class CutoutAnalysis:
    visible_ratio: float
    ghost_alpha_ratio: float
    bbox_fill_ratio: float
    bbox_area_ratio: float
    bbox_min_x: int
    bbox_min_y: int
    edge_touch_count: int
    alpha_transition: float
    alpha_recurrence: float
    policy: CutoutPolicy


def _bbox_stats(visible: np.ndarray) -> tuple[float, float, int, int, int]:
    height, width = visible.shape
    ys, xs = np.nonzero(visible)
    if not len(xs):
        return 0.0, 0.0, 0, 0, 0

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    bbox_area = max(1, (x1 - x0) * (y1 - y0))
    fill = float(visible[y0:y1, x0:x1].mean())
    touches = sum(
        (
            bool(visible[0].any()),
            bool(visible[-1].any()),
            bool(visible[:, 0].any()),
            bool(visible[:, -1].any()),
        )
    )
    return fill, bbox_area / float(width * height), int(touches), x0, y0


def _alpha_pattern_stats(visible: np.ndarray) -> tuple[float, float]:
    """Return alpha-boundary density and two-pixel recurrence.

    A high transition density indicates a fragmented/dense cutout.  Recurrence
    is retained as a diagnostic because repeated two-pixel structure is a useful
    signature for authored lattices and dither-like masks, even though v3 does
    not yet branch directly on it.
    """

    horizontal = float(np.mean(visible != np.roll(visible, 1, axis=1)))
    vertical = float(np.mean(visible != np.roll(visible, 1, axis=0)))
    transition = 0.5 * (horizontal + vertical)
    recurrence = 0.5 * (
        float(np.mean(visible == np.roll(visible, 2, axis=1)))
        + float(np.mean(visible == np.roll(visible, 2, axis=0)))
    )
    return transition, recurrence


def _phase_downscale_2x(
    image: Image.Image,
    size: tuple[int, int],
    phase_x: int,
    phase_y: int,
) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    target_width, target_height = size
    if rgba.shape[1] != target_width * 2 or rgba.shape[0] != target_height * 2:
        return image.resize(size, resample=Image.Resampling.NEAREST)

    output = rgba[
        phase_y : phase_y + target_height * 2 : 2,
        phase_x : phase_x + target_width * 2 : 2,
    ].copy()
    return Image.fromarray(output, mode="RGBA")


def _axis_cells(source_length: int, target_length: int) -> list[tuple[np.ndarray, np.ndarray]]:
    scale = source_length / target_length
    cells: list[tuple[np.ndarray, np.ndarray]] = []
    for index in range(target_length):
        start = index * scale
        end = (index + 1) * scale
        indices = np.arange(int(np.floor(start)), int(np.ceil(end)), dtype=np.intp)
        overlaps = np.maximum(
            0.0,
            np.minimum(indices.astype(np.float64) + 1.0, end)
            - np.maximum(indices.astype(np.float64), start),
        )
        cells.append((indices, overlaps))
    return cells


def _coverage_downscale(
    image: Image.Image,
    size: tuple[int, int],
    *,
    occupancy_threshold: float,
) -> Image.Image:
    """Reduce a binary cutout by area while retaining source-palette colors.

    The stable center sample supplies the RGB whenever it is visible.  If that
    sample is transparent but the cell must survive, the most frequent visible
    source RGB is selected.  This changes topology without introducing blended
    colors.
    """

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    source_height, source_width = rgba.shape[:2]
    target_width, target_height = size
    x_cells = _axis_cells(source_width, target_width)
    y_cells = _axis_cells(source_height, target_height)
    output = np.zeros((target_height, target_width, 4), dtype=np.uint8)

    for target_y, (y_indices, y_weights) in enumerate(y_cells):
        for target_x, (x_indices, x_weights) in enumerate(x_cells):
            weights = np.multiply.outer(y_weights, x_weights)
            region = rgba[np.ix_(y_indices, x_indices)]
            alpha = region[..., 3].astype(np.float64) / 255.0
            coverage = float((weights * alpha).sum() / max(float(weights.sum()), 1e-12))
            if coverage < occupancy_threshold:
                continue

            visible = alpha > 0.0
            if not np.any(visible):
                continue

            source_x = min(
                source_width - 1,
                int((target_x + 0.5) * source_width / target_width),
            )
            source_y = min(
                source_height - 1,
                int((target_y + 0.5) * source_height / target_height),
            )

            if rgba[source_y, source_x, 3] > 0:
                chosen = rgba[source_y, source_x, :3]
            else:
                colors = region[..., :3][visible]
                packed = (
                    colors[:, 0].astype(np.uint32) << 16
                    | colors[:, 1].astype(np.uint32) << 8
                    | colors[:, 2].astype(np.uint32)
                )
                unique, counts = np.unique(packed, return_counts=True)
                code = int(unique[int(np.argmax(counts))])
                chosen = np.array(
                    ((code >> 16) & 255, (code >> 8) & 255, code & 255),
                    dtype=np.uint8,
                )

            output[target_y, target_x, :3] = chosen
            output[target_y, target_x, 3] = 255

    return Image.fromarray(output, mode="RGBA")


def analyze_cutout(
    image: ImageInput,
    size: tuple[int, int],
) -> CutoutAnalysis:
    """Classify a cutout using only source alpha topology.

    The thresholds are intentionally coarse.  They describe geometry rather
    than Minecraft texture names and were selected through ablation on the 2x
    benchmark, then kept as simple regimes rather than a learned classifier.
    """

    source = _open_rgba(image)
    rgba = np.asarray(source, dtype=np.uint8)
    alpha = rgba[..., 3].astype(np.float64) / 255.0
    visible = alpha > 0.0
    visible_ratio = float(visible.mean())
    ghost_alpha_ratio = float(np.mean((alpha > 0.0) & (alpha <= (4.0 / 255.0))))
    fill, area, touches, x0, y0 = _bbox_stats(visible)
    transition, recurrence = _alpha_pattern_stats(visible)

    exact_2x = source.width == int(size[0]) * 2 and source.height == int(size[1]) * 2

    if ghost_alpha_ratio > 0.02:
        policy = CutoutPolicy.STABLE_PHASE
    elif area <= 0.16:
        stable = source.resize(size, resample=Image.Resampling.NEAREST)
        stable_visible = bool(np.any(np.asarray(stable, dtype=np.uint8)[..., 3] > 0))
        if touches >= 2:
            policy = CutoutPolicy.SPANNING_COVERAGE
        elif stable_visible or not exact_2x:
            policy = CutoutPolicy.STABLE_PHASE
        else:
            policy = CutoutPolicy.BBOX_PHASE_RESCUE
    elif transition <= 0.30:
        policy = CutoutPolicy.STABLE_PHASE
    elif visible_ratio <= 0.55:
        if area >= 0.95 and transition <= 0.41:
            policy = CutoutPolicy.STABLE_PHASE
        else:
            policy = CutoutPolicy.DENSE_COVERAGE
    else:
        policy = CutoutPolicy.SPRITE_TOPOLOGY

    return CutoutAnalysis(
        visible_ratio=visible_ratio,
        ghost_alpha_ratio=ghost_alpha_ratio,
        bbox_fill_ratio=fill,
        bbox_area_ratio=area,
        bbox_min_x=x0,
        bbox_min_y=y0,
        edge_touch_count=touches,
        alpha_transition=transition,
        alpha_recurrence=recurrence,
        policy=policy,
    )


def downscale_cutout(
    image: ImageInput,
    size: tuple[int, int],
    *,
    options: SemanticOptions | None = None,
) -> Image.Image:
    options = options or SemanticOptions(content_hint=ContentHint.BLOCK)
    source = _open_rgba(image)
    target = (int(size[0]), int(size[1]))
    if min(target) <= 0 or target[0] > source.width or target[1] > source.height:
        raise ValueError(f"invalid downscale target {target!r} for source {source.size!r}")

    cutout = analyze_cutout(source, target)
    if cutout.policy == CutoutPolicy.STABLE_PHASE:
        return source.resize(target, resample=Image.Resampling.NEAREST)
    if cutout.policy == CutoutPolicy.SPANNING_COVERAGE:
        return _coverage_downscale(source, target, occupancy_threshold=0.25)
    if cutout.policy == CutoutPolicy.DENSE_COVERAGE:
        return _coverage_downscale(source, target, occupancy_threshold=0.50)
    if cutout.policy == CutoutPolicy.SPRITE_TOPOLOGY:
        return _sprite_downscale(source, target, options)

    return _phase_downscale_2x(
        source,
        target,
        cutout.bbox_min_x & 1,
        cutout.bbox_min_y & 1,
    )


def downscale_semantic_v3(
    image: ImageInput,
    size: tuple[int, int],
    *,
    options: SemanticOptions | None = None,
) -> Image.Image:
    """Run semantic v2 shape/surface reasoning plus topology-aware cutouts."""

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
        return downscale_cutout(source, target, options=options)
    if analysis.mode == SemanticMode.SPRITE:
        return _sprite_downscale(source, target, options)
    return _surface_downscale(analysis, target, options)


def downscale_semantic_v3_by_factor(
    image: ImageInput,
    factor: float = 2.0,
    *,
    options: SemanticOptions | None = None,
) -> Image.Image:
    if not math.isfinite(factor) or factor < 1.0:
        raise ValueError("factor must be a finite value of at least 1")
    source = _open_rgba(image)
    size = (
        max(1, int(np.floor(source.width / factor))),
        max(1, int(np.floor(source.height / factor))),
    )
    return downscale_semantic_v3(source, size, options=options)
