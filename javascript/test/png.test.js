import test from 'node:test';
import assert from 'node:assert/strict';
import { decodePng, encodePng } from '../src/png.js';

test('PNG RGBA encoder/decoder roundtrip', () => {
  const image = {
    width: 3,
    height: 2,
    data: Uint8ClampedArray.from([
      255, 0, 0, 255, 0, 255, 0, 128, 0, 0, 255, 0,
      1, 2, 3, 4, 10, 20, 30, 40, 250, 240, 230, 220,
    ]),
  };
  const decoded = decodePng(encodePng(image));
  assert.equal(decoded.width, image.width);
  assert.equal(decoded.height, image.height);
  assert.deepEqual([...decoded.data], [...image.data]);
});
