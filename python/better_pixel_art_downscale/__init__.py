"""Edge-aware, silhouette-stable pixel-art downscaling."""

from .core import downscale, downscale_by_factor, downscale_file, edge_layer
from .options import DownscaleOptions

__all__ = [
    "DownscaleOptions",
    "downscale",
    "downscale_by_factor",
    "downscale_file",
    "edge_layer",
]

__version__ = "2.1.0"
