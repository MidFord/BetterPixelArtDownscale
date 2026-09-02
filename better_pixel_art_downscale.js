/*
 * Better Pixel Art Downscale for Blockbench
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Self-contained integration of MidFord/BetterPixelArtDownscale.
 */
(function() {
    'use strict';

    const PLUGIN_ID = 'better_pixel_art_downscale';
    const PLUGIN_VERSION = '1.0.0';
    const SETTINGS_KEY = 'better_pixel_art_downscale.resize_settings.v1';
    const CORE_REVISION = 'BetterPixelArtDownscale v2 / JS core 58766ae30f645af40762be0c46caace67db1d86b';

    let originalResizeDialog = null;
    let patchedResizeDialog = null;

    // ---------------------------------------------------------------------
    // Embedded BetterPixelArtDownscale v2 core
    // Source: https://github.com/MidFord/BetterPixelArtDownscale
    // Browser-safe, zero runtime dependencies.
    // ---------------------------------------------------------------------

    const BetterPixelArtDownscale = (() => {
        class DownscaleOptions {
            constructor(options = {}) {
                this.alphaThreshold = options.alphaThreshold ?? options.alpha_threshold ?? 0.50;
                this.sourceAlphaThreshold = options.sourceAlphaThreshold ?? options.source_alpha_threshold ?? (1.0 / 255.0);
                this.preserveThinFeatures = options.preserveThinFeatures ?? options.preserve_thin_features ?? true;
                this.thinFeatureThreshold = options.thinFeatureThreshold ?? options.thin_feature_threshold ?? 0.125;
                this.preserveOutline = options.preserveOutline ?? options.preserve_outline ?? true;
                this.preserveInternalEdges = options.preserveInternalEdges ?? options.preserve_internal_edges ?? true;
                this.outlineMinCoverage = options.outlineMinCoverage ?? options.outline_min_coverage ?? 0.02;
                this.internalEdgeThreshold = options.internalEdgeThreshold ?? options.internal_edge_threshold ?? 0.10;
                this.internalEdgeWeight = options.internalEdgeWeight ?? options.internal_edge_weight ?? 0.65;
                this.binaryAlpha = options.binaryAlpha ?? options.binary_alpha ?? null;
                this.validate();
            }

            validate() {
                for (const name of [
                    'alphaThreshold',
                    'sourceAlphaThreshold',
                    'thinFeatureThreshold',
                    'outlineMinCoverage',
                    'internalEdgeThreshold',
                ]) {
                    const value = this[name];
                    if (!(value >= 0 && value <= 1)) {
                        throw new RangeError(`${name} must be between 0 and 1, got ${value}`);
                    }
                }
                if (this.internalEdgeWeight < 0) {
                    throw new RangeError('internalEdgeWeight must be non-negative');
                }
                if (this.binaryAlpha !== null && typeof this.binaryAlpha !== 'boolean') {
                    throw new TypeError('binaryAlpha must be true, false, or null');
                }
                return this;
            }
        }

        function normalizeOptions(options) {
            return options instanceof DownscaleOptions ? options : new DownscaleOptions(options ?? {});
        }

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
                for (const group of groups) outlineTotal += group.outlineSupport;
                restrictToOutline = outlineTotal / Math.max(cell.area, 1e-12) >= options.outlineMinCoverage;
            }

            const scores = groups.map((group) => {
                if (restrictToOutline && !(group.outlineSupport > 0)) return -Infinity;
                let score = group.coverage;
                if (options.preserveInternalEdges) score += options.internalEdgeWeight * group.edgeSupport;
                if (isBoundary && options.preserveOutline) score += group.outlineSupport;
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
                        const alpha = Math.min(255, Math.max(1, Math.round(Number(maps.alphaCoverage[i]) * 255.0)));
                        output[p + 3] = alpha;
                    }
                }
            }
            return { width: targetWidth, height: targetHeight, data: output };
        }

        function downscale(image, size, options = undefined) {
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

        function downscaleByFactor(image, factorX, factorY = factorX, options = undefined) {
            validateImage(image);
            if (!(factorX >= 1) || !(factorY >= 1)) {
                throw new RangeError('downscale factors must be at least 1.0');
            }
            const width = Math.max(1, Math.floor(image.width / factorX));
            const height = Math.max(1, Math.floor(image.height / factorY));
            return downscale(image, [width, height], options);
        }

        function edgeLayer(image, size, options = undefined, edgeOptions = {}) {
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

        function fromImageData(imageData) {
            return { width: imageData.width, height: imageData.height, data: new Uint8ClampedArray(imageData.data) };
        }

        function toImageData(image) {
            validateImage(image);
            if (typeof ImageData === 'undefined') {
                throw new Error('ImageData is not available in this runtime');
            }
            return new ImageData(new Uint8ClampedArray(image.data), image.width, image.height);
        }

        return {
            DownscaleOptions,
            downscale,
            downscaleByFactor,
            edgeLayer,
            fromImageData,
            toImageData,
        };
    })();

    const DEFAULT_SETTINGS = Object.freeze({
        method: 'better_pixel_art',
        advanced: false,
        alphaThreshold: 0.50,
        sourceAlphaThreshold: 1.0 / 255.0,
        preserveThinFeatures: true,
        thinFeatureThreshold: 0.125,
        preserveOutline: true,
        preserveInternalEdges: true,
        outlineMinCoverage: 0.02,
        internalEdgeThreshold: 0.10,
        internalEdgeWeight: 0.65,
        binaryAlpha: 'auto',
    });

    function addTranslations() {
        if (typeof Language === 'undefined' || typeof Language.addTranslations !== 'function') return;
        Language.addTranslations('en', {
            'bpad.resize.method': 'Downscale Method',
            'bpad.resize.method.better': 'Better Pixel Art',
            'bpad.resize.method.native': 'Native Nearest',
            'bpad.resize.advanced': 'Advanced BetterPixelArtDownscale Settings',
            'bpad.resize.preserve_thin': 'Preserve Thin Features',
            'bpad.resize.preserve_outline': 'Preserve Silhouette / Outline',
            'bpad.resize.preserve_internal': 'Preserve Internal Edges',
            'bpad.resize.alpha_threshold': 'Alpha Coverage Threshold',
            'bpad.resize.source_alpha_threshold': 'Source Alpha Threshold',
            'bpad.resize.thin_threshold': 'Thin Feature Threshold',
            'bpad.resize.outline_coverage': 'Outline Minimum Coverage',
            'bpad.resize.internal_threshold': 'Internal Edge Threshold',
            'bpad.resize.internal_weight': 'Internal Edge Weight',
            'bpad.resize.binary_alpha': 'Output Alpha',
            'bpad.resize.binary_alpha.auto': 'Auto',
            'bpad.resize.binary_alpha.binary': 'Force Binary',
            'bpad.resize.binary_alpha.coverage': 'Preserve Coverage',
            'bpad.message.fallback': 'Better Pixel Art downscale failed; Native Nearest was used instead.',
            'bpad.message.incompatible': 'Better Pixel Art Downscale could not patch Texture.resizeDialog in this Blockbench version.',
        });
    }

    function readSettings() {
        const result = Object.assign({}, DEFAULT_SETTINGS);
        try {
            if (typeof localStorage === 'undefined') return result;
            const raw = localStorage.getItem(SETTINGS_KEY);
            if (!raw) return result;
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== 'object') return result;
            Object.assign(result, parsed);

            if (!['better_pixel_art', 'native_nearest'].includes(result.method)) result.method = DEFAULT_SETTINGS.method;
            if (!['auto', 'binary', 'coverage'].includes(result.binaryAlpha)) result.binaryAlpha = DEFAULT_SETTINGS.binaryAlpha;
            result.advanced = !!result.advanced;
            result.preserveThinFeatures = result.preserveThinFeatures !== false;
            result.preserveOutline = result.preserveOutline !== false;
            result.preserveInternalEdges = result.preserveInternalEdges !== false;

            for (const key of [
                'alphaThreshold',
                'sourceAlphaThreshold',
                'thinFeatureThreshold',
                'outlineMinCoverage',
                'internalEdgeThreshold',
            ]) {
                const value = Number(result[key]);
                result[key] = Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : DEFAULT_SETTINGS[key];
            }
            const edgeWeight = Number(result.internalEdgeWeight);
            result.internalEdgeWeight = Number.isFinite(edgeWeight) && edgeWeight >= 0
                ? edgeWeight
                : DEFAULT_SETTINGS.internalEdgeWeight;
            return result;
        } catch (error) {
            console.warn('[Better Pixel Art Downscale] Could not read saved settings.', error);
            return result;
        }
    }

    function writeSettings(settings) {
        try {
            if (typeof localStorage === 'undefined') return;
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
        } catch (error) {
            console.warn('[Better Pixel Art Downscale] Could not persist resize settings.', error);
        }
    }

    function tr(key, fallback) {
        if (typeof tl !== 'function') return fallback || key;
        const translated = tl(key);
        return translated === key ? (fallback || key) : translated;
    }

    function finiteNumber(value, fallback) {
        const number = Number(value);
        return Number.isFinite(number) ? number : fallback;
    }

    function currentFrameCount(texture) {
        return Math.max(1, Math.round(finiteNumber(texture?.frameCount, 1)));
    }

    function currentFrameHeight(texture) {
        const value = finiteNumber(texture?.display_height, finiteNumber(texture?.height, 1));
        return Math.max(1, value);
    }

    function isAnimatedFormat() {
        return typeof Format !== 'undefined' && !!Format.animated_textures;
    }

    function isEligibleDownscale(texture, form) {
        if (!texture || !form || form.mode !== 'scale' || !Array.isArray(form.size)) return false;
        const targetWidth = finiteNumber(form.size[0], NaN);
        const targetFrameHeight = finiteNumber(form.size[1], NaN);
        const sourceWidth = finiteNumber(texture.width, NaN);
        const sourceFrameHeight = currentFrameHeight(texture);
        if (![targetWidth, targetFrameHeight, sourceWidth, sourceFrameHeight].every(Number.isFinite)) return false;
        if (targetWidth <= 0 || targetFrameHeight <= 0) return false;
        if (targetWidth > sourceWidth || targetFrameHeight > sourceFrameHeight) return false;
        if (!(targetWidth < sourceWidth || targetFrameHeight < sourceFrameHeight)) return false;

        if (isAnimatedFormat()) {
            const sourceFrames = currentFrameCount(texture);
            const targetFrames = Math.max(1, Math.round(finiteNumber(form.frames, sourceFrames)));
            if (targetFrames !== sourceFrames) return false;
        }
        return true;
    }

    function optionsFromForm(form) {
        const binaryAlpha = form._bpad_binary_alpha === 'binary'
            ? true
            : form._bpad_binary_alpha === 'coverage'
                ? false
                : null;

        return new BetterPixelArtDownscale.DownscaleOptions({
            alphaThreshold: finiteNumber(form._bpad_alpha_threshold, DEFAULT_SETTINGS.alphaThreshold),
            sourceAlphaThreshold: finiteNumber(form._bpad_source_alpha_threshold, DEFAULT_SETTINGS.sourceAlphaThreshold),
            preserveThinFeatures: form._bpad_preserve_thin !== false,
            thinFeatureThreshold: finiteNumber(form._bpad_thin_threshold, DEFAULT_SETTINGS.thinFeatureThreshold),
            preserveOutline: form._bpad_preserve_outline !== false,
            preserveInternalEdges: form._bpad_preserve_internal !== false,
            outlineMinCoverage: finiteNumber(form._bpad_outline_coverage, DEFAULT_SETTINGS.outlineMinCoverage),
            internalEdgeThreshold: finiteNumber(form._bpad_internal_threshold, DEFAULT_SETTINGS.internalEdgeThreshold),
            internalEdgeWeight: finiteNumber(form._bpad_internal_weight, DEFAULT_SETTINGS.internalEdgeWeight),
            binaryAlpha,
        });
    }

    function settingsFromForm(form, previousSettings) {
        return {
            method: form._bpad_method || previousSettings.method,
            advanced: !!form._bpad_advanced,
            alphaThreshold: finiteNumber(form._bpad_alpha_threshold, previousSettings.alphaThreshold),
            sourceAlphaThreshold: finiteNumber(form._bpad_source_alpha_threshold, previousSettings.sourceAlphaThreshold),
            preserveThinFeatures: form._bpad_preserve_thin !== false,
            thinFeatureThreshold: finiteNumber(form._bpad_thin_threshold, previousSettings.thinFeatureThreshold),
            preserveOutline: form._bpad_preserve_outline !== false,
            preserveInternalEdges: form._bpad_preserve_internal !== false,
            outlineMinCoverage: finiteNumber(form._bpad_outline_coverage, previousSettings.outlineMinCoverage),
            internalEdgeThreshold: finiteNumber(form._bpad_internal_threshold, previousSettings.internalEdgeThreshold),
            internalEdgeWeight: finiteNumber(form._bpad_internal_weight, previousSettings.internalEdgeWeight),
            binaryAlpha: form._bpad_binary_alpha || previousSettings.binaryAlpha,
        };
    }

    function putDownscaledImage(destCtx, sourceImageData, targetWidth, targetHeight, options, destX = 0, destY = 0) {
        const source = BetterPixelArtDownscale.fromImageData(sourceImageData);
        const output = BetterPixelArtDownscale.downscale(source, [targetWidth, targetHeight], options);
        const imageData = destCtx.createImageData(output.width, output.height);
        imageData.data.set(output.data);
        destCtx.putImageData(imageData, destX, destY);
    }

    function renderPixelArtDownscale({
        sourceCtx,
        destCtx,
        sourceWidth,
        sourceHeight,
        targetWidth,
        targetHeight,
        options,
        frameAware,
        sourceFrames,
        targetFrames,
    }) {
        const canSplitFrames = frameAware &&
            sourceFrames > 1 &&
            sourceFrames === targetFrames &&
            sourceHeight % sourceFrames === 0 &&
            targetHeight % targetFrames === 0;

        if (!canSplitFrames) {
            const imageData = sourceCtx.getImageData(0, 0, sourceWidth, sourceHeight);
            putDownscaledImage(destCtx, imageData, targetWidth, targetHeight, options);
            return;
        }

        const sourceFrameHeight = sourceHeight / sourceFrames;
        const targetFrameHeight = targetHeight / targetFrames;
        for (let frame = 0; frame < sourceFrames; frame += 1) {
            const sourceImageData = sourceCtx.getImageData(
                0,
                frame * sourceFrameHeight,
                sourceWidth,
                sourceFrameHeight,
            );
            putDownscaledImage(
                destCtx,
                sourceImageData,
                targetWidth,
                targetFrameHeight,
                options,
                0,
                frame * targetFrameHeight,
            );
        }
    }

    function enhancedResizeDialog() {
        const scope = this;
        const saved = readSettings();
        let updatedToRepeat = false;

        const dialog = new Dialog({
            id: 'resize_texture',
            title: 'action.resize_texture',
            form: {
                mode: {label: 'dialog.resize_texture.mode', type: 'inline_select', default: 'crop', options: {
                    crop: 'dialog.resize_texture.mode.crop',
                    scale: 'dialog.resize_texture.mode.scale',
                }},
                size: {
                    label: 'dialog.project.texture_size',
                    type: 'vector',
                    dimensions: 2,
                    linked_ratio: false,
                    value: [this.width, this.display_height],
                    step: 1,
                    force_step: true,
                    min: 1,
                },
                frames: {
                    label: 'dialog.resize_texture.animation_frames',
                    type: 'number',
                    condition: () => isAnimatedFormat(),
                    value: this.frameCount || 1,
                    min: 1,
                    max: 2048,
                    step: 1,
                },
                fill: {label: 'dialog.resize_texture.fill', type: 'select', condition: form => form.mode === 'crop', default: 'transparent', options: {
                    transparent: 'dialog.resize_texture.fill.transparent',
                    color: 'dialog.resize_texture.fill.color',
                    repeat: 'dialog.resize_texture.fill.repeat',
                }},
                _bpad_method: {
                    label: 'bpad.resize.method',
                    type: 'inline_select',
                    condition: form => isEligibleDownscale(scope, form),
                    default: saved.method,
                    options: {
                        better_pixel_art: 'bpad.resize.method.better',
                        native_nearest: 'bpad.resize.method.native',
                    },
                },
                _bpad_advanced: {
                    label: 'bpad.resize.advanced',
                    type: 'checkbox',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art',
                    value: saved.advanced,
                },
                _bpad_preserve_thin: {
                    label: 'bpad.resize.preserve_thin',
                    type: 'checkbox',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.preserveThinFeatures,
                },
                _bpad_preserve_outline: {
                    label: 'bpad.resize.preserve_outline',
                    type: 'checkbox',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.preserveOutline,
                },
                _bpad_preserve_internal: {
                    label: 'bpad.resize.preserve_internal',
                    type: 'checkbox',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.preserveInternalEdges,
                },
                _bpad_alpha_threshold: {
                    label: 'bpad.resize.alpha_threshold',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.alphaThreshold,
                    min: 0,
                    max: 1,
                    step: 0.01,
                },
                _bpad_source_alpha_threshold: {
                    label: 'bpad.resize.source_alpha_threshold',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.sourceAlphaThreshold,
                    min: 0,
                    max: 1,
                    step: 0.001,
                },
                _bpad_thin_threshold: {
                    label: 'bpad.resize.thin_threshold',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.thinFeatureThreshold,
                    min: 0,
                    max: 1,
                    step: 0.01,
                },
                _bpad_outline_coverage: {
                    label: 'bpad.resize.outline_coverage',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.outlineMinCoverage,
                    min: 0,
                    max: 1,
                    step: 0.01,
                },
                _bpad_internal_threshold: {
                    label: 'bpad.resize.internal_threshold',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.internalEdgeThreshold,
                    min: 0,
                    max: 1,
                    step: 0.01,
                },
                _bpad_internal_weight: {
                    label: 'bpad.resize.internal_weight',
                    type: 'number',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    value: saved.internalEdgeWeight,
                    min: 0,
                    max: 8,
                    step: 0.05,
                },
                _bpad_binary_alpha: {
                    label: 'bpad.resize.binary_alpha',
                    type: 'select',
                    condition: form => isEligibleDownscale(scope, form) && form._bpad_method === 'better_pixel_art' && form._bpad_advanced,
                    default: saved.binaryAlpha,
                    options: {
                        auto: 'bpad.resize.binary_alpha.auto',
                        binary: 'bpad.resize.binary_alpha.binary',
                        coverage: 'bpad.resize.binary_alpha.coverage',
                    },
                },
            },
            onFormChange(formResult) {
                if (formResult.frames > (scope.frameCount || 1) && !updatedToRepeat) {
                    updatedToRepeat = true;
                    this.setFormValues({fill: 'repeat'});
                }
            },
            onConfirm(formResult) {
                const oldWidth = scope.width;
                const oldHeight = scope.height;
                const sourceFrames = currentFrameCount(scope);
                const targetFrames = isAnimatedFormat()
                    ? Math.max(1, Math.round(finiteNumber(formResult.frames, sourceFrames)))
                    : 1;
                const targetFrameHeight = finiteNumber(formResult.size[1], currentFrameHeight(scope));
                const eligible = isEligibleDownscale(scope, formResult);
                let useBetterPixelArt = eligible && formResult._bpad_method === 'better_pixel_art';
                let algorithmOptions = null;
                let fallbackError = null;
                if (useBetterPixelArt) {
                    try {
                        algorithmOptions = optionsFromForm(formResult);
                    } catch (error) {
                        useBetterPixelArt = false;
                        fallbackError = error;
                        console.error('[Better Pixel Art Downscale] Invalid algorithm settings; using Native Nearest.', error);
                    }
                }
                const persisted = settingsFromForm(formResult, saved);
                writeSettings(persisted);

                let elementsToChange = null;
                let algorithmCalls = 0;
                let processedSourcePixels = 0;
                const startedAt = typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now();

                if (formResult.mode === 'crop' && Texture.length >= 2 && !Format.single_texture) {
                    const elements = [...Cube.all, ...Mesh.all].filter(element => {
                        for (const faceKey in element.faces) {
                            if (element.faces[faceKey].texture === scope.uuid) return true;
                        }
                        return false;
                    });
                    if (elements.length) elementsToChange = elements;
                }

                if (isAnimatedFormat() && targetFrames > 1) {
                    formResult.size[1] *= targetFrames;
                }

                Undo.initEdit({
                    textures: [scope],
                    bitmap: true,
                    elements: elementsToChange,
                    uv_only: true,
                });

                scope.edit(() => {
                    const tempCanvas = document.createElement('canvas');
                    const tempCtx = tempCanvas.getContext('2d', {willReadFrequently: true});
                    const baseCanvasWidth = scope.canvas.width;
                    const baseCanvasHeight = scope.canvas.height;
                    const scaleX = formResult.size[0] / baseCanvasWidth;
                    const scaleY = formResult.size[1] / baseCanvasHeight;

                    const resizeCanvas = (ctx) => {
                        const sourceWidth = ctx.canvas.width;
                        const sourceHeight = ctx.canvas.height;
                        const isFullTextureCanvas = sourceWidth === baseCanvasWidth && sourceHeight === baseCanvasHeight;

                        tempCanvas.width = sourceWidth;
                        tempCanvas.height = sourceHeight;
                        tempCtx.imageSmoothingEnabled = false;
                        tempCtx.clearRect(0, 0, sourceWidth, sourceHeight);
                        tempCtx.drawImage(ctx.canvas, 0, 0);

                        let targetWidth = sourceWidth;
                        let targetHeight = sourceHeight;
                        if (isFullTextureCanvas) {
                            targetWidth = formResult.size[0];
                            targetHeight = formResult.size[1];
                        } else if (formResult.mode === 'scale') {
                            targetWidth = Math.max(1, Math.round(sourceWidth * scaleX));
                            targetHeight = Math.max(1, Math.round(sourceHeight * scaleY));
                        } else {
                            targetWidth = formResult.size[0];
                            targetHeight = formResult.size[1];
                        }

                        ctx.canvas.width = targetWidth;
                        ctx.canvas.height = targetHeight;
                        ctx.imageSmoothingEnabled = false;

                        if (formResult.mode === 'crop') {
                            switch (formResult.fill) {
                                case 'transparent':
                                    ctx.drawImage(tempCanvas, 0, 0, sourceWidth, sourceHeight);
                                    break;
                                case 'color':
                                    ctx.fillStyle = ColorPanel.get();
                                    ctx.fillRect(0, 0, targetWidth, targetHeight);
                                    ctx.clearRect(0, 0, sourceWidth, sourceHeight);
                                    ctx.drawImage(tempCanvas, 0, 0, sourceWidth, sourceHeight);
                                    break;
                                case 'repeat':
                                    for (let x = 0; x < targetWidth; x += sourceWidth) {
                                        for (let y = 0; y < targetHeight; y += sourceHeight) {
                                            ctx.drawImage(tempCanvas, x, y, sourceWidth, sourceHeight);
                                        }
                                    }
                                    break;
                            }
                            return;
                        }

                        const canUseBetterHere = useBetterPixelArt &&
                            targetWidth <= sourceWidth &&
                            targetHeight <= sourceHeight &&
                            (targetWidth < sourceWidth || targetHeight < sourceHeight);

                        if (!canUseBetterHere) {
                            ctx.drawImage(tempCanvas, 0, 0, targetWidth, targetHeight);
                            return;
                        }

                        try {
                            renderPixelArtDownscale({
                                sourceCtx: tempCtx,
                                destCtx: ctx,
                                sourceWidth,
                                sourceHeight,
                                targetWidth,
                                targetHeight,
                                options: algorithmOptions,
                                frameAware: isFullTextureCanvas,
                                sourceFrames,
                                targetFrames,
                            });
                            algorithmCalls += 1;
                            processedSourcePixels += sourceWidth * sourceHeight;
                        } catch (error) {
                            fallbackError = fallbackError || error;
                            console.error('[Better Pixel Art Downscale] Algorithm failed; using Native Nearest for this canvas.', error);
                            ctx.imageSmoothingEnabled = false;
                            ctx.drawImage(tempCanvas, 0, 0, targetWidth, targetHeight);
                        }
                    };

                    if (scope.layers_enabled && scope.layers.length) {
                        for (const layer of scope.layers) {
                            if (formResult.mode === 'scale') {
                                resizeCanvas(layer.ctx);
                                layer.offset[0] = Math.round(layer.offset[0] * (formResult.size[0] / scope.width));
                                layer.offset[1] = Math.round(layer.offset[1] * (formResult.size[1] / scope.height));
                            }
                        }
                    } else {
                        resizeCanvas(scope.ctx);
                    }

                    scope.width = formResult.size[0];
                    scope.height = formResult.size[1];
                    scope.keep_size = true;

                    if (formResult.mode === 'scale') {
                        // Scaling keeps Blockbench's native UV behavior unchanged.
                    } else if (formResult.fill === 'repeat' && isAnimatedFormat() && formResult.size[0] < formResult.size[1]) {
                        // Animated texture repeat: native behavior.
                    } else if (Format.single_texture || Texture.all.length === 1 || Format.per_texture_uv_size) {
                        if (Format.per_texture_uv_size) {
                            scope.uv_width = scope.uv_width * (formResult.size[0] / oldWidth);
                            scope.uv_height = scope.uv_height * (formResult.size[1] / oldHeight);
                            Project.texture_width = scope.uv_width;
                            Project.texture_height = scope.uv_height;
                        } else {
                            Undo.current_save.uv_mode = {
                                box_uv: Project.box_uv,
                                width: Project.texture_width,
                                height: Project.texture_height,
                            };
                            Undo.current_save.aspects.uv_mode = true;
                            Project.texture_width = Project.texture_width * (formResult.size[0] / oldWidth);
                            Project.texture_height = Project.texture_height * (formResult.size[1] / oldHeight);
                        }
                        Canvas.updateAllUVs();
                    } else if (Texture.length >= 2 && elementsToChange) {
                        elementsToChange.forEach(element => {
                            if (element.getTypeBehavior('cube_faces')) {
                                for (const key in element.faces) {
                                    if (element.faces[key].texture !== scope.uuid) continue;
                                    const uv = element.faces[key].uv;
                                    uv[0] /= formResult.size[0] / oldWidth;
                                    uv[2] /= formResult.size[0] / oldWidth;
                                    uv[1] /= formResult.size[1] / oldHeight;
                                    uv[3] /= formResult.size[1] / oldHeight;
                                }
                            } else if (element instanceof Mesh) {
                                for (const key in element.faces) {
                                    if (element.faces[key].texture !== scope.uuid) continue;
                                    const uv = element.faces[key].uv;
                                    for (const vertexKey in uv) {
                                        uv[vertexKey][0] /= formResult.size[0] / oldWidth;
                                        uv[vertexKey][1] /= formResult.size[1] / oldHeight;
                                    }
                                }
                            }
                        });
                        Canvas.updateView({elements: elementsToChange, element_aspects: {uv: true}});
                    }
                }, {no_undo: true});

                Undo.finishEdit('Resize texture');
                UVEditor.vue.updateTexture();
                setTimeout(updateSelection, 100);

                if (algorithmCalls) {
                    const endedAt = typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now();
                    console.debug(
                        `[Better Pixel Art Downscale] ${scope.name || 'Texture'}: ${algorithmCalls} canvas${algorithmCalls === 1 ? '' : 'es'}, ` +
                        `${processedSourcePixels.toLocaleString()} source pixels, ${(endedAt - startedAt).toFixed(2)} ms.`,
                    );
                }
                if (fallbackError) {
                    if (Blockbench && typeof Blockbench.showQuickMessage === 'function') {
                        Blockbench.showQuickMessage(tr('bpad.message.fallback', 'Better Pixel Art downscale failed; Native Nearest was used instead.'), 3500);
                    }
                }
            },
        });

        dialog.show();
        return this;
    }

    Object.defineProperties(enhancedResizeDialog, {
        __betterPixelArtDownscalePatch: {value: true},
        __betterPixelArtDownscaleCore: {value: BetterPixelArtDownscale},
        __betterPixelArtDownscaleRevision: {value: CORE_REVISION},
    });

    function installPatch() {
        if (typeof Texture === 'undefined' || !Texture.prototype || typeof Texture.prototype.resizeDialog !== 'function') {
            console.error('[Better Pixel Art Downscale] Texture.resizeDialog was not found.');
            if (typeof Blockbench !== 'undefined' && typeof Blockbench.showQuickMessage === 'function') {
                Blockbench.showQuickMessage(tr('bpad.message.incompatible', 'Better Pixel Art Downscale could not patch Texture.resizeDialog in this Blockbench version.'), 5000);
            }
            return false;
        }

        if (Texture.prototype.resizeDialog.__betterPixelArtDownscalePatch) {
            patchedResizeDialog = Texture.prototype.resizeDialog;
            return true;
        }

        originalResizeDialog = Texture.prototype.resizeDialog;
        patchedResizeDialog = enhancedResizeDialog;
        Texture.prototype.resizeDialog = patchedResizeDialog;
        console.info(`[Better Pixel Art Downscale] Installed ${PLUGIN_VERSION}. ${CORE_REVISION}`);
        return true;
    }

    function uninstallPatch() {
        if (
            typeof Texture !== 'undefined' &&
            Texture.prototype &&
            Texture.prototype.resizeDialog === patchedResizeDialog &&
            originalResizeDialog
        ) {
            Texture.prototype.resizeDialog = originalResizeDialog;
        }
        originalResizeDialog = null;
        patchedResizeDialog = null;
    }

    Plugin.register(PLUGIN_ID, {
        title: 'Better Pixel Art Downscale',
        author: 'MidFord',
        description: 'Integrates BetterPixelArtDownscale directly into Blockbench\'s native Resize Texture dialog, preserving pixel-art silhouettes, outlines, thin features, internal edges, palette colors, alpha behavior, layers, Undo, and native UV handling.',
        icon: 'photo_size_select_small',
        version: PLUGIN_VERSION,
        variant: 'both',
        min_version: '5.1.0',
        tags: ['Texture', 'Pixel Art', 'Utility'],
        onload() {
            addTranslations();
            installPatch();
        },
        onunload() {
            uninstallPatch();
        },
    });
})();
