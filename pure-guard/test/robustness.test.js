import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scanSource } from '../src/index.js';

// Inputs built to trigger quadratic / catastrophic regex behaviour. Every one used to take 8-40s or hang at 200 KB.
const N = 100_000;
const ADVERSARIAL = {
  'one huge line': 'a'.repeat(N),
  'unterminated string': `x = "${'a'.repeat(N)}`,
  'quote soup': '"\'`'.repeat(N / 3),
  'select column list': `q = "select ${'a, '.repeat(N / 3)}"`,
  'select prose': `q = "select ${'a b '.repeat(N / 4)}"`,
  'where tail': `q = "where ${' and '.repeat(N / 5)}" + x`,
  'long property chain': `user${'.a'.repeat(N / 2)}`,
  'many opening braces': '{'.repeat(N),
  'many try blocks': 'try {'.repeat(N / 5),
  'many destructurings': 'const {'.repeat(N / 7),
  'many .catch( calls': '.catch(('.repeat(N / 8),
  'many .repeat( calls': '.repeat('.repeat(N / 8),
  'many imports': 'import {'.repeat(N / 8),
  'catch + huge whitespace': `catch (${' '.repeat(N)}) {`,
  'split + huge whitespace': `.split(${' '.repeat(N)}"`,
  'jwt prefix repeated': 'eyJ'.repeat(N / 3),
  'db url prefix repeated': 'postgres://a:'.repeat(N / 13),
  'bearer repeated': 'Bearer '.repeat(N / 7),
  'zero-width run': '​'.repeat(N),
  'deeply nested templates': '`${'.repeat(3000) + '}`'.repeat(3000),
  'slashes': '/'.repeat(N),
  'half-open regex classes': `x = /${'[a-'.repeat(N / 3)}`,
};

for (const [name, source] of Object.entries(ADVERSARIAL)) {
  for (const filename of ['a.js', '.env']) {
    test(`adversarial: ${name} (${filename}) is scanned quickly and never throws`, () => {
      const t0 = performance.now();
      assert.doesNotThrow(() => scanSource(source, { filename }));
      assert.ok(performance.now() - t0 < 1500, `took ${(performance.now() - t0).toFixed(0)}ms`);
    });
  }
}

test('minified-style single 600 KB line of code finishes in a few seconds', () => {
  const line = 'function a(b){return b.c.d?e(b):f("x"+b)}var g=JSON.parse(h);'.repeat(10_000);
  const t0 = performance.now();
  scanSource(line, { filename: 'bundle.js' });
  assert.ok(performance.now() - t0 < 4000, `took ${(performance.now() - t0).toFixed(0)}ms`);
});
