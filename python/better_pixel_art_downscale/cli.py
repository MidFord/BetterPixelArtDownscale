from __future__ import annotations

import argparse
from pathlib import Path

from .core import downscale_file
from .options import DownscaleOptions


def _size(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        parsed = int(width), int(height)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            "size must use WIDTHxHEIGHT, for example 16x16"
        ) from exc
    if parsed[0] <= 0 or parsed[1] <= 0:
        raise argparse.ArgumentTypeError("size values must be positive")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="better-pixel-art-downscale",
        description="Downscale pixel art without shifting or enlarging outlines.",
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--size", type=_size, help="Exact output size, for example 16x16")
    target.add_argument("--factor", type=float, help="Width and height divisor")
    parser.add_argument("--alpha-threshold", type=float, default=0.50)
    parser.add_argument("--no-outline", action="store_true")
    parser.add_argument("--no-internal-edges", action="store_true")
    parser.add_argument("--no-thin-features", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = DownscaleOptions(
        alpha_threshold=args.alpha_threshold,
        preserve_outline=not args.no_outline,
        preserve_internal_edges=not args.no_internal_edges,
        preserve_thin_features=not args.no_thin_features,
    )
    downscale_file(
        args.input,
        args.output,
        size=args.size,
        factor=args.factor,
        options=options,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
