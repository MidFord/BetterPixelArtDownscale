from __future__ import annotations

import argparse
import io
import math
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from skimage.color import deltaE_ciede2000, rgb2lab
from skimage.metrics import structural_similarity

from better_pixel_art_downscale import downscale
from better_pixel_art_downscale.semantic import ContentHint, SemanticOptions, downscale_semantic

CATEGORIES = ("item", "block")


def _load_png(archive: zipfile.ZipFile, path: str) -> Image.Image:
    return Image.open(io.BytesIO(archive.read(path))).convert("RGBA")


def _boundary(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, constant_values=False)
    return mask & ~(
        padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )


def _f1(a: np.ndarray, b: np.ndarray) -> float:
    tp = int(np.logical_and(a, b).sum())
    fp = int(np.logical_and(a, ~b).sum())
    fn = int(np.logical_and(~a, b).sum())
    if tp == 0:
        return 1.0 if fp == 0 and fn == 0 else 0.0
    return 2 * tp / (2 * tp + fp + fn)


def _metrics(prediction: Image.Image, reference: Image.Image) -> dict[str, float]:
    pred = np.asarray(prediction.convert("RGBA"), dtype=np.uint8)
    ref = np.asarray(reference.convert("RGBA"), dtype=np.uint8)
    pred_mask, ref_mask = pred[..., 3] > 0, ref[..., 3] > 0
    overlap = pred_mask & ref_mask
    intersection = int(overlap.sum())
    union = int(np.logical_or(pred_mask, ref_mask).sum())
    pred_count, ref_count = int(pred_mask.sum()), int(ref_mask.sum())
    iou = intersection / union if union else 1.0
    dice = 2 * intersection / (pred_count + ref_count) if pred_count + ref_count else 1.0
    boundary_f1 = _f1(_boundary(pred_mask), _boundary(ref_mask))

    if overlap.any():
        pred_lab = rgb2lab(pred[..., :3].astype(np.float64) / 255.0)
        ref_lab = rgb2lab(ref[..., :3].astype(np.float64) / 255.0)
        delta_mean = float(np.mean(deltaE_ciede2000(pred_lab[overlap], ref_lab[overlap])))
    else:
        delta_mean = 100.0

    pred_premul = pred[..., :3].astype(np.float64) * (pred[..., 3:4] / 255.0)
    ref_premul = ref[..., :3].astype(np.float64) * (ref[..., 3:4] / 255.0)
    win_size = min(7, pred.shape[0], pred.shape[1])
    if win_size % 2 == 0:
        win_size -= 1
    ssim = float(
        structural_similarity(
            pred_premul,
            ref_premul,
            channel_axis=-1,
            data_range=255.0,
            win_size=win_size,
        )
    )
    exact_rgba = float(np.mean(np.all(pred == ref, axis=-1)))
    composite = 100.0 * (
        0.35 * dice
        + 0.20 * boundary_f1
        + 0.25 * ((ssim + 1.0) / 2.0)
        + 0.20 * math.exp(-delta_mean / 20.0)
    )
    return {
        "silhouette_iou": iou,
        "silhouette_dice": dice,
        "boundary_f1": boundary_f1,
        "deltaE00_mean": delta_mean,
        "ssim": ssim,
        "exact_rgba": exact_rgba,
        "composite_score": composite,
    }


def _fair_pairs(jar: zipfile.ZipFile, f8: zipfile.ZipFile):
    f8_names = set(f8.namelist())
    for category in CATEGORIES:
        prefix = f"assets/minecraft/textures/{category}/"
        names = sorted(
            name for name in jar.namelist() if name.startswith(prefix) and name.endswith(".png")
        )
        for path in names:
            if path not in f8_names:
                continue
            source = _load_png(jar, path)
            reference = _load_png(f8, path)
            if reference.size != (source.width // 2, source.height // 2):
                continue
            yield category, path, source, reference


def run(jar_path: Path, f8_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(jar_path) as jar, zipfile.ZipFile(f8_path) as f8:
        pairs = list(_fair_pairs(jar, f8))
        for index, (category, path, source, reference) in enumerate(pairs, start=1):
            target = reference.size
            hint = ContentHint.ITEM if category == "item" else ContentHint.BLOCK
            methods = {
                "BPAD": downscale(source, target),
                "SEMANTIC_V2": downscale_semantic(
                    source,
                    target,
                    options=SemanticOptions(content_hint=hint),
                ),
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
    parser = argparse.ArgumentParser(description="Minecraft 26.2 -> F8thful 8x benchmark")
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--f8thful", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark-output"))
    args = parser.parse_args()
    run(args.jar, args.f8thful, args.output_dir)


if __name__ == "__main__":
    main()
