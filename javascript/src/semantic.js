import { downscale } from './core.js';

export const SemanticMode = Object.freeze({
  AUTO: 'auto',
  SPRITE: 'sprite',
  SURFACE: 'surface',
  PATTERN: 'pattern',
});

export const ContentHint = Object.freeze({
  AUTO: 'auto',
  ITEM: 'item',
  BLOCK: 'block',
  ENTITY: 'entity',
});

export class SemanticOptions {
  constructor(options = {}) {
    this.mode = options.mode ?? SemanticMode.AUTO;
    this.contentHint = options.contentHint ?? options.content_hint ?? ContentHint.AUTO;
    this.spriteAlphaThreshold = options.spriteAlphaThreshold ?? options.sprite_alpha_threshold ?? 0.05;
    this.spriteThinFeatureThreshold = options.spriteThinFeatureThreshold ?? options.sprite_thin_feature_threshold ?? 0.125;
    this.surfacePhaseWeight = options.surfacePhaseWeight ?? options.surface_phase_weight ?? 0.40;
    this.surfaceAnchorWeight = options.surfaceAnchorWeight ?? options.surface_anchor_weight ?? 0.02;
    this.surfaceCoverageWeight = options.surfaceCoverageWeight ?? options.surface_coverage_weight ?? 0.08;
    this.surfaceDarkNoisePenalty = options.surfaceDarkNoisePenalty ?? options.surface_dark_noise_penalty ?? 0.18;
    this.surfaceStructureWeight = options.surfaceStructureWeight ?? options.surface_structure_weight ?? 0.0;
    this.surfaceDitherSuppression = options.surfaceDitherSuppression ?? options.surface_dither_suppression ?? 0.80;
    this.tileAware = options.tileAware ?? options.tile_aware ?? true;
    this.validate();
  }

  validate() {
    if (!Object.values(SemanticMode).includes(this.mode)) throw new RangeError(`invalid semantic mode: ${this.mode}`);
    if (!Object.values(ContentHint).includes(this.contentHint)) throw new RangeError(`invalid content hint: ${this.contentHint}`);
    for (const name of [
      'spriteAlphaThreshold',
      'spriteThinFeatureThreshold',
      'surfacePhaseWeight',
      'surfaceAnchorWeight',
      'surfaceCoverageWeight',
      'surfaceDarkNoisePenalty',
      'surfaceStructureWeight',
      'surfaceDitherSuppression',
    ]) {
      const value = Number(this[name]);
      if (!Number.isFinite(value) || value < 0) throw new RangeError(`${name} must be a finite non-negative number`);
    }
    if (this.spriteAlphaThreshold > 1 || this.spriteThinFeatureThreshold > 1 || this.surfacePhaseWeight > 1 || this.surfaceDitherSuppression > 1) {
      throw new RangeError('threshold/fraction semantic options must not exceed 1');
    }
    this.tileAware = Boolean(this.tileAware);
    return this;
  }
}

function normalizeSemanticOptions(options) {
  return options instanceof SemanticOptions ? options : new SemanticOptions(options ?? {});
}

function validateImage(image) {
  if (!image || !Number.isInteger(image.width) || !Number.isInteger(image.height)) {
    throw new TypeError('image must have integer width and height properties');
  }
  if (image.width <= 0 || image.height <= 0) throw new RangeError('image dimensions must be positive');
  if (!(image.data instanceof Uint8Array) && !(image.data instanceof Uint8ClampedArray)) {
    throw new TypeError('image.data must be a Uint8Array or Uint8ClampedArray containing RGBA bytes');
  }
  if (image.data.length !== image.width * image.height * 4) {
    throw new RangeError(`image.data must contain exactly ${image.width * image.height * 4} RGBA bytes`);
  }
}

function validateTargetSize(image, size) {
  if (!Array.isArray(size) || size.length !== 2) throw new TypeError('size must be a [width, height] pair');
  const width = Number(size[0]);
  const height = Number(size[1]);
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
    throw new RangeError(`target dimensions must be positive integers, got ${size}`);
  }
  if (width > image.width || height > image.height) {
    throw new RangeError(`invalid downscale target ${width}x${height} for source ${image.width}x${image.height}`);
  }
  return [width, height];
}

function cloneImage(image) {
  return { width: image.width, height: image.height, data: new Uint8ClampedArray(image.data) };
}

