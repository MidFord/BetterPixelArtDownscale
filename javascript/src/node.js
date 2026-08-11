import { readFileSync, writeFileSync } from 'node:fs';
import { downscale, downscaleByFactor, edgeLayer } from './core.js';
import { decodePng, encodePng } from './png.js';

export function readPng(path) {
  return decodePng(readFileSync(path));
}

export function writePng(path, image, options = undefined) {
  writeFileSync(path, encodePng(image, options));
  return image;
}

export function downscaleFile(inputPath, outputPath, { size = null, factor = null, options = undefined } = {}) {
  if ((size === null) === (factor === null)) {
    throw new Error('provide exactly one of size or factor');
  }
  const image = readPng(inputPath);
  const result = size !== null
    ? downscale(image, size, options)
    : Array.isArray(factor)
      ? downscaleByFactor(image, factor[0], factor[1], options)
      : downscaleByFactor(image, factor, factor, options);
  writePng(outputPath, result);
  return result;
}

export function edgeLayerFile(
  inputPath,
  outputPath,
  { size, options = undefined, includeOutline = true, includeInternalEdges = true } = {},
) {
  const image = readPng(inputPath);
  const result = edgeLayer(image, size, options, { includeOutline, includeInternalEdges });
  writePng(outputPath, result);
  return result;
}

export { decodePng, encodePng } from './png.js';
export { downscaleFile as downscale_file, edgeLayerFile as edge_layer_file };
