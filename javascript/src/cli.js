#!/usr/bin/env node
import { downscaleFile } from './node.js';
import { DownscaleOptions } from './options.js';

function usage() {
  console.error(`Usage:\n  better-pixel-art-downscale-js input.png output.png --size 32x32\n  better-pixel-art-downscale-js input.png output.png --factor 2\n\nOptions:\n  --alpha-threshold N\n  --no-outline\n  --no-internal-edges\n  --no-thin-features`);
  process.exit(2);
}

const args = process.argv.slice(2);
if (args.length < 4) usage();
const [inputPath, outputPath, ...rest] = args;
let size = null;
let factor = null;
const opts = {};

for (let i = 0; i < rest.length; i += 1) {
  const arg = rest[i];
  if (arg === '--size') {
    const m = /^(\d+)x(\d+)$/i.exec(rest[++i] ?? '');
    if (!m) usage();
    size = [Number(m[1]), Number(m[2])];
  } else if (arg === '--factor') {
    factor = Number(rest[++i]);
    if (!(factor >= 1)) usage();
  } else if (arg === '--alpha-threshold') {
    opts.alphaThreshold = Number(rest[++i]);
  } else if (arg === '--no-outline') {
    opts.preserveOutline = false;
  } else if (arg === '--no-internal-edges') {
    opts.preserveInternalEdges = false;
  } else if (arg === '--no-thin-features') {
    opts.preserveThinFeatures = false;
  } else {
    usage();
  }
}

if ((size === null) === (factor === null)) usage();
downscaleFile(inputPath, outputPath, {
  size,
  factor,
  options: new DownscaleOptions(opts),
});
