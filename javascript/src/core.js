import { DownscaleOptions, normalizeOptions } from './options.js';

const f32 = Math.fround;

function validateImage(image) {
  if (!image || !Number.isInteger(image.width) || !Number.isInteger(image.height)) {
    throw new TypeError('image must have integer width and height properties');
  }
  if (image.width <= 0 || image.height <= 0) {
    throw new RangeError('image dimensions must be positive');
  }
  if (!(image.data instanceof Uint8Array) && !(image.data instanceof Uint8ClampedArray)) {
    throw new TypeError('image.data must be a Uint8Array or Uint8ClampedArray containing RGBA bytes');
  }
  const expected = image.width * image.height * 4;
  if (image.data.length !== expected) {
    throw new RangeError(`image.data must contain exactly ${expected} RGBA bytes`);
  }
}

function validateTargetSize(image, size) {
  if (!Array.isArray(size) || size.length !== 2) {
    throw new TypeError('size must be a [width, height] pair');
  }
  const width = Number(size[0]);
  const height = Number(size[1]);
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
    throw new RangeError(`target dimensions must be positive integers, got ${size}`);
  }
  if (width > image.width || height > image.height) {
    throw new RangeError(
      `BetterPixelArtDownscale only downsizes images; source is ${image.width}x${image.height}, target is ${width}x${height}`,
    );
  }
  return [width, height];
}

function pixelIndex(width, x, y) {
  return y * width + x;
}

function packRgba(r, g, b, a) {
  return ((((r << 24) >>> 0) | (g << 16) | (b << 8) | a) >>> 0);
}

function unpackRgba(code) {
  return [
    (code >>> 24) & 0xff,
    (code >>> 16) & 0xff,
    (code >>> 8) & 0xff,
    code & 0xff,
  ];
}

function prepareSource(image, options) {
  const { width, height, data } = image;
  const count = width * height;
  const alpha = new Float32Array(count);
  const opaque = new Uint8Array(count);
  const outline = new Uint8Array(count);
  const internalEdge = new Float32Array(count);
  const codes = new Uint32Array(count);
  let binaryAlpha = true;
  let hasTransparent = false;

  for (let i = 0; i < count; i += 1) {
    const p = i * 4;
    const aByte = data[p + 3];
    const a = f32(aByte / 255.0);
    alpha[i] = a;
    const isOpaque = a >= options.sourceAlphaThreshold;
    opaque[i] = isOpaque ? 1 : 0;
    if (!isOpaque) hasTransparent = true;
    if (aByte !== 0 && aByte !== 255) binaryAlpha = false;
    codes[i] = packRgba(data[p], data[p + 1], data[p + 2], aByte);
  }

  if (hasTransparent) {
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const i = pixelIndex(width, x, y);
        if (!opaque[i]) continue;
        const up = y > 0 && opaque[pixelIndex(width, x, y - 1)];
        const down = y + 1 < height && opaque[pixelIndex(width, x, y + 1)];
        const left = x > 0 && opaque[pixelIndex(width, x - 1, y)];
        const right = x + 1 < width && opaque[pixelIndex(width, x + 1, y)];
        outline[i] = up && down && left && right ? 0 : 1;
      }
    }
  }

  const neighborDirs = [[0, -1], [0, 1], [-1, 0], [1, 0]];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = pixelIndex(width, x, y);
      if (!opaque[i]) continue;
      const p = i * 4;
      const r = f32(data[p] / 255.0);
      const g = f32(data[p + 1] / 255.0);
      const b = f32(data[p + 2] / 255.0);
      let maxDistance = 0;
      for (const [dx, dy] of neighborDirs) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
        const ni = pixelIndex(width, nx, ny);
        if (!opaque[ni]) continue;
        const np = ni * 4;
        const dr = f32(r - f32(data[np] / 255.0));
        const dg = f32(g - f32(data[np + 1] / 255.0));
        const db = f32(b - f32(data[np + 2] / 255.0));
        const rr = f32(dr * dr);
        const gg = f32(dg * dg);
        const bb = f32(db * db);
        const weighted = f32(f32(0.30 * rr) + f32(0.59 * gg) + f32(0.11 * bb));
        const distance = f32(Math.sqrt(weighted));
        if (distance > maxDistance) maxDistance = distance;
      }
      internalEdge[i] = maxDistance >= options.internalEdgeThreshold ? f32(maxDistance) : 0;
    }
  }

  return { width, height, data, alpha, opaque, outline, internalEdge, codes, binaryAlpha };
}

