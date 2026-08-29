"""Edge-aware and semantic pixel-art downscaling."""

from .core import downscale, downscale_by_factor, downscale_file, edge_layer
from .options import DownscaleOptions
from .semantic import (
    ContentHint,
    SemanticAnalysis,
    SemanticMode,
    SemanticOptions,
    analyze,
    downscale_semantic,
    downscale_semantic_by_factor,
)
from .semantic_v3 import (
    CutoutAnalysis,
    CutoutPolicy,
    analyze_cutout,
    downscale_cutout,
    downscale_semantic_v3,
    downscale_semantic_v3_by_factor,
)

__all__ = [
    "ContentHint",
    "CutoutAnalysis",
    "CutoutPolicy",
    "DownscaleOptions",
    "SemanticAnalysis",
    "SemanticMode",
    "SemanticOptions",
    "analyze",
    "analyze_cutout",
    "downscale",
    "downscale_by_factor",
    "downscale_cutout",
    "downscale_file",
    "downscale_semantic",
    "downscale_semantic_by_factor",
    "downscale_semantic_v3",
    "downscale_semantic_v3_by_factor",
    "edge_layer",
]

__version__ = "2.1.0"
