# Minecraft 26.2 -> F8thful semantic-v3 benchmark

Semantic v3 keeps the semantic-v2 item and opaque-surface solvers unchanged and replaces the single nearest-neighbor cutout policy with a topology-aware router.

Entities remain excluded because the supplied F8thful release frequently changes entity UV layout instead of providing a directly comparable half-resolution sheet.

## Comparable dataset

- Items: **670**
- Blocks: **1,064**
- Total: **1,734**
- Transparent/cutout blocks: **411**
- Opaque surface blocks: **653**

## Results

| Category | Method | Composite | Dice | Boundary F1 | mean DeltaE00 | SSIM | Exact RGBA |
|---|---:|---:|---:|---:|---:|---:|---:|
| Items | Semantic v3 | **82.02** | 0.9023 | 0.7522 | 7.99 | 0.7277 | 0.4311 |
| Blocks | Semantic v3 | **86.93** | **0.9478** | **0.9245** | **5.67** | 0.5822 | 0.3525 |

Semantic v3 intentionally produces the same item result as semantic v2. The change is isolated to cutout blocks.

### Block progression

- BPAD 2.1 default: **84.60**
- Semantic v2: **85.93**
- Semantic v3: **86.93**

### Cutout-only progression

- Semantic v2 fixed stable phase: **82.65**
- Semantic v3 topology-aware policy: **85.24**

Cutout Dice rises from approximately **0.848 -> 0.886**, and cutout boundary F1 from approximately **0.801 -> 0.834**.

### Primary weighted composite

Items + blocks, weighted by texture count:

- Semantic v2: **84.42**
- Semantic v3: **85.03**

## v3 topology regimes

The router uses only source alpha geometry; it does not inspect texture names or F8thful at inference time.

### Stable phase

Nearest sampling remains the default when it already represents the topology well. This is especially important for authored high-frequency patterns and low-alpha overlays.

### Ghost-alpha overlay

Texels with alpha 1-4/255 are treated as intentional information rather than empty space. Minecraft destroy-stage textures are the canonical example. Binary occupancy processing destroys this signal, while stable phase sampling preserves it.

### Spanning thin lattice

A very small bounding box touching multiple tile edges behaves differently from a freestanding sprite. Pane tops and similar structures preserve sub-cell coverage so a two-pixel-wide line that straddles a 2x cell boundary does not collapse incorrectly.

### Bbox phase rescue

For tiny freestanding features, v3 first tests the stable phase. It changes phase only when stable nearest would erase the feature completely. The rescue phase is aligned to the source bounding-box origin.

### Dense coverage

Fragmented masks with moderate occupancy use 50% area coverage instead of promoting every alpha transition as an outline. Full-tile coherent masks with moderate transition density stay on the stable phase.

### Sprite topology

Dense high-occupancy cutouts such as leaves/grates use the mature silhouette solver, where explicit topology preservation is stronger than simple phase sampling.

## Important ablations

Several ideas were tested and rejected before this configuration:

- selecting a policy by reconstruction error after re-upscaling the output did not correlate sufficiently with the human 8x decision;
- routing every soft-alpha texture to nearest fixed destroy stages but regressed glass, water, honey and portal textures;
- treating every thin feature as an area-preservation problem expanded isolated features such as torches;
- changing the sampling phase whenever another phase better reconstructed the source caused unnecessary color-phase regressions.

The final policy therefore follows a conservative rule: **stable phase first, topology-specific intervention only when source geometry provides evidence that stable sampling is structurally wrong.**

## Reproduce

```bash
python -m pip install -e .[benchmark]
python python/benchmarks/minecraft_f8thful_semantic_v3.py \
  --jar /path/to/26.2.jar \
  --f8thful /path/to/F8thful.zip \
  --output-dir benchmark-output-v3
```