function pixelIndex(width, x, y) {
  return y * width + x;
}

function nearestResize(image, size) {
  const [targetWidth, targetHeight] = validateTargetSize(image, size);
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);
  for (let ty = 0; ty < targetHeight; ty += 1) {
    const sy = Math.min(image.height - 1, Math.trunc((ty + 0.5) * image.height / targetHeight));
    for (let tx = 0; tx < targetWidth; tx += 1) {
      const sx = Math.min(image.width - 1, Math.trunc((tx + 0.5) * image.width / targetWidth));
      const sourceOffset = pixelIndex(image.width, sx, sy) * 4;
      const targetOffset = pixelIndex(targetWidth, tx, ty) * 4;
      output[targetOffset] = image.data[sourceOffset];
      output[targetOffset + 1] = image.data[sourceOffset + 1];
      output[targetOffset + 2] = image.data[sourceOffset + 2];
      output[targetOffset + 3] = image.data[sourceOffset + 3];
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

function shiftScalar(array, width, height, dy, dx, wrap) {
  const output = new Float64Array(array.length);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let sourceX = x - dx;
      let sourceY = y - dy;
      if (wrap) {
        sourceX = ((sourceX % width) + width) % width;
        sourceY = ((sourceY % height) + height) % height;
      } else {
        sourceX = Math.max(0, Math.min(width - 1, sourceX));
        sourceY = Math.max(0, Math.min(height - 1, sourceY));
      }
      output[pixelIndex(width, x, y)] = array[pixelIndex(width, sourceX, sourceY)];
    }
  }
  return output;
}

function box3(array, width, height, wrap) {
  const output = new Float64Array(array.length);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let sum = 0;
      for (let dy = -1; dy <= 1; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          let sx = x + dx;
          let sy = y + dy;
          if (wrap) {
            sx = ((sx % width) + width) % width;
            sy = ((sy % height) + height) % height;
          } else {
            sx = Math.max(0, Math.min(width - 1, sx));
            sy = Math.max(0, Math.min(height - 1, sy));
          }
          sum += array[pixelIndex(width, sx, sy)];
        }
      }
      output[pixelIndex(width, x, y)] = sum / 9.0;
    }
  }
  return output;
}

