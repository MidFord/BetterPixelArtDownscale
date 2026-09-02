import {
  ContentHint,
  SemanticMode,
  SemanticOptions,
  analyze,
  inferContentHint,
  nearestResize,
  normalizeSemanticOptions,
  pixelIndex,
  spriteDownscale,
  surfaceDownscale,
  validateImage,
  validateTargetSize,
} from './semantic.js';

export const CutoutPolicy = Object.freeze({
  STABLE_PHASE: 'stable_phase',
  BBOX_PHASE_RESCUE: 'bbox_phase_rescue',
  SPANNING_COVERAGE: 'spanning_coverage',
  DENSE_COVERAGE: 'dense_coverage',
  SPRITE_TOPOLOGY: 'sprite_topology',
});

function bboxStats(mask, width, height) {
  let x0 = width;
  let x1 = 0;
  let y0 = height;
  let y1 = 0;
  let count = 0;
  let top = false;
  let bottom = false;
  let left = false;
  let right = false;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (!mask[pixelIndex(width, x, y)]) continue;
      count += 1;
      x0 = Math.min(x0, x);
      x1 = Math.max(x1, x + 1);
      y0 = Math.min(y0, y);
      y1 = Math.max(y1, y + 1);
      if (y === 0) top = true;
      if (y === height - 1) bottom = true;
      if (x === 0) left = true;
      if (x === width - 1) right = true;
    }
  }
  if (!count) return { fill: 0.0, areaRatio: 0.0, touches: 0, x0: 0, y0: 0 };
  const bboxArea = Math.max(1, (x1 - x0) * (y1 - y0));
  return {
    fill: count / bboxArea,
    areaRatio: bboxArea / (width * height),
    touches: Number(top) + Number(bottom) + Number(left) + Number(right),
    x0,
    y0,
  };
}

function alphaPatternStats(visible, width, height) {
  let horizontalDiff = 0;
  let verticalDiff = 0;
  let horizontalSame2 = 0;
  let verticalSame2 = 0;
  const count = width * height;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const value = visible[pixelIndex(width, x, y)];
      if (value !== visible[pixelIndex(width, (x - 1 + width) % width, y)]) horizontalDiff += 1;
      if (value !== visible[pixelIndex(width, x, (y - 1 + height) % height)]) verticalDiff += 1;
      if (value === visible[pixelIndex(width, (x - 2 + width) % width, y)]) horizontalSame2 += 1;
      if (value === visible[pixelIndex(width, x, (y - 2 + height) % height)]) verticalSame2 += 1;
    }
  }
  return {
    transition: 0.5 * (horizontalDiff / count + verticalDiff / count),
    recurrence: 0.5 * (horizontalSame2 / count + verticalSame2 / count),
  };
}

