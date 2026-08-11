# BetterPixelArtDownscale — JavaScript

A zero-external-dependency JavaScript port of the BetterPixelArtDownscale v2 algorithm.

The core intentionally mirrors the Python implementation: one exact destination grid, alpha-coverage occupancy, silhouette-first boundary classification, outline/internal-edge support, source-palette color selection, thin-feature preservation, deterministic tie-breaking, and binary/semitransparent alpha handling.

## Install from this repository

```bash
cd javascript
npm install
```

There are no npm runtime dependencies.

## Core API

The browser-safe core works on raw RGBA buffers:

```js
import {
  DownscaleOptions,
  downscale,
  downscaleByFactor,
  edgeLayer,
} from './javascript/src/index.js';

const source = {
  width: 16,
  height: 16,
  data: rgbaBytes, // Uint8Array or Uint8ClampedArray, width * height * 4
};

const result = downscale(source, [8, 8]);
console.log(result.width, result.height, result.data);
```

Python-style aliases are also exported:

```js
import { downscale_by_factor, edge_layer } from './javascript/src/index.js';
```

`DownscaleOptions` accepts both JavaScript-style and Python-style option names:

```js
const options = new DownscaleOptions({
  alphaThreshold: 0.5,
  preserveThinFeatures: true,
  preserveOutline: true,
  preserveInternalEdges: true,
});

// Equivalent:
const sameOptions = new DownscaleOptions({
  alpha_threshold: 0.5,
  preserve_thin_features: true,
  preserve_outline: true,
  preserve_internal_edges: true,
});
```

## Browser ImageData

```js
import { fromImageData, toImageData, downscale } from './javascript/src/index.js';

const source = fromImageData(ctx.getImageData(0, 0, 16, 16));
const small = downscale(source, [8, 8]);
ctx.putImageData(toImageData(small), 0, 0);
```

## Node PNG files

The Node adapter includes a small PNG reader/writer implemented with Node built-ins only (`node:fs` and `node:zlib`). No third-party image library is required.

```js
import { downscaleFile } from './javascript/src/node.js';

downscaleFile('character.png', 'character_8.png', {
  size: [8, 8],
});
```

Or by factor:

```js
import { downscale_file } from './javascript/src/node.js';

downscale_file('character.png', 'character_half.png', {
  factor: 2,
});
```

The PNG decoder supports the non-interlaced grayscale, RGB, indexed/palette, grayscale+alpha and RGBA formats used by the Minecraft texture benchmark, including 1/2/4/8-bit indexed PNGs. The encoder writes standard non-interlaced RGBA8 PNGs.

## CLI

From `javascript/`:

```bash
node src/cli.js input.png output.png --size 8x8
node src/cli.js input.png output.png --factor 2
```

When installed as a package:

```bash
better-pixel-art-downscale-js input.png output.png --size 8x8
```

Useful flags:

```text
--alpha-threshold 0.5
--no-outline
--no-internal-edges
--no-thin-features
```

## Tests

```bash
npm test
```

The test suite uses Node's built-in `node:test`; it has no dev dependencies either.

See `PARITY.md` for the Python ↔ JavaScript parity validation.
