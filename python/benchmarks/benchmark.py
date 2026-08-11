from __future__ import annotations

import time

import numpy as np
from PIL import Image

from better_pixel_art_downscale import downscale


def main() -> None:
    rng = np.random.default_rng(7)
    rgba = rng.integers(0, 256, size=(512, 512, 4), dtype=np.uint8)
    rgba[..., 3] = np.where(rgba[..., 3] > 96, 255, 0)
    image = Image.fromarray(rgba, mode="RGBA")
    start = time.perf_counter()
    result = downscale(image, (128, 128))
    elapsed = time.perf_counter() - start
    print(f"512x512 -> {result.width}x{result.height}: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