function axisCells(sourceLength, targetLength) {
  const cells = [];
  const scale = sourceLength / targetLength;
  for (let targetIndex = 0; targetIndex < targetLength; targetIndex += 1) {
    const start = targetIndex * scale;
    const end = (targetIndex + 1) * scale;
    const first = Math.floor(start);
    const last = Math.ceil(end);
    const indices = [];
    const weights = [];
    for (let index = first; index < last; index += 1) {
      const left = Math.max(index, start);
      const right = Math.min(index + 1.0, end);
      indices.push(index);
      weights.push(f32(Math.max(0.0, right - left)));
    }
    cells.push({ indices, weights });
  }
  return cells;
}

function makeCell(xData, yData) {
  const weights = new Float32Array(xData.indices.length * yData.indices.length);
  let sum = f32(0);
  let k = 0;
  for (let yi = 0; yi < yData.weights.length; yi += 1) {
    for (let xi = 0; xi < xData.weights.length; xi += 1) {
      const w = f32(yData.weights[yi] * xData.weights[xi]);
      weights[k++] = w;
      sum = f32(sum + w);
    }
  }
  return { xIndices: xData.indices, yIndices: yData.indices, weights, area: Number(sum) };
}

function centerSample(source, targetX, targetY, targetWidth, targetHeight) {
  const x = Math.min(source.width - 1, Math.trunc((targetX + 0.5) * source.width / targetWidth));
  const y = Math.min(source.height - 1, Math.trunc((targetY + 0.5) * source.height / targetHeight));
  return Boolean(source.opaque[pixelIndex(source.width, x, y)]);
}

function destinationBoundary(occupancy, width, height) {
  const boundary = new Uint8Array(width * height);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = pixelIndex(width, x, y);
      if (!occupancy[i]) continue;
      const up = y > 0 && occupancy[pixelIndex(width, x, y - 1)];
      const down = y + 1 < height && occupancy[pixelIndex(width, x, y + 1)];
      const left = x > 0 && occupancy[pixelIndex(width, x - 1, y)];
      const right = x + 1 < width && occupancy[pixelIndex(width, x + 1, y)];
      boundary[i] = up && down && left && right ? 0 : 1;
    }
  }
  return boundary;
}

function chooseColor(source, cell, isBoundary, options) {
  const grouped = new Map();
  let wi = 0;
  for (const y of cell.yIndices) {
    for (const x of cell.xIndices) {
      const i = pixelIndex(source.width, x, y);
      const effectiveWeight = Number(f32(cell.weights[wi++] * source.alpha[i]));
      if (!(effectiveWeight > 0)) continue;
      const code = source.codes[i] >>> 0;
      let group = grouped.get(code);
      if (!group) {
        group = { code, coverage: 0, outlineSupport: 0, edgeSupport: 0 };
        grouped.set(code, group);
      }
      group.coverage += effectiveWeight;
      if (source.outline[i]) group.outlineSupport += effectiveWeight;
      if (source.internalEdge[i]) group.edgeSupport += effectiveWeight * source.internalEdge[i];
    }
  }

  if (grouped.size === 0) return [0, 0, 0, 0];
  const groups = [...grouped.values()].sort((a, b) => (a.code >>> 0) - (b.code >>> 0));

  let restrictToOutline = false;
  if (isBoundary && options.preserveOutline) {
    let outlineTotal = 0;
    for (const g of groups) outlineTotal += g.outlineSupport;
    restrictToOutline = outlineTotal / Math.max(cell.area, 1e-12) >= options.outlineMinCoverage;
  }

  const scores = groups.map((g) => {
    if (restrictToOutline && !(g.outlineSupport > 0)) return -Infinity;
    let score = g.coverage;
    if (options.preserveInternalEdges) score += options.internalEdgeWeight * g.edgeSupport;
    if (isBoundary && options.preserveOutline) score += g.outlineSupport;
    return score;
  });
  const bestScore = Math.max(...scores);
  const contenders = [];
  for (let index = 0; index < scores.length; index += 1) {
    if (isClose(scores[index], bestScore)) contenders.push(index);
  }

  let bestIndex = contenders[0];
  if (contenders.length > 1) {
    for (let j = 1; j < contenders.length; j += 1) {
      const candidate = contenders[j];
      if (compareTieKey(groups[candidate], groups[bestIndex], isBoundary) > 0) bestIndex = candidate;
    }
  }
  return unpackRgba(groups[bestIndex].code);
}

