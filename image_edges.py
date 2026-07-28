"""Backward-compatible edge extraction helpers.

The original experimental implementation traced and resized edge coordinates in a
separate pass. That design caused the issue fixed in v2. These wrappers now use the
same destination grid as the final downscale operation.
"""

from __future__ import annotations

from PIL import Image

from better_pixel_art_downscale import DownscaleOptions, edge_layer
from better_pixel_art_downscale.core import _open_rgba


def CombineImageInCaps(image: Image.Image, image2: Image.Image) -> Image.Image:
    if image.size != image2.size:
        raise ValueError("images must have the same size")
    foreground = image.convert("RGBA")
    background = image2.convert("RGBA")
    return Image.alpha_composite(background, foreground)


def processImage(
    path,
    factor_x,
    factor_y,
    include_outline=True,
    include_edges=True,
    only_edges=False,
    outline_threshold=1.32,
    center_threshold=0.0,
    sharp_radius=1,
    sharp_percent=1,
    color_simplifier=2,
    color_diff_threshold=10,
    color_light_threshold=10,
):
    if factor_x < 1 or factor_y < 1:
        raise ValueError("downscale factors must be at least 1.0")
    source = _open_rgba(path)
    width = max(1, int(source.width // factor_x))
    height = max(1, int(source.height // factor_y))
    options = DownscaleOptions(
        preserve_outline=bool(include_outline),
        preserve_internal_edges=bool(include_edges),
    )
    return edge_layer(
        source,
        (width, height),
        options=options,
        include_outline=bool(include_outline),
        include_internal_edges=bool(include_edges),
    )
