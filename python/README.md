# BetterPixelArtDownscale — Python

This directory contains the reference Python implementation and the historical compatibility modules.

The public package name remains `better_pixel_art_downscale`, and installation still happens from the repository root:

```bash
python -m pip install -e .
```

```python
from better_pixel_art_downscale import DownscaleOptions, downscale

result = downscale("character.png", (8, 8))
result.save("character_8.png")
```

The Python implementation depends on NumPy and Pillow. The JavaScript port lives independently in `../javascript/` and has no external runtime dependencies.
