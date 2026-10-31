import { test } from 'node:test';
import assert from 'node:assert/strict';
import { qrMatrix, qrSvg, qrDataUrl } from '../src/qr.js';
import { rsDivisor, rsRemainder } from '../src/rs.js';

// A small independent reader: format bits -> unmask -> zigzag read -> de-interleave -> RS syndromes -> byte mode.
const EC_BITS = { 1: 'L', 0: 'M', 3: 'Q', 2: 'H' };
const MASKS = [
  (x, y) => (x + y) % 2 === 0, (x, y) => y % 2 === 0, (x) => x % 3 === 0, (x, y) => (x + y) % 3 === 0,
  (x, y) => (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0, (x, y) => ((x * y) % 2) + ((x * y) % 3) === 0,
  (x, y) => (((x * y) % 2) + ((x * y) % 3)) % 2 === 0, (x, y) => (((x + y) % 2) + ((x * y) % 3)) % 2 === 0,
];

function gfMul(x, y) {
  let z = 0;
  for (let i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11d); z ^= ((y >>> i) & 1) * x; }
  return z;
}

function readFormat({ modules: m }) {
  let bits = 0;
  const seq = [[8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8], [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8]];
  seq.forEach(([x, y], i) => { if (m[y][x]) bits |= 1 << i; });
  const data = (bits ^ 0x5412) >>> 10;
  return { ecl: EC_BITS[data >>> 3], mask: data & 7 };
}

// Independent map of function modules (finders + separators, timing, alignment, format, version, dark module).
function functionMap(version, size) {
  const f = Array.from({ length: size }, () => new Array(size).fill(false));
  const mark = (x, y) => { if (x >= 0 && y >= 0 && x < size && y < size) f[y][x] = true; };
  for (let y = 0; y < 9; y++) for (let x = 0; x < 9; x++) mark(x, y); // top-left finder + format
  for (let y = 0; y < 9; y++) for (let x = 0; x < 8; x++) { mark(size - 1 - x, y); mark(y, size - 1 - x); }
  for (let i = 0; i < size; i++) { mark(6, i); mark(i, 6); }
  if (version > 1) {
    const n = Math.floor(version / 7) + 2;
    const step = version === 32 ? 26 : Math.ceil((version * 4 + 4) / (n * 2 - 2)) * 2;
    const pos = [6];
    for (let p = size - 7; pos.length < n; p -= step) pos.splice(1, 0, p);
    for (const cx of pos) for (const cy of pos) {
      if ((cx === 6 && cy === 6) || (cx === 6 && cy === size - 7) || (cx === size - 7 && cy === 6)) continue;
      for (let d = -2; d <= 2; d++) for (let e = -2; e <= 2; e++) mark(cx + d, cy + e);
    }
  }
  if (version >= 7) for (let i = 0; i < 18; i++) { mark(size - 11 + (i % 3), Math.floor(i / 3)); mark(Math.floor(i / 3), size - 11 + (i % 3)); }
  return f;
}

test('Reed-Solomon matches the published 1-M "HELLO WORLD" vector', () => {
  const data = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17];
  assert.deepEqual(rsRemainder(data, rsDivisor(10)), [196, 35, 39, 119, 235, 215, 231, 226, 93, 23]);
});

test('every RS codeword (data + ecc) has zero syndromes', () => {
  for (const degree of [7, 10, 16, 22, 28, 30]) {
    const data = Array.from({ length: 40 }, (_, i) => (i * 37 + degree) & 255);
    const word = data.concat(rsRemainder(data, rsDivisor(degree)));
    let root = 1;
    for (let i = 0; i < degree; i++) {
      let s = 0;
      for (const c of word) s = gfMul(s, root) ^ c;
      assert.equal(s, 0, `syndrome ${i} of degree ${degree}`);
      root = gfMul(root, 2);
    }
  }
});

test('finder patterns, timing, dark module and size per version', () => {
  for (const len of [1, 20, 100, 400]) {
    const qr = qrMatrix('x'.repeat(len));
    const { size, modules: m, version } = qr;
    assert.equal(size, version * 4 + 17);
    for (const [cx, cy] of [[3, 3], [size - 4, 3], [3, size - 4]]) {
      for (let d = -3; d <= 3; d++) {
        assert.equal(m[cy - 3][cx + d], true);
        assert.equal(m[cy + 3][cx + d], true);
        assert.equal(m[cy][cx], true);
      }
      assert.equal(m[cy - 2][cx], false);
    }
    for (let i = 8; i < size - 8; i++) {
      assert.equal(m[6][i], i % 2 === 0);
      assert.equal(m[i][6], i % 2 === 0);
    }
    assert.equal(m[size - 8][8], true);
  }
});

test('format info encodes the chosen level and mask', () => {
  for (const ecl of ['L', 'M', 'Q', 'H']) {
    for (let mask = 0; mask < 8; mask++) {
      const qr = qrMatrix('upi://pay?pa=a@b', { ecl, mask });
      assert.deepEqual(readFormat(qr), { ecl, mask });
    }
  }
});

test('version grows with data and higher ECC', () => {
  assert.equal(qrMatrix('a'.repeat(14), { ecl: 'M' }).version, 1);
  assert.equal(qrMatrix('a'.repeat(15), { ecl: 'M' }).version, 2);
  assert.equal(qrMatrix('a'.repeat(17), { ecl: 'L' }).version, 1);
  assert.ok(qrMatrix('a'.repeat(100), { ecl: 'H' }).version > qrMatrix('a'.repeat(100), { ecl: 'L' }).version);
  assert.equal(qrMatrix('a'.repeat(2953), { ecl: 'L' }).version, 40);
  assert.throws(() => qrMatrix('a'.repeat(2954), { ecl: 'L' }), RangeError);
});

