import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scanPaths } from '../src/index.js';

const root = new URL('..', import.meta.url).pathname;

test('the scanner passes its own scan (src, bin) with nothing at medium or above', async () => {
  const result = await scanPaths(['src', 'bin'], { cwd: root, minSeverity: 'medium' });
  assert.ok(result.filesScanned >= 10);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.findings.map((f) => `${f.file}:${f.line} ${f.ruleId}`), []);
});
