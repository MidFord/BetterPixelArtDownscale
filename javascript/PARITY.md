# Python ↔ JavaScript parity

The JavaScript core is a direct behavioral port of BetterPixelArtDownscale v2, not a visually similar substitute.

## Validation performed

A development parity harness compared the current Python implementation against the JavaScript implementation on the Minecraft 26.2 texture benchmark used while developing this port.

- Exact 16×16 textures tested: **1,964**
- Items: **789**
- Blocks: **1,175**
- Operation: **16×16 → 8×8**
- RGBA output bytes compared: **502,784**
- Images with byte-for-byte identical output: **1,964 / 1,964**
- Differing output bytes: **0**

The Minecraft assets themselves are not committed to this repository.

## What is intentionally mirrored

The port preserves the Python implementation's key numerical and structural behavior:

- exact fractional source-area overlap for every destination cell;
- Float32-style storage/rounding where the NumPy implementation uses `float32`;
- alpha-weighted source coverage;
- destination occupancy before color selection;
- thin-feature center sampling;
- destination-boundary classification from the final occupancy map;
- source outline detection;
- weighted RGB internal-edge detection;
- source-palette-only color candidates;
- outline and internal-edge support scoring;
- the same deterministic tie-breaking order;
- binary-alpha detection and area-aware semitransparent output;
- no independently resized edge overlay.

Because JavaScript's core API receives raw RGBA bytes instead of a Pillow image object, file decoding is kept outside the algorithm. The optional Node adapter provides PNG file I/O without third-party dependencies.