function featureMaps(image, tileAware) {
  const { width, height, data } = image;
  const count = width * height;
  const alpha = new Float64Array(count);
  const opaque = new Uint8Array(count);
  const luminance = new Float64Array(count);
  let opaqueCount = 0;

  for (let i = 0; i < count; i += 1) {
    const p = i * 4;
    const a = data[p + 3] / 255.0;
    alpha[i] = a;
    const isOpaque = a > (1.0 / 255.0);
    opaque[i] = isOpaque ? 1 : 0;
    if (isOpaque) opaqueCount += 1;
    luminance[i] = 0.2126 * (data[p] / 255.0) + 0.7152 * (data[p + 1] / 255.0) + 0.0722 * (data[p + 2] / 255.0);
  }

  const wrap = Boolean(tileAware && opaqueCount / count > 0.98);
  const left = shiftScalar(luminance, width, height, 0, -1, wrap);
  const right = shiftScalar(luminance, width, height, 0, 1, wrap);
  const up = shiftScalar(luminance, width, height, -1, 0, wrap);
  const down = shiftScalar(luminance, width, height, 1, 0, wrap);
  const gx = new Float64Array(count);
  const gy = new Float64Array(count);
  const gx2 = new Float64Array(count);
  const gy2 = new Float64Array(count);
  const gxy = new Float64Array(count);
  for (let i = 0; i < count; i += 1) {
    gx[i] = 0.5 * (right[i] - left[i]);
    gy[i] = 0.5 * (down[i] - up[i]);
    gx2[i] = gx[i] * gx[i];
    gy2[i] = gy[i] * gy[i];
    gxy[i] = gx[i] * gy[i];
  }

  const jxx = box3(gx2, width, height, wrap);
  const jyy = box3(gy2, width, height, wrap);
  const jxy = box3(gxy, width, height, wrap);
  const lum2 = new Float64Array(count);
  for (let i = 0; i < count; i += 1) lum2[i] = luminance[i] * luminance[i];
  const mean = box3(luminance, width, height, wrap);
  const mean2 = box3(lum2, width, height, wrap);

  const left2 = shiftScalar(luminance, width, height, 0, -2, wrap);
  const right2 = shiftScalar(luminance, width, height, 0, 2, wrap);
  const up2 = shiftScalar(luminance, width, height, -2, 0, wrap);
  const down2 = shiftScalar(luminance, width, height, 2, 0, wrap);

  const structure = new Float64Array(count);
  const texture = new Float64Array(count);
  const dither = new Float64Array(count);
  for (let i = 0; i < count; i += 1) {
    if (!opaque[i]) continue;
    const coherence = Math.sqrt((jxx[i] - jyy[i]) ** 2 + 4.0 * jxy[i] ** 2) / (jxx[i] + jyy[i] + 1e-9);
    const gradient = Math.sqrt(gx[i] * gx[i] + gy[i] * gy[i]);
    const oneStep = (
      Math.abs(luminance[i] - left[i]) + Math.abs(luminance[i] - right[i]) +
      Math.abs(luminance[i] - up[i]) + Math.abs(luminance[i] - down[i])
    ) / 4.0;
    const twoStep = (
      Math.abs(luminance[i] - left2[i]) + Math.abs(luminance[i] - right2[i]) +
      Math.abs(luminance[i] - up2[i]) + Math.abs(luminance[i] - down2[i])
    ) / 4.0;
    const recurrence = Math.max(0.0, Math.min(1.0, 1.0 - 4.0 * twoStep));
    dither[i] = Math.max(0.0, Math.min(1.0, 4.0 * oneStep)) * recurrence * (1.0 - 0.55 * coherence);
    const variance = Math.max(0.0, mean2[i] - mean[i] * mean[i]);
    texture[i] = Math.max(0.0, Math.min(1.0, 4.0 * Math.sqrt(variance)));
    structure[i] = Math.max(0.0, Math.min(1.0, 5.0 * gradient)) * coherence * (1.0 - 0.80 * dither[i]);
  }
  return { alpha, opaque, luminance, structure, texture, dither, opaqueRatio: opaqueCount / count };
}

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
  if (!count) return { fill: 0.0, areaRatio: 0.0, touches: 0 };
  const bboxArea = Math.max(1, (x1 - x0) * (y1 - y0));
  return {
    fill: count / bboxArea,
    areaRatio: bboxArea / (width * height),
    touches: Number(top) + Number(bottom) + Number(left) + Number(right),
  };
}

export function analyze(image, options = undefined) {
  validateImage(image);
  const normalized = normalizeSemanticOptions(options);
  const maps = featureMaps(image, normalized.tileAware);
  const bbox = bboxStats(maps.opaque, image.width, image.height);
  let mode;
  if (normalized.mode !== SemanticMode.AUTO) mode = normalized.mode;
  else if (normalized.contentHint === ContentHint.ITEM) mode = SemanticMode.SPRITE;
  else if (normalized.contentHint === ContentHint.BLOCK) mode = maps.opaqueRatio > 0.98 ? SemanticMode.SURFACE : SemanticMode.PATTERN;
  else if (normalized.contentHint === ContentHint.ENTITY) mode = maps.opaqueRatio > 0.98 ? SemanticMode.SURFACE : SemanticMode.SPRITE;
  else if (maps.opaqueRatio > 0.94) mode = SemanticMode.SURFACE;
  else if (bbox.areaRatio > 0.82 && bbox.touches >= 2 && bbox.fill < 0.72) mode = SemanticMode.PATTERN;
  else mode = SemanticMode.SPRITE;

  return {
    rgba: image.data,
    width: image.width,
    height: image.height,
    alpha: maps.alpha,
    opaque: maps.opaque,
    luminance: maps.luminance,
    structure: maps.structure,
    texture: maps.texture,
    dither: maps.dither,
    opaqueRatio: maps.opaqueRatio,
    bboxFillRatio: bbox.fill,
    bboxAreaRatio: bbox.areaRatio,
    edgeTouchCount: bbox.touches,
    mode,
  };
}

