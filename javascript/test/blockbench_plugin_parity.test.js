import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import {
  ContentHint,
  CutoutPolicy,
  downscaleSemanticV3,
  analyzeCutout,
} from '../src/index.js';

function makeImage(width, height, fill = [0, 0, 0, 0]) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < width * height; i += 1) data.set(fill, i * 4);
  return { width, height, data };
}

function setPixel(image, x, y, rgba) {
  image.data.set(rgba, (y * image.width + x) * 4);
}

function loadPluginEngine() {
  const pluginPath = fileURLToPath(new URL('../../better_pixel_art_downscale.js', import.meta.url));
  const source = fs.readFileSync(pluginPath, 'utf8');
  let registration = null;

  function Texture() {}
  Texture.prototype.resizeDialog = function nativeResizeDialog() {};
  Texture.all = [];

  const sandbox = {
    Plugin: {
      register(id, definition) {
        registration = { id, definition };
      },
    },
    Texture,
    console: { info() {}, warn() {}, error() {}, debug() {} },
  };
  vm.createContext(sandbox);
  new vm.Script(source, { filename: 'better_pixel_art_downscale.js' }).runInContext(sandbox);
  assert.ok(registration, 'plugin must register itself');
  assert.equal(registration.id, 'better_pixel_art_downscale');
  assert.equal(registration.definition.version, '1.1.0');
  registration.definition.onload();

  const patch = sandbox.Texture.prototype.resizeDialog;
  assert.equal(patch.__betterPixelArtDownscalePatch, true);
  assert.match(patch.__betterPixelArtDownscaleRevision, /Semantic v3/);
  assert.ok(patch.__betterPixelArtDownscaleCore);
  return patch.__betterPixelArtDownscaleCore;
}

function pluginImage(engine, image) {
  return engine.fromImageData({
    width: image.width,
    height: image.height,
    data: Array.from(image.data),
  });
}

function compareFixture(engine, image, size, contentHint) {
  const expected = downscaleSemanticV3(image, size, { contentHint });
  const actual = engine.downscaleSemanticV3(
    pluginImage(engine, image),
    size,
    new engine.SemanticOptions({ contentHint }),
  );
  assert.deepEqual([actual.width, actual.height], [expected.width, expected.height]);
  assert.deepEqual(Array.from(actual.data), Array.from(expected.data));
}

test('Blockbench bundle is byte-identical to modular semantic v3 fixtures', () => {
  const engine = loadPluginEngine();

  const item = makeImage(16, 16);
  for (let y = 1; y < 15; y += 1) {
    setPixel(item, 7, y, [210, 180, 60, 255]);
    setPixel(item, 8, y, [210, 180, 60, 255]);
  }
  for (let x = 4; x < 12; x += 1) {
    setPixel(item, x, 5, [35, 35, 35, 255]);
    setPixel(item, x, 6, [35, 35, 35, 255]);
  }
  compareFixture(engine, item, [8, 8], ContentHint.ITEM);

  const surface = makeImage(16, 16, [64, 70, 75, 255]);
  const palette = [
    [64, 70, 75, 255],
    [86, 91, 94, 255],
    [110, 105, 96, 255],
    [135, 125, 110, 255],
  ];
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) setPixel(surface, x, y, palette[(x + 2 * y) % palette.length]);
  }
  compareFixture(engine, surface, [8, 8], ContentHint.BLOCK);

  const ghost = makeImage(16, 16, [90, 90, 90, 1]);
  for (let y = 1; y < 16; y += 2) {
    for (let x = 1; x < 16; x += 2) setPixel(ghost, x, y, [200, 40, 40, 255]);
  }
  compareFixture(engine, ghost, [8, 8], ContentHint.BLOCK);

  const spanning = makeImage(16, 16);
  for (let x = 0; x < 16; x += 1) setPixel(spanning, x, 4, [120, 200, 80, 255]);
  compareFixture(engine, spanning, [8, 8], ContentHint.BLOCK);

  const rescue = makeImage(16, 16);
  setPixel(rescue, 4, 4, [250, 210, 60, 255]);
  compareFixture(engine, rescue, [8, 8], ContentHint.BLOCK);

  const dense = makeImage(16, 16);
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) {
      if ((x + y) % 2 === 0) setPixel(dense, x, y, [40, 180, 90, 255]);
    }
  }
  compareFixture(engine, dense, [8, 8], ContentHint.BLOCK);
});

test('Blockbench bundle cutout policy router matches modular semantic v3', () => {
  const engine = loadPluginEngine();
  const fixtures = [];

  const ghost = makeImage(16, 16, [80, 80, 80, 1]);
  fixtures.push(ghost);

  const spanning = makeImage(16, 16);
  for (let x = 0; x < 16; x += 1) setPixel(spanning, x, 4, [255, 255, 255, 255]);
  fixtures.push(spanning);

  const rescue = makeImage(16, 16);
  setPixel(rescue, 4, 4, [255, 255, 255, 255]);
  fixtures.push(rescue);

  const dense = makeImage(16, 16);
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) if ((x + y) % 2 === 0) setPixel(dense, x, y, [255, 255, 255, 255]);
  }
  fixtures.push(dense);

  for (const fixture of fixtures) {
    const expected = analyzeCutout(fixture, [8, 8]);
    const actual = engine.analyzeCutout(pluginImage(engine, fixture), [8, 8]);
    assert.equal(actual.policy, expected.policy);
  }

  assert.equal(engine.CutoutPolicy.STABLE_PHASE, CutoutPolicy.STABLE_PHASE);
  assert.equal(engine.CutoutPolicy.BBOX_PHASE_RESCUE, CutoutPolicy.BBOX_PHASE_RESCUE);
  assert.equal(engine.CutoutPolicy.SPANNING_COVERAGE, CutoutPolicy.SPANNING_COVERAGE);
  assert.equal(engine.CutoutPolicy.DENSE_COVERAGE, CutoutPolicy.DENSE_COVERAGE);
  assert.equal(engine.CutoutPolicy.SPRITE_TOPOLOGY, CutoutPolicy.SPRITE_TOPOLOGY);
});