function phaseDownscale2x(image, size, phaseX, phaseY) {
  const [targetWidth, targetHeight] = size;
  if (image.width !== targetWidth * 2 || image.height !== targetHeight * 2) return nearestResize(image, size);
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);
  for (let ty = 0; ty < targetHeight; ty += 1) {
    for (let tx = 0; tx < targetWidth; tx += 1) {
      const sx = phaseX + tx * 2;
      const sy = phaseY + ty * 2;
      const sourceP = pixelIndex(image.width, sx, sy) * 4;
      const targetP = pixelIndex(targetWidth, tx, ty) * 4;
      output[targetP] = image.data[sourceP];
      output[targetP + 1] = image.data[sourceP + 1];
      output[targetP + 2] = image.data[sourceP + 2];
      output[targetP + 3] = image.data[sourceP + 3];
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

function axisCells(sourceLength, targetLength) {
  const scale = sourceLength / targetLength;
  const cells = [];
  for (let index = 0; index < targetLength; index += 1) {
    const start = index * scale;
    const end = (index + 1) * scale;
    const indices = [];
    const weights = [];
    for (let sourceIndex = Math.floor(start); sourceIndex < Math.ceil(end); sourceIndex += 1) {
      indices.push(sourceIndex);
      weights.push(Math.max(0.0, Math.min(sourceIndex + 1.0, end) - Math.max(sourceIndex, start)));
    }
    cells.push({ indices, weights });
  }
  return cells;
}

function coverageDownscale(image, size, occupancyThreshold) {
  const [targetWidth, targetHeight] = size;
  const xCells = axisCells(image.width, targetWidth);
  const yCells = axisCells(image.height, targetHeight);
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);

  for (let ty = 0; ty < targetHeight; ty += 1) {
    const yCell = yCells[ty];
    for (let tx = 0; tx < targetWidth; tx += 1) {
      const xCell = xCells[tx];
      let weightedAlpha = 0;
      let weightSum = 0;
      const visibleColors = new Map();
      for (let yi = 0; yi < yCell.indices.length; yi += 1) {
        const sy = yCell.indices[yi];
        for (let xi = 0; xi < xCell.indices.length; xi += 1) {
          const sx = xCell.indices[xi];
          const weight = yCell.weights[yi] * xCell.weights[xi];
          weightSum += weight;
          const p = pixelIndex(image.width, sx, sy) * 4;
          const alpha = image.data[p + 3] / 255.0;
          weightedAlpha += weight * alpha;
          if (!(alpha > 0)) continue;
          const code = (image.data[p] << 16) | (image.data[p + 1] << 8) | image.data[p + 2];
          visibleColors.set(code, (visibleColors.get(code) ?? 0) + 1);
        }
      }
      const coverage = weightedAlpha / Math.max(weightSum, 1e-12);
      if (coverage < occupancyThreshold || visibleColors.size === 0) continue;

      const sourceX = Math.min(image.width - 1, Math.trunc((tx + 0.5) * image.width / targetWidth));
      const sourceY = Math.min(image.height - 1, Math.trunc((ty + 0.5) * image.height / targetHeight));
      const sourceP = pixelIndex(image.width, sourceX, sourceY) * 4;
      let r;
      let g;
      let b;
      if (image.data[sourceP + 3] > 0) {
        r = image.data[sourceP];
        g = image.data[sourceP + 1];
        b = image.data[sourceP + 2];
      } else {
        let bestCode = null;
        let bestCount = -1;
        for (const [code, count] of [...visibleColors.entries()].sort((a, bEntry) => a[0] - bEntry[0])) {
          if (count > bestCount) {
            bestCode = code;
            bestCount = count;
          }
        }
        r = (bestCode >> 16) & 255;
        g = (bestCode >> 8) & 255;
        b = bestCode & 255;
      }
      const targetP = pixelIndex(targetWidth, tx, ty) * 4;
      output[targetP] = r;
      output[targetP + 1] = g;
      output[targetP + 2] = b;
      output[targetP + 3] = 255;
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

export function analyzeCutout(image, size) {
  validateImage(image);
  const target = validateTargetSize(image, size);
  const visible = new Uint8Array(image.width * image.height);
  let visibleCount = 0;
  let ghostCount = 0;
  for (let i = 0; i < visible.length; i += 1) {
    const alphaByte = image.data[i * 4 + 3];
    if (alphaByte > 0) {
      visible[i] = 1;
      visibleCount += 1;
      if (alphaByte <= 4) ghostCount += 1;
    }
  }
  const visibleRatio = visibleCount / visible.length;
  const ghostAlphaRatio = ghostCount / visible.length;
  const bbox = bboxStats(visible, image.width, image.height);
  const pattern = alphaPatternStats(visible, image.width, image.height);
  const exact2x = image.width === target[0] * 2 && image.height === target[1] * 2;
  let policy;

  if (ghostAlphaRatio > 0.02) {
    policy = CutoutPolicy.STABLE_PHASE;
  } else if (bbox.areaRatio <= 0.16) {
    const stable = nearestResize(image, target);
    let stableVisible = false;
    for (let i = 3; i < stable.data.length; i += 4) {
      if (stable.data[i] > 0) { stableVisible = true; break; }
    }
    if (bbox.touches >= 2) policy = CutoutPolicy.SPANNING_COVERAGE;
    else if (stableVisible || !exact2x) policy = CutoutPolicy.STABLE_PHASE;
    else policy = CutoutPolicy.BBOX_PHASE_RESCUE;
  } else if (pattern.transition <= 0.30) {
    policy = CutoutPolicy.STABLE_PHASE;
  } else if (visibleRatio <= 0.55) {
    if (bbox.areaRatio >= 0.95 && pattern.transition <= 0.41) policy = CutoutPolicy.STABLE_PHASE;
    else policy = CutoutPolicy.DENSE_COVERAGE;
  } else {
    policy = CutoutPolicy.SPRITE_TOPOLOGY;
  }

  return {
    visibleRatio,
    ghostAlphaRatio,
    bboxFillRatio: bbox.fill,
    bboxAreaRatio: bbox.areaRatio,
    bboxMinX: bbox.x0,
    bboxMinY: bbox.y0,
    edgeTouchCount: bbox.touches,
    alphaTransition: pattern.transition,
    alphaRecurrence: pattern.recurrence,
    policy,
  };
}

export function downscaleCutout(image, size, options = undefined) {
  validateImage(image);
  const normalized = options === undefined
    ? new SemanticOptions({ contentHint: ContentHint.BLOCK })
    : normalizeSemanticOptions(options);
  const target = validateTargetSize(image, size);
  const cutout = analyzeCutout(image, target);
  if (cutout.policy === CutoutPolicy.STABLE_PHASE) return nearestResize(image, target);
  if (cutout.policy === CutoutPolicy.SPANNING_COVERAGE) return coverageDownscale(image, target, 0.25);
  if (cutout.policy === CutoutPolicy.DENSE_COVERAGE) return coverageDownscale(image, target, 0.50);
  if (cutout.policy === CutoutPolicy.SPRITE_TOPOLOGY) return spriteDownscale(image, target, normalized);
  return phaseDownscale2x(image, target, cutout.bboxMinX & 1, cutout.bboxMinY & 1);
}

export function downscaleSemanticV3(image, size, options = undefined) {
  validateImage(image);
  let normalized = normalizeSemanticOptions(options);
  if (normalized.contentHint === ContentHint.AUTO && options && typeof options.sourcePath === 'string') {
    normalized = new SemanticOptions({ ...normalized, contentHint: inferContentHint(options.sourcePath) });
  }
  const target = validateTargetSize(image, size);
  if (target[0] === image.width && target[1] === image.height) {
    return { width: image.width, height: image.height, data: new Uint8ClampedArray(image.data) };
  }
  const analysis = analyze(image, normalized);
  if (analysis.mode === SemanticMode.PATTERN) return downscaleCutout(image, target, normalized);
  if (analysis.mode === SemanticMode.SPRITE) return spriteDownscale(image, target, normalized);
  return surfaceDownscale(analysis, target, normalized);
}

export function downscaleSemanticV3ByFactor(image, factor = 2.0, options = undefined) {
  validateImage(image);
  if (!Number.isFinite(factor) || factor < 1.0) throw new RangeError('factor must be a finite value of at least 1');
  const size = [Math.max(1, Math.floor(image.width / factor)), Math.max(1, Math.floor(image.height / factor))];
  return downscaleSemanticV3(image, size, options);
}
