import { deflateSync, inflateSync } from 'node:zlib';

const PNG_SIGNATURE = Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]);

function readU32(bytes, offset) {
  return ((bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
}

function writeU32(value) {
  return Uint8Array.from([(value >>> 24) & 255, (value >>> 16) & 255, (value >>> 8) & 255, value & 255]);
}

let crcTable;
function getCrcTable() {
  if (crcTable) return crcTable;
  crcTable = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    crcTable[n] = c >>> 0;
  }
  return crcTable;
}

function crc32(bytes) {
  const table = getCrcTable();
  let c = 0xffffffff;
  for (const byte of bytes) c = table[(c ^ byte) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function concatArrays(parts) {
  const length = parts.reduce((n, part) => n + part.length, 0);
  const out = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function chunk(type, data = new Uint8Array()) {
  const typeBytes = new TextEncoder().encode(type);
  const body = concatArrays([typeBytes, data]);
  return concatArrays([writeU32(data.length), body, writeU32(crc32(body))]);
}

function paethPredictor(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

function channelsForColorType(colorType) {
  switch (colorType) {
    case 0: return 1;
    case 2: return 3;
    case 3: return 1;
    case 4: return 2;
    case 6: return 4;
    default: throw new Error(`Unsupported PNG color type ${colorType}`);
  }
}

function validBitDepth(colorType, bitDepth) {
  if (colorType === 0) return [1, 2, 4, 8, 16].includes(bitDepth);
  if (colorType === 2) return [8, 16].includes(bitDepth);
  if (colorType === 3) return [1, 2, 4, 8].includes(bitDepth);
  if (colorType === 4 || colorType === 6) return [8, 16].includes(bitDepth);
  return false;
}

function sampleAt(row, sampleIndex, bitDepth) {
  if (bitDepth === 8) return row[sampleIndex];
  if (bitDepth === 16) return row[sampleIndex * 2];
  const samplesPerByte = 8 / bitDepth;
  const byte = row[Math.floor(sampleIndex / samplesPerByte)];
  const shift = 8 - bitDepth * ((sampleIndex % samplesPerByte) + 1);
  const mask = (1 << bitDepth) - 1;
  return (byte >>> shift) & mask;
}

function scaleSample(value, bitDepth) {
  if (bitDepth === 8 || bitDepth === 16) return value;
  const max = (1 << bitDepth) - 1;
  return Math.round(value * 255 / max);
}

export function decodePng(input) {
  const bytes = input instanceof Uint8Array ? input : new Uint8Array(input);
  if (bytes.length < 8 || !PNG_SIGNATURE.every((v, i) => bytes[i] === v)) {
    throw new Error('Invalid PNG signature');
  }

  let offset = 8;
  let width;
  let height;
  let bitDepth;
  let colorType;
  let interlace;
  let palette = null;
  let transparency = null;
  const idat = [];

  while (offset + 12 <= bytes.length) {
    const length = readU32(bytes, offset);
    offset += 4;
    const type = new TextDecoder().decode(bytes.subarray(offset, offset + 4));
    offset += 4;
    const data = bytes.subarray(offset, offset + length);
    offset += length;
    offset += 4;

    if (type === 'IHDR') {
      width = readU32(data, 0);
      height = readU32(data, 4);
      bitDepth = data[8];
      colorType = data[9];
      const compression = data[10];
      const filter = data[11];
      interlace = data[12];
      if (compression !== 0 || filter !== 0) throw new Error('Unsupported PNG compression/filter method');
      if (interlace !== 0) throw new Error('Adam7-interlaced PNGs are not supported');
      if (!validBitDepth(colorType, bitDepth)) {
        throw new Error(`Unsupported PNG bit depth ${bitDepth} for color type ${colorType}`);
      }
    } else if (type === 'PLTE') {
      palette = new Uint8Array(data);
    } else if (type === 'tRNS') {
      transparency = new Uint8Array(data);
    } else if (type === 'IDAT') {
      idat.push(new Uint8Array(data));
    } else if (type === 'IEND') {
      break;
    }
  }

  if (!width || !height || bitDepth === undefined || colorType === undefined) {
    throw new Error('PNG is missing IHDR');
  }
  if (colorType === 3 && !palette) throw new Error('Indexed PNG is missing PLTE');

  const channels = channelsForColorType(colorType);
  const bitsPerPixel = channels * bitDepth;
  const rowBytes = Math.ceil(width * bitsPerPixel / 8);
  const bytesPerPixel = Math.max(1, Math.ceil(bitsPerPixel / 8));
  const inflated = new Uint8Array(inflateSync(concatArrays(idat)));
  const expected = height * (rowBytes + 1);
  if (inflated.length < expected) throw new Error('Truncated PNG image data');

  const rows = new Array(height);
  let srcOffset = 0;
  let previous = new Uint8Array(rowBytes);
  for (let y = 0; y < height; y += 1) {
    const filterType = inflated[srcOffset++];
    const raw = inflated.subarray(srcOffset, srcOffset + rowBytes);
    srcOffset += rowBytes;
    const row = new Uint8Array(rowBytes);
    for (let x = 0; x < rowBytes; x += 1) {
      const a = x >= bytesPerPixel ? row[x - bytesPerPixel] : 0;
      const b = previous[x] ?? 0;
      const c = x >= bytesPerPixel ? previous[x - bytesPerPixel] : 0;
      let value;
      switch (filterType) {
        case 0: value = raw[x]; break;
        case 1: value = (raw[x] + a) & 255; break;
        case 2: value = (raw[x] + b) & 255; break;
        case 3: value = (raw[x] + Math.floor((a + b) / 2)) & 255; break;
        case 4: value = (raw[x] + paethPredictor(a, b, c)) & 255; break;
        default: throw new Error(`Unsupported PNG row filter ${filterType}`);
      }
      row[x] = value;
    }
    rows[y] = row;
    previous = row;
  }

  const rgba = new Uint8ClampedArray(width * height * 4);
  let transparentGray = null;
  let transparentRgb = null;
  if (transparency && colorType === 0 && transparency.length >= 2) {
    transparentGray = (transparency[0] << 8) | transparency[1];
  }
  if (transparency && colorType === 2 && transparency.length >= 6) {
    transparentRgb = [
      (transparency[0] << 8) | transparency[1],
      (transparency[2] << 8) | transparency[3],
      (transparency[4] << 8) | transparency[5],
    ];
  }

  for (let y = 0; y < height; y += 1) {
    const row = rows[y];
    for (let x = 0; x < width; x += 1) {
      const p = (y * width + x) * 4;
      if (colorType === 0) {
        const sample = sampleAt(row, x, bitDepth);
        const gray = scaleSample(sample, bitDepth);
        rgba[p] = gray;
        rgba[p + 1] = gray;
        rgba[p + 2] = gray;
        const rawSample = bitDepth === 16 ? ((row[x * 2] << 8) | row[x * 2 + 1]) : sample;
        rgba[p + 3] = transparentGray !== null && rawSample === transparentGray ? 0 : 255;
      } else if (colorType === 2) {
        const base = x * 3;
        const r = sampleAt(row, base, bitDepth);
        const g = sampleAt(row, base + 1, bitDepth);
        const b = sampleAt(row, base + 2, bitDepth);
        rgba[p] = r;
        rgba[p + 1] = g;
        rgba[p + 2] = b;
        if (transparentRgb && bitDepth === 8) {
          rgba[p + 3] = (r === transparentRgb[0] && g === transparentRgb[1] && b === transparentRgb[2]) ? 0 : 255;
        } else {
          rgba[p + 3] = 255;
        }
      } else if (colorType === 3) {
        const index = sampleAt(row, x, bitDepth);
        const pp = index * 3;
        rgba[p] = palette[pp] ?? 0;
        rgba[p + 1] = palette[pp + 1] ?? 0;
        rgba[p + 2] = palette[pp + 2] ?? 0;
        rgba[p + 3] = transparency && index < transparency.length ? transparency[index] : 255;
      } else if (colorType === 4) {
        const base = x * 2;
        const gray = sampleAt(row, base, bitDepth);
        const a = sampleAt(row, base + 1, bitDepth);
        rgba[p] = gray;
        rgba[p + 1] = gray;
        rgba[p + 2] = gray;
        rgba[p + 3] = a;
      } else if (colorType === 6) {
        const base = x * 4;
        rgba[p] = sampleAt(row, base, bitDepth);
        rgba[p + 1] = sampleAt(row, base + 1, bitDepth);
        rgba[p + 2] = sampleAt(row, base + 2, bitDepth);
        rgba[p + 3] = sampleAt(row, base + 3, bitDepth);
      }
    }
  }

  return { width, height, data: rgba };
}

export function encodePng(image, { compressionLevel = 9 } = {}) {
  if (!image || !Number.isInteger(image.width) || !Number.isInteger(image.height) || !image.data || image.data.length !== image.width * image.height * 4) {
    throw new TypeError('encodePng expects { width, height, data } with RGBA bytes');
  }

  const ihdr = new Uint8Array(13);
  ihdr.set(writeU32(image.width), 0);
  ihdr.set(writeU32(image.height), 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const stride = image.width * 4;
  const raw = new Uint8Array(image.height * (stride + 1));
  for (let y = 0; y < image.height; y += 1) {
    const dst = y * (stride + 1);
    raw[dst] = 0;
    raw.set(image.data.subarray(y * stride, (y + 1) * stride), dst + 1);
  }

  const idat = new Uint8Array(deflateSync(raw, { level: compressionLevel }));
  return concatArrays([
    PNG_SIGNATURE,
    chunk('IHDR', ihdr),
    chunk('IDAT', idat),
    chunk('IEND'),
  ]);
}
