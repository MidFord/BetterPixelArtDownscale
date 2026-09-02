# BetterPixelArtDownscale — JavaScript

A zero-runtime-dependency JavaScript implementation of BetterPixelArtDownscale, including the legacy edge-aware v2 core and the Python-parity **Semantic v3** engine.

Semantic v3 separates three different pixel-art problems instead of treating every contrast as an edge:

- **sprites/items** use the mature silhouette, outline, and thin-feature solver with the Minecraft 2x tuning;
- **opaque surfaces/blocks** use source-palette-first phase-coherent sampling in Oklab;
- **cutout/alpha textures** use topology-aware routing: stable phase, bbox phase rescue, spanning coverage, dense coverage, sprite topology, and ghost-alpha preservation.

The implementation mirrors the Python semantic engine's thresholds, routing, color scoring, and deterministic tie behavior. The Blockbench bundle is tested byte-for-byte against this modular JavaScript implementation on representative sprite, surface, ghost-alpha, and cutout fixtures.

## Install from this repository

```bash
cd javascript
npm install
```

There are no npm runtime dependencies.

## Semantic v3 API

```js
import {
  ContentHint,
  SemanticOptions,
  downscaleSemanticV3,
} from './javascript/src/index.js';

const source = {
  width: 16,
  height: 16,
  data: rgbaBytes, // Uint8Array or Uint8ClampedArray
};

const result = downscaleSemanticV3(
  source,
  [8, 8],
  new SemanticOptions({ contentHint: ContentHint.BLOCK }),
);
```

`ContentHint` supports `AUTO`, `ITEM`, `BLOCK`, and `ENTITY`. `AUTO` analyzes alpha occupancy and topology; a known hint is preferable when the asset category is already available.

Python-style aliases are exported as well:

```js
import {
  downscale_semantic_v3,
  downscale_semantic_v3_by_factor,
  analyze_cutout,
} from './javascript/src/index.js';
```

The cutout analyzer is directly accessible for diagnostics:

```js
import { analyzeCutout, CutoutPolicy } from './javascript/src/index.js';

const analysis = analyzeCutout(source, [8, 8]);
console.log(analysis.policy === CutoutPolicy.SPANNING_COVERAGE);
```

## Legacy v2 API

The original edge-aware API remains available and unchanged:

```js
import {
  DownscaleOptions,
  downscale,
  downscaleByFactor,
  edgeLayer,
} from './javascript/src/index.js';

const result = downscale(source, [8, 8], new DownscaleOptions({
  alphaThreshold: 0.5,
  preserveThinFeatures: true,
  preserveOutline: true,
  preserveInternalEdges: true,
}));
```

Both camelCase and Python-style option names remain accepted by `DownscaleOptions`.

## Browser ImageData

```js
import { fromImageData, toImageData, downscaleSemanticV3 } from './javascript/src/index.js';

const source = fromImageData(ctx.getImageData(0, 0, 16, 16));
const small = downscaleSemanticV3(source, [8, 8], { contentHint: 'block' });
ctx.putImageData(toImageData(small), 0, 0);
```

## Blockbench plugin

The root `better_pixel_art_downscale.js` plugin embeds the same Semantic v3 engine. In the native **Resize Texture** dialog it exposes:

- **Semantic v3 (Recommended)** — the new default;
- content type: **Auto / Item / Block / Entity**;
- **Legacy Edge-Aware v2** for the historical behavior and advanced controls;
- **Native Nearest** as a baseline/fallback.

The integration preserves Blockbench's existing handling for animation frames, layers, Undo, and UV resizing.

## Node PNG files

The Node adapter includes a small PNG reader/writer implemented with Node built-ins only (`node:fs` and `node:zlib`). No third-party image library is required.

```js
import { downscaleFile } from './javascript/src/node.js';

downscaleFile('character.png', 'character_8.png', {
  size: [8, 8],
});
```

The file/CLI adapter currently retains the stable legacy API; Semantic v3 is available through the raw-RGBA API above.

## CLI

```bash
node src/cli.js input.png output.png --size 8x8
node src/cli.js input.png output.png --factor 2
```

When installed as a package:

```bash
better-pixel-art-downscale-js input.png output.png --size 8x8
```

## Tests

```bash
npm test
```

The suite uses Node's built-in `node:test` and includes semantic routing tests plus a VM test that loads the actual Blockbench plugin bundle and compares its Semantic v3 output byte-for-byte with the modular implementation.

See `PARITY.md` for the original Python ↔ JavaScript core parity validation.
