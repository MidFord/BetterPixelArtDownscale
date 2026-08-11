# Changelog

## 2.1.0

- Added a dependency-free JavaScript port of the v2 downscaling core.
- Matched Python behavior for fractional coverage, occupancy, outlines, internal edges, palette selection, thin features, alpha handling, and deterministic tie-breaking.
- Added browser/raw-RGBA helpers and a Node PNG adapter/CLI using only built-in modules.
- Validated the JavaScript port byte-for-byte against 1,964 Minecraft 26.2 16×16 → 8×8 texture outputs with zero differing RGBA bytes.
- Separated the Python implementation into `python/` and the JavaScript implementation into `javascript/`.
- Expanded CI to test both language implementations.

## 2.0.0

- Rebuilt the downscaler around one exact destination grid.
- Fixed outline offset and size drift caused by separately resizing edge coordinates.
- Added alpha-coverage silhouette decisions and destination-space boundary detection.
- Added palette-preserving, edge-aware color selection.
- Removed the OpenCV dependency and the mutating edge-tracing pipeline.
- Added a typed public API, CLI, package metadata, compatibility wrappers, tests, and CI.
