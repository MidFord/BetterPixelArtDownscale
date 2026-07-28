# BetterPixelArtDownscale

A deterministic, edge-aware Python downscaler for pixel art. It preserves sharp palettes, thin features, internal color boundaries, transparent backgrounds, and—most importantly—the alignment between an object's silhouette and its outline.

## Why v2 was rebuilt

The original `image_resize_edge` pipeline produced the resized content and the edge layer independently:

1. content pixels were selected with a distributed sampling pattern;
2. edges were detected at source resolution;
3. edge coordinates were divided and floored into a second target image;
4. the two results were overlaid.

Those paths did not share the same sample positions or rounding rules. At non-trivial scales, an edge could therefore land in a different destination cell than the content it belonged to, making outlines appear shifted, thicker, or a different size.

Version 2 uses **one exact destination grid**. Each output cell measures source-pixel area overlap, decides alpha occupancy once, classifies destination boundaries from that occupancy, and selects outline or interior colors only inside the established silhouette. There is no independently resized edge overlay to drift.

## Installation

```bash
python -m pip install -e .
```

Runtime dependencies are only NumPy and Pillow. OpenCV is no longer required.

## Python API

```python
from better_pixel_art_downscale import downscale

result = downscale("character.png", (32, 32))
result.save("character_32.png")
```

Using divisors:

```python
from better_pixel_art_downscale import downscale_by_factor

result = downscale_by_factor("character.png", 2)
result.save("character_half.png")
```

Advanced control:

```python
from better_pixel_art_downscale import DownscaleOptions, downscale

options = DownscaleOptions(
    alpha_threshold=0.5,
    preserve_thin_features=True,
    preserve_outline=True,
    preserve_internal_edges=True,
)

result = downscale("character.png", (24, 24), options=options)
```

## Command line

```bash
better-pixel-art-downscale input.png output.png --size 32x32
better-pixel-art-downscale input.png output.png --factor 2
```

Useful switches:

```text
--alpha-threshold 0.5
--no-outline
--no-internal-edges
--no-thin-features
```

## Compatibility

The historical modules remain importable:

```python
import image_resize_edge

result = image_resize_edge.processImage("character.png", 2, 2)
```

The misspelled legacy argument `iclude_outline` is still accepted, and `include_outline` is accepted as a corrected alias. The old experimental filter parameters remain accepted for call compatibility, but v2 does not use them.

## Algorithm guarantees

- **No edge/content coordinate split:** silhouette and edge decisions use identical cell boundaries.
- **No transparent RGB bleeding:** colors are weighted by alpha before selection.
- **Deterministic output:** no random edge colors or traversal-order behavior.
- **Palette-friendly:** output colors are selected from real source colors rather than invented by interpolation.
- **Non-integer scale support:** source coverage is computed from exact fractional overlap.
- **Conservative outlines:** outline colors can occupy boundary cells, but cannot create pixels outside the destination silhouette.

## Development

```bash
python -m pip install -e .[dev]
pytest
ruff check .
python -m benchmarks.benchmark
```

The test suite includes regression coverage for outline expansion, non-integer alignment, transparent RGB contamination, deterministic output, alpha handling, and the legacy API.
