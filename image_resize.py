"""Backward-compatible basic downscale helpers."""

from __future__ import annotations

import numpy as np
from PIL import Image

from better_pixel_art_downscale import DownscaleOptions, downscale_by_factor


def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)


def convert_image(image: Image.Image) -> Image.Image:
    return image.copy()


def convert_image_size(image: Image.Image, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return image.crop((0, 0, min(width, image.width), min(height, image.height)))


def simplify(value, times):
    if times <= 0:
        raise ValueError("times must be positive")
    return round(value * times) / times


def SimplifyColors(image: Image.Image, simplifier=8) -> Image.Image:
    if simplifier <= 0:
        raise ValueError("simplifier must be positive")
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    levels = float(simplifier)
    rgba[..., :3] = np.clip(
        np.rint(np.rint((rgba[..., :3] / 255.0) * levels) / levels * 255.0),
        0,
        255,
    ).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def processImage(
    pathto,
    scaleMultiplierX,
    scaleMultiplierY,
    simplify=False,
    simplifyPixel=8,
):
    options = DownscaleOptions(
        preserve_outline=False,
        preserve_internal_edges=False,
    )
    result = downscale_by_factor(
        pathto,
        scaleMultiplierX,
        scaleMultiplierY,
        options=options,
    )
    return SimplifyColors(result, simplifyPixel) if simplify else result
