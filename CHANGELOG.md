# Changelog

## 2.0.0

- Rebuilt the downscaler around one exact destination grid.
- Fixed outline offset and size drift caused by separately resizing edge coordinates.
- Added alpha-coverage silhouette decisions and destination-space boundary detection.
- Added palette-preserving, edge-aware color selection.
- Removed the OpenCV dependency and the mutating edge-tracing pipeline.
- Added a typed public API, CLI, package metadata, compatibility wrappers, tests, and CI.
