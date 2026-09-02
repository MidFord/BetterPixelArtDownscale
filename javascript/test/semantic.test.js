import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ContentHint,
  CutoutPolicy,
  SemanticMode,
  SemanticOptions,
  analyze,
  analyzeCutout,
  downscale,
  downscaleSemanticV3,
} from '../src/index.js';

function image(width, height, fill = [0, 0, 0, 0]) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < width * height; i += 1) data.set(fill, i * 4);
  return { width, height, data };
}

function setPixel(img, x, y, rgba) {
  img.data.set(rgba, (y * img.width + x) * 4);
}

function visibleCount(img) {
  let count = 0;
  for (let i = 3; i < img.data.length; i += 4) if (img.data[i] > 0) count += 1;
  return count;
}

test('semantic item hint routes to the tuned sprite solver', () => {
  const img = image(16, 16);
  for (let y = 1; y < 15; y += 1) {
    setPixel(img, 7, y, [210, 180, 60, 255]);
    setPixel(img, 8, y, [210, 180, 60, 255]);
  }
  for (let x = 4; x < 12; x += 1) {
    setPixel(img, x, 5, [35, 35, 35, 255]);
    setPixel(img, x, 6, [35, 35, 35, 255]);
  }
  const analysis = analyze(img, new SemanticOptions({ contentHint: ContentHint.ITEM }));
  assert.equal(analysis.mode, SemanticMode.SPRITE);
  const expected = downscale(img, [8, 8], { alphaThreshold: 0.05, internalEdgeWeight: 0.0 });
  const actual = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.ITEM });
  assert.deepEqual([...actual.data], [...expected.data]);
});

test('opaque block uses surface mode and remains source-palette-first', () => {
  const img = image(16, 16, [64, 70, 75, 255]);
  const palette = [
    [64, 70, 75, 255],
    [86, 91, 94, 255],
    [110, 105, 96, 255],
    [135, 125, 110, 255],
  ];
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) setPixel(img, x, y, palette[(x + 2 * y) % palette.length]);
  }
  const analysis = analyze(img, new SemanticOptions({ contentHint: ContentHint.BLOCK }));
  assert.equal(analysis.mode, SemanticMode.SURFACE);
  const result = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  const colors = new Set(palette.map((rgba) => rgba.slice(0, 3).join(',')));
  for (let p = 0; p < result.data.length; p += 4) {
    assert.ok(colors.has([result.data[p], result.data[p + 1], result.data[p + 2]].join(',')));
  }
});

test('ghost alpha uses stable phase instead of binary topology reasoning', () => {
  const img = image(16, 16, [90, 90, 90, 1]);
  for (let y = 1; y < 16; y += 2) {
    for (let x = 1; x < 16; x += 2) setPixel(img, x, y, [200, 40, 40, 255]);
  }
  const cutout = analyzeCutout(img, [8, 8]);
  assert.equal(cutout.policy, CutoutPolicy.STABLE_PHASE);
  const result = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  assert.equal(result.data[3], 255);
  assert.equal(result.data[0], 200);
});

test('edge-spanning thin features use coverage preservation', () => {
  const img = image(16, 16);
  for (let x = 0; x < 16; x += 1) setPixel(img, x, 4, [120, 200, 80, 255]);
  const cutout = analyzeCutout(img, [8, 8]);
  assert.equal(cutout.policy, CutoutPolicy.SPANNING_COVERAGE);
  const result = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  assert.equal(visibleCount(result), 8);
});

test('freestanding feature is rescued only when stable phase erases it', () => {
  const img = image(16, 16);
  setPixel(img, 4, 4, [250, 210, 60, 255]);
  const cutout = analyzeCutout(img, [8, 8]);
  assert.equal(cutout.policy, CutoutPolicy.BBOX_PHASE_RESCUE);
  const result = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  assert.equal(visibleCount(result), 1);
  const p = (2 * 8 + 2) * 4;
  assert.deepEqual([...result.data.slice(p, p + 4)], [250, 210, 60, 255]);
});

test('dense checker cutout uses dense coverage without RGB blending', () => {
  const img = image(16, 16);
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) {
      if ((x + y) % 2 === 0) setPixel(img, x, y, [40, 180, 90, 255]);
    }
  }
  const cutout = analyzeCutout(img, [8, 8]);
  assert.equal(cutout.policy, CutoutPolicy.DENSE_COVERAGE);
  const result = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  assert.equal(visibleCount(result), 64);
  for (let p = 0; p < result.data.length; p += 4) {
    assert.deepEqual([...result.data.slice(p, p + 4)], [40, 180, 90, 255]);
  }
});

test('semantic v3 is deterministic', () => {
  const img = image(16, 16);
  let state = 123;
  const rnd = () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state & 0xff;
  };
  for (let i = 0; i < 16 * 16; i += 1) {
    const p = i * 4;
    img.data[p] = rnd();
    img.data[p + 1] = rnd();
    img.data[p + 2] = rnd();
    img.data[p + 3] = rnd() > 100 ? 255 : 0;
  }
  const a = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  const b = downscaleSemanticV3(img, [8, 8], { contentHint: ContentHint.BLOCK });
  assert.deepEqual([...a.data], [...b.data]);
});