function rgbToOklab(r, g, b) {
  let rr = r / 255.0;
  let gg = g / 255.0;
  let bb = b / 255.0;
  rr = rr <= 0.04045 ? rr / 12.92 : ((rr + 0.055) / 1.055) ** 2.4;
  gg = gg <= 0.04045 ? gg / 12.92 : ((gg + 0.055) / 1.055) ** 2.4;
  bb = bb <= 0.04045 ? bb / 12.92 : ((bb + 0.055) / 1.055) ** 2.4;
  const l = Math.cbrt(0.4122214708 * rr + 0.5363325363 * gg + 0.0514459929 * bb);
  const m = Math.cbrt(0.2119034982 * rr + 0.6806995451 * gg + 0.1073969566 * bb);
  const s = Math.cbrt(0.0883024619 * rr + 0.2817188376 * gg + 0.6299787005 * bb);
  return [
    0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
  ];
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

export function spriteDownscale(image, size, options = undefined) {
  const normalized = normalizeSemanticOptions(options);
  return downscale(image, size, {
    alphaThreshold: normalized.spriteAlphaThreshold,
    thinFeatureThreshold: normalized.spriteThinFeatureThreshold,
    preserveThinFeatures: true,
    preserveOutline: true,
    preserveInternalEdges: true,
    internalEdgeWeight: 0.0,
  });
}

export function surfaceDownscale(analysis, size, options = undefined) {
  const normalized = normalizeSemanticOptions(options);
  const sourceWidth = analysis.width;
  const sourceHeight = analysis.height;
  const [targetWidth, targetHeight] = size;
  const xCells = axisCells(sourceWidth, targetWidth);
  const yCells = axisCells(sourceHeight, targetHeight);
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);
  let binaryAlpha = true;
  for (let i = 3; i < analysis.rgba.length; i += 4) {
    const a = analysis.rgba[i];
    if (a !== 0 && a !== 255) { binaryAlpha = false; break; }
  }

  for (let ty = 0; ty < targetHeight; ty += 1) {
    const yCell = yCells[ty];
    for (let tx = 0; tx < targetWidth; tx += 1) {
      const xCell = xCells[tx];
      const groups = new Map();
      const labValues = [];
      const labWeights = [];
      const structureValues = [];
      const textureValues = [];
      const ditherValues = [];
      let weightSum = 0;
      let alphaCoverageSum = 0;
      let areaSum = 0;

      for (let yi = 0; yi < yCell.indices.length; yi += 1) {
        const sy = yCell.indices[yi];
        for (let xi = 0; xi < xCell.indices.length; xi += 1) {
          const sx = xCell.indices[xi];
          const weight = yCell.weights[yi] * xCell.weights[xi];
          areaSum += weight;
          const index = pixelIndex(sourceWidth, sx, sy);
          const alpha = analysis.alpha[index];
          alphaCoverageSum += weight * alpha;
          const effective = weight * alpha;
          if (!(effective > 0)) continue;
          const p = index * 4;
          const r = analysis.rgba[p];
          const g = analysis.rgba[p + 1];
          const b = analysis.rgba[p + 2];
          const code = (r << 16) | (g << 8) | b;
          const lab = rgbToOklab(r, g, b);
          labValues.push(lab);
          labWeights.push(effective);
          structureValues.push(analysis.structure[index]);
          textureValues.push(analysis.texture[index]);
          ditherValues.push(analysis.dither[index]);
          weightSum += effective;
          let group = groups.get(code);
          if (!group) {
            group = { code, r, g, b, lab, coverageWeight: 0, structureWeight: 0 };
            groups.set(code, group);
          }
          group.coverageWeight += effective;
          group.structureWeight += effective * analysis.structure[index];
        }
      }

      if (!(weightSum > 0) || groups.size === 0) continue;
      const desired = [0, 0, 0];
      for (let i = 0; i < labValues.length; i += 1) {
        desired[0] += labValues[i][0] * labWeights[i];
        desired[1] += labValues[i][1] * labWeights[i];
        desired[2] += labValues[i][2] * labWeights[i];
      }
      desired[0] /= weightSum;
      desired[1] /= weightSum;
      desired[2] /= weightSum;

      let cellStructure = 0;
      let cellTexture = 0;
      let cellDither = 0;
      for (let i = 0; i < labWeights.length; i += 1) {
        cellStructure += structureValues[i] * labWeights[i];
        cellTexture += textureValues[i] * labWeights[i];
        cellDither += ditherValues[i] * labWeights[i];
      }
      cellStructure /= weightSum;
      cellTexture /= weightSum;
      cellDither /= weightSum;

      const sx = Math.min(sourceWidth - 1, Math.trunc((tx + 0.5) * sourceWidth / targetWidth));
      const sy = Math.min(sourceHeight - 1, Math.trunc((ty + 0.5) * sourceHeight / targetHeight));
      const anchorP = pixelIndex(sourceWidth, sx, sy) * 4;
      const anchorR = analysis.rgba[anchorP];
      const anchorG = analysis.rgba[anchorP + 1];
      const anchorB = analysis.rgba[anchorP + 2];
      const anchorCode = (anchorR << 16) | (anchorG << 8) | anchorB;
      const anchorLab = rgbToOklab(anchorR, anchorG, anchorB);
      desired[0] = (1.0 - normalized.surfacePhaseWeight) * desired[0] + normalized.surfacePhaseWeight * anchorLab[0];
      desired[1] = (1.0 - normalized.surfacePhaseWeight) * desired[1] + normalized.surfacePhaseWeight * anchorLab[1];
      desired[2] = (1.0 - normalized.surfacePhaseWeight) * desired[2] + normalized.surfacePhaseWeight * anchorLab[2];

      const lightness = labValues.map((lab) => lab[0]);
      lightness.sort((a, b) => a - b);
      const middle = Math.floor(lightness.length / 2);
      const medianLightness = lightness.length % 2 ? lightness[middle] : 0.5 * (lightness[middle - 1] + lightness[middle]);
      let best = null;
      let bestScore = Infinity;
      const candidates = [...groups.values()].sort((a, b) => a.code - b.code);
      for (const group of candidates) {
        const coverage = group.coverageWeight / weightSum;
        const structureSupport = group.structureWeight / weightSum;
        const dL = group.lab[0] - desired[0];
        const da = group.lab[1] - desired[1];
        const db = group.lab[2] - desired[2];
        let score = Math.sqrt(1.35 * dL * dL + da * da + db * db);
        score -= normalized.surfaceCoverageWeight * coverage;
        if (group.code === anchorCode) score -= normalized.surfaceAnchorWeight;
        const coherent = cellStructure * (1.0 - normalized.surfaceDitherSuppression * cellDither);
        score -= normalized.surfaceStructureWeight * coherent * structureSupport;
        const darkness = Math.max(0.0, medianLightness - group.lab[0]);
        score += normalized.surfaceDarkNoisePenalty * cellTexture * (1.0 - cellStructure) * (1.0 - coverage) * darkness;
        if (score < bestScore) {
          bestScore = score;
          best = group;
        }
      }

      const targetP = pixelIndex(targetWidth, tx, ty) * 4;
      output[targetP] = best.r;
      output[targetP + 1] = best.g;
      output[targetP + 2] = best.b;
      const alphaCoverage = alphaCoverageSum / Math.max(areaSum, 1e-12);
      output[targetP + 3] = binaryAlpha && alphaCoverage >= 0.5
        ? 255
        : Math.max(0, Math.min(255, Math.round(alphaCoverage * 255.0)));
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

export function inferContentHint(sourcePath) {
  if (typeof sourcePath !== 'string') return ContentHint.AUTO;
  const normalized = sourcePath.replaceAll('\\', '/').toLowerCase();
  if (normalized.includes('/textures/item/')) return ContentHint.ITEM;
  if (normalized.includes('/textures/block/')) return ContentHint.BLOCK;
  if (normalized.includes('/textures/entity/')) return ContentHint.ENTITY;
  return ContentHint.AUTO;
}

export function downscaleSemantic(image, size, options = undefined) {
  validateImage(image);
  const normalized = normalizeSemanticOptions(options);
  const target = validateTargetSize(image, size);
  if (target[0] === image.width && target[1] === image.height) return cloneImage(image);
  const analysis = analyze(image, normalized);
  if (analysis.mode === SemanticMode.PATTERN) return nearestResize(image, target);
  if (analysis.mode === SemanticMode.SPRITE) return spriteDownscale(image, target, normalized);
  return surfaceDownscale(analysis, target, normalized);
}

export function downscaleSemanticByFactor(image, factor = 2.0, options = undefined) {
  validateImage(image);
  if (!Number.isFinite(factor) || factor < 1.0) throw new RangeError('factor must be a finite value of at least 1');
  return downscaleSemantic(image, [Math.max(1, Math.floor(image.width / factor)), Math.max(1, Math.floor(image.height / factor))], options);
}

export { nearestResize, normalizeSemanticOptions, validateImage, validateTargetSize, pixelIndex };
