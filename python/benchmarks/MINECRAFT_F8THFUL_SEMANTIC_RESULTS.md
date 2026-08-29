# Minecraft 26.2 -> F8thful semantic-v2 benchmark

This benchmark compares the current BPAD implementation, the experimental semantic-v2 engine, Pillow BOX, and nearest-neighbor against the supplied F8thful 8x resource pack.

The fair set requires the same texture path in both packs and a F8thful target exactly half the Vanilla width and height. Entities are intentionally excluded because this F8thful release frequently changes entity UV layouts rather than providing a geometrically comparable half-resolution sheet.

## Dataset

- Items: **670** comparable textures
- Blocks: **1,064** comparable textures
- Primary total: **1,734** textures

## Results

| Category | Method | Composite | Dice | Boundary F1 | mean DeltaE00 | SSIM | Exact RGBA |
|---|---:|---:|---:|---:|---:|---:|---:|
| Items | Semantic v2 | **82.02** | **0.9023** | **0.7522** | **7.99** | 0.7277 | **0.4311** |
| Items | BOX | 81.94 | 0.9023 | 0.7522 | 8.62 | **0.7654** | 0.1429 |
| Items | BPAD 2.1 default | 81.19 | 0.8970 | 0.7449 | 8.75 | 0.7225 | 0.4192 |
| Items | Nearest | 76.53 | 0.8438 | 0.6206 | 9.01 | 0.7043 | 0.3633 |
| Blocks | Semantic v2 | **85.93** | 0.9330 | 0.9117 | 6.05 | 0.5695 | 0.3526 |
| Blocks | Nearest | 85.89 | 0.9330 | **0.9117** | **5.91** | 0.5568 | **0.3599** |
| Blocks | BOX | 85.80 | **0.9441** | 0.9024 | 6.42 | **0.5912** | 0.0597 |
| Blocks | BPAD 2.1 default | 84.60 | 0.9335 | 0.8991 | 6.77 | 0.5372 | 0.3161 |

Primary weighted composite (items + blocks):

- **Semantic v2: 84.42**
- BOX: 84.31
- BPAD 2.1 default: 83.28
- Nearest: 82.27

The composite is the same diagnostic score used by the earlier benchmark:

`100 * (0.35*Dice + 0.20*boundaryF1 + 0.25*((SSIM+1)/2) + 0.20*exp(-meanDeltaE00/20))`

It is not a standard perceptual metric and should be interpreted together with the component metrics.

## What changed

### Sprite policy

Items reuse the mature silhouette solver rather than replacing it. The Minecraft 2x profile lowers the alpha coverage threshold to `0.05` and removes internal-edge score weight. This preserves sparse silhouettes that the default `0.50` threshold can delete.

### Surface policy

Opaque block textures no longer treat every strong local contrast as an internal edge. The analyzer estimates coherent structure, local texture energy, and two-pixel recurrence/dither, but the first benchmarked surface policy deliberately does **not** promote internal-edge evidence by default.

Instead it uses **phase-coherent surface sampling**: each destination cell forms a perceptual Oklab representative, then shifts that representative 40% toward the stable center-sample phase before choosing a source-palette color. A small anchor prior (`0.02`) discourages arbitrary phase changes without locking the result to nearest-neighbor.

Ablation showed that error diffusion and a continuous structure bonus both reduced F8thful similarity, so neither is enabled by default in this prototype.

### Cutout / overlay blocks

Minecraft block textures with alpha use stable phase sampling (nearest) in the current block profile. This is intentional: on the comparable transparent-block subset it was substantially stronger than the original edge-aware policy. Future work should split vegetation, rails/grates, overlays, and sparse cracks into more specific surface/topology classes.

## Interpretation

Semantic v2 is the first tested configuration in this repository that narrowly leads the aggregate F8thful benchmark in **both** primary categories without making BOX-style blended colors the default. The block gain is small versus nearest/BOX, so it should be treated as an experimental foundation rather than a solved surface model.

The largest remaining opportunity is to make the currently diagnostic structure/texture/dither maps actionable through conservative, context-dependent rules instead of a global edge reward. In particular, true region boundaries in bricks/planks/ores should be promoted only when directional coherence and multi-cell support distinguish them from granulation.
