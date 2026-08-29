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

__all__ = [
    "ContentHint",
    "DownscaleOptions",
    "SemanticAnalysis",
    "SemanticMode",
    "SemanticOptions",
    "analyze",
    "downscale",
    "downscale_by_factor",
    "downscale_file",
    "downscale_semantic",
    "downscale_semantic_by_factor",
    "edge_layer",
]

__version__ = "2.1.0"
