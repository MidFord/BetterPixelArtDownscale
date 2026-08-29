from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import pandas as pd
from PIL import Image

from better_pixel_art_downscale import downscale
from better_pixel_art_downscale.semantic import ContentHint, SemanticOptions, downscale_semantic
from better_pixel_art_downscale.semantic_v3 import downscale_semantic_v3
from minecraft_f8thful_semantic import _fair_pairs, _metrics


def run(jar_path: Path, f8_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    with zipfile.ZipFile(jar_path) as jar, zipfile.ZipFile(f8_path) as f8:
        pairs = list(_fair_pairs(jar, f8))
        for index, (category, path, source, reference) in enumerate(pairs, start=1):
            target = reference.size
            hint = ContentHint.ITEM if category == "item" else ContentHint.BLOCK
            options = SemanticOptions(content_hint=hint)
            methods = {
                "BPAD": downscale(source, target),
                "SEMANTIC_V2": downscale_semantic(source, target, options=options),
                "SEMANTIC_V3": downscale_semantic_v3(source, target, options=options),
                "BOX": source.resize(target, resample=Image.Resampling.BOX),
                "NEAREST": source.resize(target, resample=Image.Resampling.NEAREST),
            }
            for method, prediction in methods.items():
                row = _metrics(prediction, reference)
                row.update(category=category, path=path, method=method)
                rows.append(row)

            if index % 250 == 0:
                print(f"{index}/{len(pairs)} textures")

    results = pd.DataFrame(rows)
    results.to_csv(output_dir / "results.csv", index=False)
    summary = (
        results.groupby(["category", "method"])
        .agg(
            n=("path", "size"),
            composite_score=("composite_score", "mean"),
            silhouette_dice=("silhouette_dice", "mean"),
            boundary_f1=("boundary_f1", "mean"),
            deltaE00=("deltaE00_mean", "mean"),
            ssim=("ssim", "mean"),
            exact_rgba=("exact_rgba", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(output_dir / "summary.csv", index=False)
    print(summary.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Minecraft 26.2 -> F8thful semantic-v3 benchmark")
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--f8thful", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark-output-v3"))
    args = parser.parse_args()
    run(args.jar, args.f8thful, args.output_dir)


if __name__ == "__main__":
    main()
