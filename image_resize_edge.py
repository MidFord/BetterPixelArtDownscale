"""Backward-compatible entry point for BetterPixelArtDownscale 1.x.

New code should import from ``better_pixel_art_downscale``.
"""

from __future__ import annotations

from better_pixel_art_downscale import DownscaleOptions, downscale_by_factor, edge_layer
from better_pixel_art_downscale.core import _open_rgba


def processImage(
    image_path,
    factor_x,
    factor_y,
    iclude_outline=True,
    include_edges=True,
    only_edges=False,
    outline_threshold=1.32,
    center_threshold=0.0,
    sharp_radius=1,
    sharp_percent=1,
    color_simplifier=2,
    color_diff_threshold=10,
    color_light_threshold=10,
    **kwargs,
):
    """Legacy wrapper around the new single-grid edge-aware algorithm.

    The historical misspelling ``iclude_outline`` remains supported. The old
    filter-tuning arguments are accepted for source compatibility but are no
    longer used by the deterministic v2 algorithm.
    """

    if "include_outline" in kwargs:
        iclude_outline = kwargs.pop("include_outline")
    if kwargs:
        unknown = ", ".join(sorted(kwargs))
        raise TypeError(f"unexpected keyword argument(s): {unknown}")

    options = DownscaleOptions(
        preserve_outline=bool(iclude_outline),
        preserve_internal_edges=bool(include_edges),
    )
    if factor_x < 1 or factor_y < 1:
        raise ValueError("downscale factors must be at least 1.0")
    if only_edges:
        source = _open_rgba(image_path)
        width = max(1, int(source.width // factor_x))
        height = max(1, int(source.height // factor_y))
        return edge_layer(
            source,
            (width, height),
            options=options,
            include_outline=bool(iclude_outline),
            include_internal_edges=bool(include_edges),
        )
    return downscale_by_factor(image_path, factor_x, factor_y, options=options)