function isClose(a, b) {
  if (!Number.isFinite(a) || !Number.isFinite(b)) return a === b;
  return Math.abs(a - b) <= (1e-12 + 1e-10 * Math.abs(b));
}

function compareTieKey(a, b, isBoundary) {
  if (a.coverage !== b.coverage) return a.coverage > b.coverage ? 1 : -1;
  const aEdge = a.outlineSupport + a.edgeSupport;
  const bEdge = b.outlineSupport + b.edgeSupport;
  if (aEdge !== bEdge) return aEdge > bEdge ? 1 : -1;
  const [ar, ag, ab] = unpackRgba(a.code);
  const [br, bg, bb] = unpackRgba(b.code);
  const aLum = 0.2126 * ar + 0.7152 * ag + 0.0722 * ab;
  const bLum = 0.2126 * br + 0.7152 * bg + 0.0722 * bb;
  const aDark = isBoundary ? -aLum : aLum;
  const bDark = isBoundary ? -bLum : bLum;
  if (aDark !== bDark) return aDark > bDark ? 1 : -1;
  const aCodeKey = -(a.code >>> 0);
  const bCodeKey = -(b.code >>> 0);
  if (aCodeKey === bCodeKey) return 0;
  return aCodeKey > bCodeKey ? 1 : -1;
}

function buildMaps(source, targetSize, options) {
  const [targetWidth, targetHeight] = targetSize;
  const xCells = axisCells(source.width, targetWidth);
  const yCells = axisCells(source.height, targetHeight);
  const cells = Array.from({ length: targetHeight }, () => Array(targetWidth));
  const alphaCoverage = new Float32Array(targetWidth * targetHeight);
  const internalSupport = new Float32Array(targetWidth * targetHeight);

  for (let targetY = 0; targetY < targetHeight; targetY += 1) {
    for (let targetX = 0; targetX < targetWidth; targetX += 1) {
      const cell = makeCell(xCells[targetX], yCells[targetY]);
      cells[targetY][targetX] = cell;
      let alphaSum = f32(0);
      let internalSum = f32(0);
      let wi = 0;
      for (const y of cell.yIndices) {
        for (const x of cell.xIndices) {
          const i = pixelIndex(source.width, x, y);
          const weight = cell.weights[wi++];
          alphaSum = f32(alphaSum + f32(weight * source.alpha[i]));
          internalSum = f32(internalSum + f32(weight * source.internalEdge[i]));
        }
      }
      const di = pixelIndex(targetWidth, targetX, targetY);
      alphaCoverage[di] = f32(alphaSum / Math.max(cell.area, 1e-12));
      internalSupport[di] = f32(internalSum / Math.max(cell.area, 1e-12));
    }
  }

  const occupancy = new Uint8Array(targetWidth * targetHeight);
  for (let i = 0; i < occupancy.length; i += 1) {
    occupancy[i] = alphaCoverage[i] >= options.alphaThreshold ? 1 : 0;
  }

  if (options.preserveThinFeatures) {
    for (let targetY = 0; targetY < targetHeight; targetY += 1) {
      for (let targetX = 0; targetX < targetWidth; targetX += 1) {
        const i = pixelIndex(targetWidth, targetX, targetY);
        if (occupancy[i]) continue;
        if (alphaCoverage[i] < options.thinFeatureThreshold) continue;
        occupancy[i] = centerSample(source, targetX, targetY, targetWidth, targetHeight) ? 1 : 0;
      }
    }
  }

  const boundary = destinationBoundary(occupancy, targetWidth, targetHeight);
  return { cells, alphaCoverage, occupancy, boundary, internalSupport };
}

