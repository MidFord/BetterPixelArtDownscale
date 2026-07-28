from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, TypeAlias

import numpy as np
from PIL import Image

from .options import DownscaleOptions

ImageInput: TypeAlias = Image.Image | str | Path | BinaryIO


@dataclass(slots=True)
class _PreparedSource:
    rgba: np.ndarray
    codes: np.ndarray
    alpha: np.ndarray
    opaque: np.ndarray
    outline: np.ndarray
    internal_edge: np.ndarray
    binary_alpha: bool


@dataclass(slots=True)
class _Cell:
    x_indices: np.ndarray
    y_indices: np.ndarray
    weights: np.ndarray
    area: float


def _open_rgba(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGBA")
    with Image.open(image) as opened:
        return opened.convert("RGBA")


def _validate_target_size(source_size: tuple[int, int], size: tuple[int, int]) -> tuple[int, int]:
    if len(size) != 2:
        raise ValueError("size must be a (width, height) pair")
    width, height = (int(size[0]), int(size[1]))
    if width <= 0 or height <= 0:
        raise ValueError(f"target dimensions must be positive, got {size!r}")
    source_width, source_height = source_size
    if width > source_width or height > source_height:
        raise ValueError(
            "BetterPixelArtDownscale only downsizes images; "
            f"source is {source_width}x{source_height}, target is {width}x{height}"
        )
    return width, height


def _pack_rgba(rgba: np.ndarray) -> np.ndarray:
    data = rgba.astype(np.uint32, copy=False)
    return (
        (data[..., 0] << 24)
        | (data[..., 1] << 16)
        | (data[..., 2] << 8)
        | data[..., 3]
    )


def _unpack_rgba(code: int) -> tuple[int, int, int, int]:
    return (
        (code >> 24) & 0xFF,
        (code >> 16) & 0xFF,
        (code >> 8) & 0xFF,
        code & 0xFF,
    )


def _shift_with_false(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    shifted = np.zeros_like(mask, dtype=bool)
    y_src_start = max(0, -dy)
    y_src_end = mask.shape[0] - max(0, dy)
    x_src_start = max(0, -dx)
    x_src_end = mask.shape[1] - max(0, dx)
    y_dst_start = max(0, dy)
    y_dst_end = mask.shape[0] - max(0, -dy)
    x_dst_start = max(0, dx)
    x_dst_end = mask.shape[1] - max(0, -dx)
    shifted[y_dst_start:y_dst_end, x_dst_start:x_dst_end] = mask[
        y_src_start:y_src_end, x_src_start:x_src_end
    ]
    return shifted


def _shift_rgb(rgb: np.ndarray, dy: int, dx: int) -> np.ndarray:
    shifted = np.zeros_like(rgb)
    y_src_start = max(0, -dy)
    y_src_end = rgb.shape[0] - max(0, dy)
    x_src_start = max(0, -dx)
    x_src_end = rgb.shape[1] - max(0, dx)
    y_dst_start = max(0, dy)
    y_dst_end = rgb.shape[0] - max(0, -dy)
    x_dst_start = max(0, dx)
    x_dst_end = rgb.shape[1] - max(0, -dx)
    shifted[y_dst_start:y_dst_end, x_dst_start:x_dst_end] = rgb[
        y_src_start:y_src_end, x_src_start:x_src_end
    ]
    return shifted


def _prepare_source(image: Image.Image, options: DownscaleOptions) -> _PreparedSource:
    rgba = np.asarray(image, dtype=np.uint8)
    alpha = rgba[..., 3].astype(np.float32) / 255.0
    opaque = alpha >= options.source_alpha_threshold

    neighbors = [
        _shift_with_false(opaque, -1, 0),
        _shift_with_false(opaque, 1, 0),
        _shift_with_false(opaque, 0, -1),
        _shift_with_false(opaque, 0, 1),
    ]
    if np.any(~opaque):
        outline = opaque & ~(neighbors[0] & neighbors[1] & neighbors[2] & neighbors[3])
    else:
        outline = np.zeros_like(opaque, dtype=bool)

    rgb = rgba[..., :3].astype(np.float32) / 255.0
    # Weighted RGB distance. It is intentionally inexpensive and stable for the
    # small, discrete palettes common in pixel art.
    internal_edge = np.zeros(alpha.shape, dtype=np.float32)
    for dy, dx, neighbor_opaque in (
        (-1, 0, neighbors[0]),
        (1, 0, neighbors[1]),
        (0, -1, neighbors[2]),
        (0, 1, neighbors[3]),
    ):
        neighbor_rgb = _shift_rgb(rgb, dy, dx)
        delta = rgb - neighbor_rgb
        distance = np.sqrt(
            0.30 * delta[..., 0] ** 2
            + 0.59 * delta[..., 1] ** 2
            + 0.11 * delta[..., 2] ** 2
        )
        valid = opaque & neighbor_opaque
        internal_edge = np.maximum(internal_edge, np.where(valid, distance, 0.0))

    internal_edge = np.where(
        internal_edge >= options.internal_edge_threshold, internal_edge, 0.0
    ).astype(np.float32, copy=False)

    alpha_bytes = rgba[..., 3]
    binary_alpha = bool(np.all((alpha_bytes == 0) | (alpha_bytes == 255)))

    return _PreparedSource(
        rgba=rgba,
        codes=_pack_rgba(rgba),
        alpha=alpha,
        opaque=opaque,
        outline=outline,
        internal_edge=internal_edge,
        binary_alpha=binary_alpha,
    )


def _axis_cells(source_length: int, target_length: int) -> list[tuple[np.ndarray, np.ndarray]]:
    cells: list[tuple[np.ndarray, np.ndarray]] = []
    scale = source_length / target_length
    for target_index in range(target_length):
        start = target_index * scale
        end = (target_index + 1) * scale
        first = int(np.floor(start))
        last = int(np.ceil(end))
        indices = np.arange(first, last, dtype=np.intp)
        left = np.maximum(indices.astype(np.float64), start)
        right = np.minimum(indices.astype(np.float64) + 1.0, end)
        weights = np.maximum(0.0, right - left).astype(np.float32)
        cells.append((indices, weights))
    return cells


def _make_cell(
    x_data: tuple[np.ndarray, np.ndarray], y_data: tuple[np.ndarray, np.ndarray]
) -> _Cell:
    x_indices, x_weights = x_data
    y_indices, y_weights = y_data
    weights = np.multiply.outer(y_weights, x_weights).astype(np.float32, copy=False)
    return _Cell(
        x_indices=x_indices,
        y_indices=y_indices,
        weights=weights,
        area=float(weights.sum()),
    )


def _center_sample(
    source: _PreparedSource,
    target_x: int,
    target_y: int,
    target_width: int,
    target_height: int,
) -> bool:
    source_height, source_width = source.alpha.shape
    x = min(source_width - 1, int((target_x + 0.5) * source_width / target_width))
    y = min(source_height - 1, int((target_y + 0.5) * source_height / target_height))
    return bool(source.opaque[y, x])


def _destination_boundary(occupancy: np.ndarray) -> np.ndarray:
    up = _shift_with_false(occupancy, -1, 0)
    down = _shift_with_false(occupancy, 1, 0)
    left = _shift_with_false(occupancy, 0, -1)
    right = _shift_with_false(occupancy, 0, 1)
    return occupancy & ~(up & down & left & right)


def _group_scores(
    codes: np.ndarray,
    weights: np.ndarray,
    outline: np.ndarray,
    internal_edge: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    unique_codes, inverse = np.unique(codes, return_inverse=True)
    coverage = np.bincount(inverse, weights=weights, minlength=len(unique_codes))
    outline_support = np.bincount(
        inverse, weights=weights * outline.astype(np.float32), minlength=len(unique_codes)
    )
    edge_support = np.bincount(
        inverse, weights=weights * internal_edge, minlength=len(unique_codes)
    )
    return unique_codes, coverage, outline_support, edge_support


def _choose_color(
    source: _PreparedSource,
    cell: _Cell,
    is_boundary: bool,
    options: DownscaleOptions,
) -> tuple[int, int, int, int]:
    y_slice = np.ix_(cell.y_indices, cell.x_indices)
    alpha = source.alpha[y_slice]
    effective_weight = cell.weights * alpha
    valid = effective_weight > 0.0
    if not np.any(valid):
        return 0, 0, 0, 0

    codes = source.codes[y_slice][valid]
    weights = effective_weight[valid].astype(np.float64, copy=False)
    outline = source.outline[y_slice][valid]
    internal_edge = source.internal_edge[y_slice][valid]
    unique_codes, coverage, outline_support, edge_support = _group_scores(
        codes, weights, outline, internal_edge
    )

    candidate_mask = np.ones(len(unique_codes), dtype=bool)
    if is_boundary and options.preserve_outline:
        outline_total = float(outline_support.sum())
        if outline_total / max(cell.area, 1e-12) >= options.outline_min_coverage:
            candidate_mask = outline_support > 0.0

    score = coverage.copy()
    if options.preserve_internal_edges:
        score += options.internal_edge_weight * edge_support
    if is_boundary and options.preserve_outline:
        score += outline_support

    score = np.where(candidate_mask, score, -np.inf)
    best_score = np.max(score)
    contenders = np.flatnonzero(np.isclose(score, best_score, rtol=1e-10, atol=1e-12))
    if len(contenders) > 1:
        # Stable tie-breakers: more coverage, more edge support, then darker on
        # silhouette boundaries. The final numeric code makes the result fully
        # deterministic across Python and NumPy versions.
        def key(index: int) -> tuple[float, float, float, int]:
            r, g, b, _ = _unpack_rgba(int(unique_codes[index]))
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            darkness = -luminance if is_boundary else luminance
            return (
                float(coverage[index]),
                float(outline_support[index] + edge_support[index]),
                float(darkness),
                -int(unique_codes[index]),
            )

        best_index = max((int(index) for index in contenders), key=key)
    else:
        best_index = int(contenders[0])
    return _unpack_rgba(int(unique_codes[best_index]))


def _build_maps(
    source: _PreparedSource,
    target_size: tuple[int, int],
    options: DownscaleOptions,
) -> tuple[list[list[_Cell]], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    target_width, target_height = target_size
    source_height, source_width = source.alpha.shape
    x_cells = _axis_cells(source_width, target_width)
    y_cells = _axis_cells(source_height, target_height)
    cells: list[list[_Cell]] = []
    alpha_coverage = np.zeros((target_height, target_width), dtype=np.float32)
    internal_support = np.zeros_like(alpha_coverage)

    for target_y, y_data in enumerate(y_cells):
        row: list[_Cell] = []
        for target_x, x_data in enumerate(x_cells):
            cell = _make_cell(x_data, y_data)
            row.append(cell)
            region = np.ix_(cell.y_indices, cell.x_indices)
            alpha_coverage[target_y, target_x] = float(
                np.sum(cell.weights * source.alpha[region]) / max(cell.area, 1e-12)
            )
            internal_support[target_y, target_x] = float(
                np.sum(cell.weights * source.internal_edge[region]) / max(cell.area, 1e-12)
            )
        cells.append(row)

    occupancy = alpha_coverage >= options.alpha_threshold
    if options.preserve_thin_features:
        for target_y in range(target_height):
            for target_x in range(target_width):
                if occupancy[target_y, target_x]:
                    continue
                if alpha_coverage[target_y, target_x] < options.thin_feature_threshold:
                    continue
                occupancy[target_y, target_x] = _center_sample(
                    source,
                    target_x,
                    target_y,
                    target_width,
                    target_height,
                )

    boundary = _destination_boundary(occupancy)
    return cells, alpha_coverage, occupancy, boundary, internal_support


def downscale(
    image: ImageInput,
    size: tuple[int, int],
    *,
    options: DownscaleOptions | None = None,
) -> Image.Image:
    """Downscale pixel art while preserving silhouette-aligned edges.

    Unlike a two-pass "resize then overlay edges" pipeline, this function uses a
    single exact destination grid for alpha coverage, outline classification, and
    color selection. Consequently, an outline cannot be shifted or enlarged by a
    separately rounded coordinate transform.
    """

    options = options or DownscaleOptions()
    options.validate()
    source_image = _open_rgba(image)
    target_size = _validate_target_size(source_image.size, size)
    if target_size == source_image.size:
        return source_image.copy()

    source = _prepare_source(source_image, options)
    cells, alpha_coverage, occupancy, boundary, _ = _build_maps(
        source, target_size, options
    )
    target_width, target_height = target_size
    output = np.zeros((target_height, target_width, 4), dtype=np.uint8)
    use_binary_alpha = source.binary_alpha if options.binary_alpha is None else options.binary_alpha

    for target_y in range(target_height):
        for target_x in range(target_width):
            if not occupancy[target_y, target_x]:
                continue
            color = _choose_color(
                source,
                cells[target_y][target_x],
                bool(boundary[target_y, target_x]),
                options,
            )
            output[target_y, target_x, :3] = color[:3]
            if use_binary_alpha:
                output[target_y, target_x, 3] = 255
            else:
                output[target_y, target_x, 3] = np.uint8(
                    np.clip(round(float(alpha_coverage[target_y, target_x]) * 255.0), 1, 255)
                )

    return Image.fromarray(output, mode="RGBA")


def edge_layer(
    image: ImageInput,
    size: tuple[int, int],
    *,
    options: DownscaleOptions | None = None,
    include_outline: bool = True,
    include_internal_edges: bool = True,
) -> Image.Image:
    """Return an edge-only layer aligned to the same grid used by :func:`downscale`."""

    options = options or DownscaleOptions()
    options.validate()
    source_image = _open_rgba(image)
    target_size = _validate_target_size(source_image.size, size)
    source = _prepare_source(source_image, options)
    cells, _alpha_coverage, occupancy, boundary, internal_support = _build_maps(
        source, target_size, options
    )
    target_width, target_height = target_size
    output = np.zeros((target_height, target_width, 4), dtype=np.uint8)

    for target_y in range(target_height):
        for target_x in range(target_width):
            if not occupancy[target_y, target_x]:
                continue
            is_outline = include_outline and bool(boundary[target_y, target_x])
            is_internal = (
                include_internal_edges
                and internal_support[target_y, target_x] >= options.internal_edge_threshold
            )
            if not (is_outline or is_internal):
                continue
            color = _choose_color(source, cells[target_y][target_x], is_outline, options)
            output[target_y, target_x] = (*color[:3], 255)

    return Image.fromarray(output, mode="RGBA")


def downscale_by_factor(
    image: ImageInput,
    factor_x: float,
    factor_y: float | None = None,
    *,
    options: DownscaleOptions | None = None,
) -> Image.Image:
    """Downscale using divisors, preserving the legacy repository convention."""

    if factor_y is None:
        factor_y = factor_x
    if factor_x < 1.0 or factor_y < 1.0:
        raise ValueError("downscale factors must be at least 1.0")
    source_image = _open_rgba(image)
    width = max(1, int(np.floor(source_image.width / factor_x)))
    height = max(1, int(np.floor(source_image.height / factor_y)))
    return downscale(source_image, (width, height), options=options)


def downscale_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    size: tuple[int, int] | None = None,
    factor: float | tuple[float, float] | None = None,
    options: DownscaleOptions | None = None,
) -> Image.Image:
    """Downscale a file, save it, and return the resulting image."""

    if (size is None) == (factor is None):
        raise ValueError("provide exactly one of size or factor")
    if size is not None:
        result = downscale(input_path, size, options=options)
    else:
        if isinstance(factor, tuple):
            result = downscale_by_factor(
                input_path, factor[0], factor[1], options=options
            )
        else:
            result = downscale_by_factor(input_path, float(factor), options=options)
    result.save(output_path)
    return result
