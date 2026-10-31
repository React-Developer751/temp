import { test } from 'node:test';
import assert from 'node:assert/strict';
import { tokenize } from '../src/index.js';

const mask = (src) => tokenize(src).masked;

test('masks comments and string contents but keeps code and offsets', () => {
  const src = 'const a = "x" + y; // note\n/* b\nc */ let z = \'q\';';
  const m = mask(src);
  assert.equal(m.length, src.length);
  assert.equal(m.split('\n').length, src.split('\n').length);
  assert.equal(m, 'const a = " " + y;        \n    \n     let z = \' \';');
});

test('collects comments and strings with positions', () => {
  const t = tokenize('x = "hi"; // c1\n/* c2 */');
  assert.deepEqual(t.comments.map((c) => c.text), [' c1', ' c2 ']);
  assert.equal(t.strings[0].value, 'hi');
  assert.deepEqual(t.position(t.strings[0].start), { line: 1, column: 5 });
});

test('escaped quotes do not end a string', () => {
  const t = tokenize('a = "he said \\"hi\\""; b = 1;');
  assert.equal(t.strings.length, 1);
  assert.equal(t.strings[0].value, 'he said \\"hi\\"');
  assert.ok(t.masked.includes('b = 1;'));
});

test('template literals: static text masked, ${} expressions stay code, nesting works', () => {
  const src = 'x = `a ${b + `c ${d}`} e`; f();';
  const t = tokenize(src);
  assert.ok(t.masked.includes('b + '));
  assert.ok(t.masked.includes('d'));
  assert.ok(t.masked.endsWith('f();'));
  assert.ok(!t.masked.includes('a '));
  assert.equal(t.masked.length, src.length);
  const outer = t.strings.find((s) => s.start === src.indexOf('`'));
  assert.equal(outer.hasExpr, true);
  assert.equal(outer.exprs.length, 1);
  assert.ok(!t.masked.includes('${'), 'template delimiters are blanked so braces stay balanced');
});

test('tagged templates are marked', () => {
  const t = tokenize('const q = sql`SELECT ${id}`; const r = `plain ${id}`;');
  assert.deepEqual(t.strings.map((s) => s.tagged), [true, false]);
  assert.equal(tokenize('return `x ${y}`').strings[0].tagged, false);
});

test('regex literal vs division', () => {
  const t = tokenize('a = b / c / d; e = /x\\/y[/]z/gi.test(s); f = (1) / 2; g = i++ / 2;');
  assert.equal(t.regexes.length, 1);
  assert.equal(t.regexes[0].body, 'x\\/y[/]z');
  assert.equal(t.regexes[0].flags, 'gi');
});

test('regex after return / typeof / operators', () => {
  assert.equal(tokenize('return /a+b/.test(x)').regexes.length, 1);
  assert.equal(tokenize('x = y || /re/;').regexes.length, 1);
  assert.equal(tokenize('if (ok) { /re/.test(s) }').regexes.length, 1);
});

test('comment markers inside strings, regexes and templates are not comments', () => {
  const t = tokenize('u = "http://x.test"; r = /\\/\\//; t = `// not ${"/* a */"} comment`; real(); // yes');
  assert.deepEqual(t.comments.map((c) => c.text), [' yes']);
});

test('unterminated string ends at the line break; later code is still seen', () => {
  const t = tokenize('a = "oops\nb = eval(x);\n');
  assert.ok(t.masked.includes('eval(x)'));
});

test('unterminated template / comment / regex do not hang or throw', () => {
  for (const src of ['`abc ${', 'x = `abc', '/* never closed', 'a = /[unclosed', '"', "'", '`', '${', '/', '//', '#!']) {
    const t = tokenize(src);
    assert.equal(t.masked.length, src.length, JSON.stringify(src));
  }
});

test('hashbang is masked', () => {
  assert.ok(!mask('#!/usr/bin/env node\nrun();').includes('env'));
});

test('unicode source keeps length (astral characters)', () => {
  const src = 'x = "😀 emoji"; // 🎉\ny = 1;';
  const t = tokenize(src);
  assert.equal(t.masked.length, src.length);
  assert.ok(t.masked.endsWith('y = 1;'));
});

test('fuzz: random garbage never throws, never hangs, always preserves length and line count', () => {
  let seed = 12345;
  const rand = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 2 ** 32;
  const alphabet = ['`', '"', "'", '/', '*', '\\', '$', '{', '}', '(', ')', '[', ']', '\n', ' ', 'a', 'b', '1', '=', '+', '<', '>', ';', '😀', '#', '!'];
  for (let n = 0; n < 3000; n++) {
    let src = '';
    const len = Math.floor(rand() * 60);
    for (let k = 0; k < len; k++) src += alphabet[Math.floor(rand() * alphabet.length)];
    const t = tokenize(src);
    assert.equal(t.masked.length, src.length, JSON.stringify(src));
    assert.equal(t.masked.split('\n').length, src.split('\n').length, JSON.stringify(src));
  }
});

test('performance: 2 MB of code tokenizes quickly', () => {
  const src = 'const s = "string"; // comment\nfoo(`t ${a}`, /re/g);\n'.repeat(40_000);
  const t0 = performance.now();
  tokenize(src);
  assert.ok(performance.now() - t0 < 3000, `took ${performance.now() - t0}ms`);
});
