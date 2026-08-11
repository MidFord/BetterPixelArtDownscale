import test from 'node:test';
import assert from 'node:assert/strict';
import { DownscaleOptions, downscale, downscaleByFactor } from '../src/index.js';

function image(width, height, fill = [0, 0, 0, 0]) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < width * height; i += 1) data.set(fill, i * 4);
  return { width, height, data };
}

function setPixel(img, x, y, rgba) {
  img.data.set(rgba, (y * img.width + x) * 4);
}

function bboxAlpha(img) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < img.height; y += 1) {
    for (let x = 0; x < img.width; x += 1) {
      if (img.data[(y * img.width + x) * 4 + 3] === 0) continue;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }
  return maxX < 0 ? null : [minX, minY, maxX + 1, maxY + 1];
}

function outlinedSquare(size = 16) {
  const img = image(size, size);
  for (let y = 2; y < 14; y += 1) {
    for (let x = 2; x < 14; x += 1) setPixel(img, x, y, [20, 20, 20, 255]);
  }
  for (let y = 3; y < 13; y += 1) {
    for (let x = 3; x < 13; x += 1) setPixel(img, x, y, [220, 60, 80, 255]);
  }
  return img;
}

test('outline never expands beyond silhouette', () => {
  const result = downscale(outlinedSquare(), [8, 8]);
  assert.deepEqual(bboxAlpha(result), [1, 1, 7, 7]);
});

test('transparent RGB does not bleed', () => {
  const img = image(8, 8, [255, 0, 0, 0]);
  for (let y = 2; y < 6; y += 1) {
    for (let x = 2; x < 6; x += 1) setPixel(img, x, y, [0, 90, 255, 255]);
  }
  const result = downscale(img, [4, 4]);
  for (let i = 0; i < result.width * result.height; i += 1) {
    const p = i * 4;
    if (result.data[p + 3]) {
      assert.equal(result.data[p], 0);
      assert.equal(result.data[p + 2], 255);
    }
  }
});

test('deterministic output', () => {
  const img = image(32, 32);
  let state = 42;
  const rnd = () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state & 0xff;
  };
  for (let i = 0; i < img.width * img.height; i += 1) {
    const p = i * 4;
    img.data[p] = rnd();
    img.data[p + 1] = rnd();
    img.data[p + 2] = rnd();
    img.data[p + 3] = rnd() > 100 ? 255 : 0;
  }
  assert.deepEqual([...downscale(img, [11, 13]).data], [...downscale(img, [11, 13]).data]);
});

test('factor API and validation', () => {
  const result = downscaleByFactor(outlinedSquare(), 2);
  assert.deepEqual([result.width, result.height], [8, 8]);
  assert.throws(() => downscaleByFactor(outlinedSquare(), 0.5));
  assert.throws(() => downscale(outlinedSquare(), [32, 32]));
});

test('semi-transparent alpha is area aware', () => {
  const img = image(4, 4);
  for (let y = 0; y < 4; y += 1) {
    for (let x = 0; x < 2; x += 1) setPixel(img, x, y, [100, 150, 200, 128]);
  }
  const result = downscale(
    img,
    [2, 2],
    new DownscaleOptions({ alphaThreshold: 0.1, binaryAlpha: false }),
  );
  const mean = (result.data[3] + result.data[11]) / 2;
  assert.ok(mean >= 60 && mean <= 130);
});
