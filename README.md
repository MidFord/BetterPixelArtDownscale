# BetterPixelArtDownscale

A deterministic, silhouette-first pixel-art downscaler with matching **Python** and **JavaScript** implementations.

Instead of resizing content and edges through separate coordinate paths, BetterPixelArtDownscale builds one exact destination grid. Every output cell measures source-pixel area overlap, establishes alpha occupancy once, derives its destination boundary from that occupancy, and only then selects a source-palette color. Outlines therefore cannot drift away from or enlarge the silhouette they belong to.

## Repository layout

```text
python/      Reference Python implementation, tests, benchmarks, legacy wrappers
javascript/  Dependency-free JavaScript port, Node PNG adapter, CLI, tests
```

The two implementations are intentionally separated while preserving the same algorithmic behavior.

## Why it is different

- **One exact destination grid:** silhouette, boundaries and color decisions use the same fractional cell geometry.
- **Silhouette first:** alpha coverage decides whether a destination pixel exists before outline/color selection.
- **Outline-safe:** outline colors may win inside boundary cells but cannot create pixels outside the destination silhouette.
- **Palette preserving:** output RGB colors are selected from actual source colors rather than invented by interpolation.
- **Internal-edge aware:** important color transitions can survive even when they cover less area than a flat region.
- **Thin-feature preservation:** narrow one-pixel structures get a conservative center-sample rescue path.
- **Transparent-RGB safe:** hidden RGB in alpha-zero pixels cannot bleed into visible output.
- **Non-integer scales:** exact fractional overlap is used rather than independent floor/round coordinate transforms.
- **Deterministic:** stable scoring and tie-breakers produce repeatable output.

## Python

Install from the repository root:

```bash
python -m pip install -e .
```

```python
from better_pixel_art_downscale import downscale

result = downscale("character.png", (32, 32))
result.save("character_32.png")
```

Using divisors:

```python
from better_pixel_art_downscale import downscale_by_factor

result = downscale_by_factor("character.png", 2)
```

Advanced options:

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

The historical Python modules remain available after installation, including `image_resize_edge`, `image_resize`, `image_edges`, and `pattern_noise`.

## Experimental semantic Python engine

The `agent/semantic-surface-v2` work adds an experimental Python path that separates sprite topology from surface texture reconstruction instead of treating every local contrast as an internal edge.

```python
from better_pixel_art_downscale import (
    ContentHint,
    SemanticOptions,
    downscale_semantic,
)

result = downscale_semantic(
    "assets/minecraft/textures/block/stone.png",
    (8, 8),
    options=SemanticOptions(content_hint=ContentHint.BLOCK),
)
```

For Minecraft-style 2x reduction:

- **items** reuse the mature silhouette solver with a lower `0.05` alpha threshold and zero internal-edge score weight;
- **opaque blocks** use source-palette-first **phase-coherent surface sampling** in Oklab;
- **cutout/overlay blocks** keep a stable nearest sampling phase rather than promoting texture noise as outlines;
- the analyzer exposes `structure`, `texture`, and `dither` maps for future conservative region reasoning.

The semantic API is intentionally separate from `downscale()` while the new behavior is being validated. See `python/benchmarks/MINECRAFT_F8THFUL_SEMANTIC_RESULTS.md` for the current Minecraft 26.2 -> F8thful benchmark.

## JavaScript

The JavaScript core has **zero external runtime dependencies** and consumes raw RGBA bytes:

```js
import { downscale } from './javascript/src/index.js';

const result = downscale({
  width: 16,
  height: 16,
  data: rgbaBytes,
}, [8, 8]);
```

For Node PNG files, a small built-in-only adapter uses `node:fs` and `node:zlib`:

```js
import { downscaleFile } from './javascript/src/node.js';

downscaleFile('character.png', 'character_8.png', {
  size: [8, 8],
});
```

Python-style aliases such as `downscale_by_factor`, `edge_layer`, and `downscale_file` are also available. JavaScript options accept both camelCase and Python snake_case names.

See `javascript/README.md` for the complete JavaScript API.

## Python ↔ JavaScript parity

The port was validated against the Minecraft 26.2 benchmark used during development:

- **1,964** exact 16×16 item/block textures;
- each reduced to 8×8 by Python and JavaScript;
- **502,784** RGBA output bytes compared;
- **1,964 / 1,964 byte-for-byte identical outputs**;
- **0 differing output bytes**.

The Minecraft assets are not included in this repository. The methodology is documented in `javascript/PARITY.md`.

## CLI

Python:

```bash
better-pixel-art-downscale input.png output.png --size 32x32
better-pixel-art-downscale input.png output.png --factor 2
```

JavaScript:

```bash
node javascript/src/cli.js input.png output.png --size 32x32
node javascript/src/cli.js input.png output.png --factor 2
```

Useful switches in both implementations include alpha threshold control and disabling outline, internal-edge, or thin-feature preservation.

## Development

Python:

```bash
python -m pip install -e .[dev]
pytest
ruff check python
python python/benchmarks/benchmark.py
```

Semantic Minecraft/F8thful benchmark:

```bash
python -m pip install -e .[benchmark]
python python/benchmarks/minecraft_f8thful_semantic.py \
  --jar /path/to/26.2.jar \
  --f8thful /path/to/F8thful.zip \
  --output-dir benchmark-output
```

JavaScript:

```bash
npm test --prefix javascript
```

CI runs the Python suite on Python 3.10–3.13 and the JavaScript suite on Node 18, 20 and 22.