function buildOutput(source, targetSize, maps, options) {
  const [targetWidth, targetHeight] = targetSize;
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);
  const useBinaryAlpha = options.binaryAlpha === null ? source.binaryAlpha : options.binaryAlpha;

  for (let targetY = 0; targetY < targetHeight; targetY += 1) {
    for (let targetX = 0; targetX < targetWidth; targetX += 1) {
      const i = pixelIndex(targetWidth, targetX, targetY);
      if (!maps.occupancy[i]) continue;
      const color = chooseColor(source, maps.cells[targetY][targetX], Boolean(maps.boundary[i]), options);
      const p = i * 4;
      output[p] = color[0];
      output[p + 1] = color[1];
      output[p + 2] = color[2];
      if (useBinaryAlpha) {
        output[p + 3] = 255;
      } else {
        const a = Math.min(255, Math.max(1, Math.round(Number(maps.alphaCoverage[i]) * 255.0)));
        output[p + 3] = a;
      }
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

export function downscale(image, size, options = undefined) {
  validateImage(image);
  const normalized = normalizeOptions(options);
  const targetSize = validateTargetSize(image, size);
  if (targetSize[0] === image.width && targetSize[1] === image.height) {
    return { width: image.width, height: image.height, data: new Uint8ClampedArray(image.data) };
  }
  const source = prepareSource(image, normalized);
  const maps = buildMaps(source, targetSize, normalized);
  return buildOutput(source, targetSize, maps, normalized);
}

export function downscaleByFactor(image, factorX, factorY = factorX, options = undefined) {
  validateImage(image);
  if (!(factorX >= 1) || !(factorY >= 1)) {
    throw new RangeError('downscale factors must be at least 1.0');
  }
  const width = Math.max(1, Math.floor(image.width / factorX));
  const height = Math.max(1, Math.floor(image.height / factorY));
  return downscale(image, [width, height], options);
}

export function edgeLayer(image, size, options = undefined, edgeOptions = {}) {
  validateImage(image);
  const normalized = normalizeOptions(options);
  const includeOutline = edgeOptions.includeOutline ?? edgeOptions.include_outline ?? true;
  const includeInternalEdges = edgeOptions.includeInternalEdges ?? edgeOptions.include_internal_edges ?? true;
  const targetSize = validateTargetSize(image, size);
  const source = prepareSource(image, normalized);
  const maps = buildMaps(source, targetSize, normalized);
  const [targetWidth, targetHeight] = targetSize;
  const output = new Uint8ClampedArray(targetWidth * targetHeight * 4);

  for (let y = 0; y < targetHeight; y += 1) {
    for (let x = 0; x < targetWidth; x += 1) {
      const i = pixelIndex(targetWidth, x, y);
      if (!maps.occupancy[i]) continue;
      const isOutline = includeOutline && Boolean(maps.boundary[i]);
      const isInternal = includeInternalEdges && maps.internalSupport[i] >= normalized.internalEdgeThreshold;
      if (!(isOutline || isInternal)) continue;
      const color = chooseColor(source, maps.cells[y][x], isOutline, normalized);
      const p = i * 4;
      output[p] = color[0];
      output[p + 1] = color[1];
      output[p + 2] = color[2];
      output[p + 3] = 255;
    }
  }
  return { width: targetWidth, height: targetHeight, data: output };
}

export function fromImageData(imageData) {
  return { width: imageData.width, height: imageData.height, data: new Uint8ClampedArray(imageData.data) };
}

export function toImageData(image) {
  validateImage(image);
  if (typeof ImageData === 'undefined') {
    throw new Error('ImageData is not available in this runtime');
  }
  return new ImageData(new Uint8ClampedArray(image.data), image.width, image.height);
}

export { DownscaleOptions };
