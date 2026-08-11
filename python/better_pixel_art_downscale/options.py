from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownscaleOptions:
    """Configuration for edge-aware pixel-art downscaling.

    The defaults are intentionally conservative: the output silhouette is decided
    once from alpha coverage, then outline and internal-edge colors are selected
    only inside that silhouette. This prevents outline growth and coordinate drift.
    """

    alpha_threshold: float = 0.50
    source_alpha_threshold: float = 1.0 / 255.0
    preserve_thin_features: bool = True
    thin_feature_threshold: float = 0.125
    preserve_outline: bool = True
    preserve_internal_edges: bool = True
    outline_min_coverage: float = 0.02
    internal_edge_threshold: float = 0.10
    internal_edge_weight: float = 0.65
    binary_alpha: bool | None = None

    def validate(self) -> None:
        for name in (
            "alpha_threshold",
            "source_alpha_threshold",
            "thin_feature_threshold",
            "outline_min_coverage",
            "internal_edge_threshold",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value!r}")
        if self.internal_edge_weight < 0.0:
            raise ValueError("internal_edge_weight must be non-negative")