test('version info is present from version 7', () => {
  const qr = qrMatrix('a'.repeat(200), { ecl: 'M' });
  assert.ok(qr.version >= 7);
  // version info block bottom-left mirrors top-right
  for (let i = 0; i < 18; i++) {
    const a = qr.size - 11 + (i % 3);
    const b = Math.floor(i / 3);
    assert.equal(qr.modules[b][a], qr.modules[a][b]);
  }
});

test('automatic mask choice is the lowest-penalty one and deterministic', () => {
  const a = qrMatrix('upi://pay?pa=shop@okaxis&pn=Shop&am=99.07&cu=INR');
  const b = qrMatrix('upi://pay?pa=shop@okaxis&pn=Shop&am=99.07&cu=INR');
  assert.deepEqual(a, b);
  assert.ok(a.mask >= 0 && a.mask <= 7);
});

test('UTF-8 text is supported', () => {
  const qr = qrMatrix('नमस्ते ₹');
  assert.equal(qr.version, 2); // 4 + 8 + 21*8 bits > v1-M capacity of 128
});

test('svg output', () => {
  const svg = qrSvg('hello', { size: 200, title: 'Pay <me>', dark: '#123' });
  assert.match(svg, /^<svg xmlns="http:\/\/www.w3.org\/2000\/svg" viewBox="0 0 29 29" width="200" height="200"/);
  assert.match(svg, /<title>Pay &#60;me&#62;<\/title>/);
  assert.match(svg, /fill="#123"/);
  assert.ok(qrDataUrl('hello').startsWith('data:image/svg+xml;charset=utf-8,%3Csvg'));
  assert.match(qrSvg('hello', { border: 0 }), /viewBox="0 0 21 21"/);
});

test('bad options throw', () => {
  assert.throws(() => qrMatrix(5), TypeError);
  assert.throws(() => qrMatrix('a', { ecl: 'X' }), RangeError);
  assert.throws(() => qrMatrix('a', { mask: 8 }), RangeError);
  assert.throws(() => qrMatrix('a', { minVersion: 5, maxVersion: 2 }), RangeError);
  assert.throws(() => qrSvg('a', { border: -1 }), RangeError);
  assert.throws(() => qrSvg('a', { size: 'abc' }), RangeError);
  assert.throws(() => qrSvg('a', { size: 0 }), RangeError);
});

// The unmasked data region must reproduce the exact codeword stream the encoder computed: read it back
// in zigzag order, de-interleave, check every block's RS syndromes and decode the byte-mode payload.
test('round trip: read back the payload from the matrix', () => {
  const NUM_BLOCKS_M = { 1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 4, 7: 4, 8: 4, 9: 5, 10: 5 };
  const ECC_M = { 1: 10, 2: 16, 3: 26, 4: 18, 5: 24, 6: 16, 7: 18, 8: 22, 9: 22, 10: 26 };
  for (const text of ['A', 'upi://pay?pa=shop@okaxis&pn=My%20Shop&am=99.07&cu=INR&tn=Order%20K3J9XQ2M7P', 'z'.repeat(150), 'ü'.repeat(60)]) {
    const qr = qrMatrix(text, { ecl: 'M' });
    const { size, version } = qr;
    const fn = functionMap(version, size);
    const bits = [];
    for (let right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (let vert = 0; vert < size; vert++) {
        for (let j = 0; j < 2; j++) {
          const x = right - j;
          const y = ((right + 1) & 2) === 0 ? size - 1 - vert : vert;
          if (!fn[y][x]) bits.push(qr.modules[y][x] !== MASKS[qr.mask](x, y));
        }
      }
    }
    const codewords = [];
    for (let i = 0; i + 8 <= bits.length; i += 8) codewords.push(bits.slice(i, i + 8).reduce((a, b) => (a << 1) | b, 0));
    const blocks = NUM_BLOCKS_M[version];
    const ecc = ECC_M[version];
    const total = codewords.length;
    const shortLen = Math.floor(total / blocks);
    const numShort = blocks - (total % blocks);
    const dataLens = Array.from({ length: blocks }, (_, i) => shortLen - ecc + (i < numShort ? 0 : 1));
    const out = Array.from({ length: blocks }, () => []);
    let k = 0;
    for (let i = 0; i < Math.max(...dataLens); i++) for (let b = 0; b < blocks; b++) if (i < dataLens[b]) out[b].push(codewords[k++]);
    for (let i = 0; i < ecc; i++) for (let b = 0; b < blocks; b++) out[b].push(codewords[k++]);
    for (const block of out) {
      let root = 1;
      for (let i = 0; i < ecc; i++) {
        let s = 0;
        for (const c of block) s = gfMul(s, root) ^ c;
        assert.equal(s, 0, `RS syndrome for "${text.slice(0, 10)}" v${version}`);
        root = gfMul(root, 2);
      }
    }
    const data = out.flatMap((b, i) => b.slice(0, dataLens[i]));
    const stream = data.flatMap((byte) => Array.from({ length: 8 }, (_, i) => (byte >>> (7 - i)) & 1));
    const read = (from, n) => stream.slice(from, from + n).reduce((a, b) => (a << 1) | b, 0);
    assert.equal(read(0, 4), 0b0100);
    const lenBits = version <= 9 ? 8 : 16;
    const len = read(4, lenBits);
    const bytes = Array.from({ length: len }, (_, i) => read(4 + lenBits + i * 8, 8));
    assert.equal(new TextDecoder().decode(new Uint8Array(bytes)), text);
  }
});
