import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ENGINES, RULES, classify, formatJson, formatSarif, formatText, scanSource } from '../src/index.js';
import { fake, ids, scan } from './helpers.js';

const BAD = 'try { x(); } catch (e) {}\neval(y);\nconst s = text.split("\\n");\n';

test('rule catalogue: unique ids, prefix matches engine, every rule has a description', () => {
  assert.equal(new Set(RULES.map((r) => r.id)).size, RULES.length);
  for (const r of RULES) {
    assert.ok(ENGINES.includes(r.engine), r.id);
    assert.ok(r.id.startsWith(`${r.engine}/`), r.id);
    assert.ok(r.description.length > 10, r.id);
    assert.ok(['low', 'medium', 'high', 'critical'].includes(r.severity), r.id);
  }
});

test('finding shape: location, snippet, fix and a stable fingerprint', () => {
  const [f] = scan('\n\n  eval(code);');
  assert.equal(f.ruleId, 'security/eval');
  assert.equal(f.engine, 'security');
  assert.equal(f.file, 'app.js');
  assert.equal(f.line, 3);
  assert.equal(f.column, 3);
  assert.equal(f.snippet, 'eval(code);');
  assert.match(f.fingerprint, /^[0-9a-f]{16}$/);
  assert.equal(scan('\n\n\n\n  eval(code);')[0].fingerprint, f.fingerprint, 'fingerprint ignores line numbers');
});

test('engines option limits which engines run', () => {
  assert.deepEqual([...new Set(scan(BAD).map((f) => f.engine))].sort(), ['ai', 'crash', 'security']);
  assert.deepEqual([...new Set(scan(BAD, { engines: ['crash'] }).map((f) => f.engine))], ['crash']);
  assert.throws(() => scan(BAD, { engines: ['nope'] }), RangeError);
});

test('rulesOff and minSeverity', () => {
  assert.ok(!ids(BAD, { rulesOff: ['security/eval'] }).includes('security/eval'));
  assert.throws(() => scan(BAD, { rulesOff: ['security/nope'] }), RangeError);
  assert.ok(scan(BAD, { minSeverity: 'high' }).every((f) => ['high', 'critical'].includes(f.severity)));
  assert.throws(() => scan(BAD, { minSeverity: 'severe' }), RangeError);
});

test('findings are sorted by position', () => {
  const lines = scan(BAD).map((f) => f.line);
  assert.deepEqual(lines, [...lines].sort((a, b) => a - b));
});

test('classify', () => {
  for (const f of ['a.js', 'a.mjs', 'a.ts', 'a.tsx', 'a.cjs']) assert.equal(classify(f), 'code', f);
  for (const f of ['.env', '.env.production', 'a.json', 'a.yml', 'Dockerfile', 'id.pem']) assert.equal(classify(f), 'text', f);
  for (const f of ['a.png', 'a.md', 'a.css', 'a.lock']) assert.equal(classify(f), null, f);
});

test('empty input and CRLF sources', () => {
  assert.deepEqual(scan(''), []);
  const f = scan('a();\r\neval(x);\r\n').find((x) => x.ruleId === 'security/eval');
  assert.equal(f.line, 2);
  assert.equal(f.snippet, 'eval(x);');
});

test('TypeScript syntax does not confuse the lexer', () => {
  const ts = 'interface A { x: Array<string>; }\nconst f = <T,>(a: T): T => a;\nconst r = a < b ? 1 : 2;\neval(c as string);\n';
  assert.deepEqual(ids(ts, { filename: 'a.ts' }), ['security/eval']);
});

test('formatters: text, json, sarif', () => {
  const result = { findings: scan(BAD), filesScanned: 1, skipped: [], errors: [] };
  const text = formatText(result);
  assert.match(text, /app\.js/);
  assert.match(text, /security\/eval/);
  assert.match(text, /issue\(s\)/);
  assert.match(formatText({ findings: [], filesScanned: 3, skipped: [], errors: [] }), /No issues found in 3 file/);
  assert.ok(formatText(result, { color: true }).includes('\x1b['));
  assert.ok(!formatText(result, { color: false }).includes('\x1b['));

  const json = JSON.parse(formatJson(result));
  assert.equal(json.findings.length, result.findings.length);
  assert.equal(json.summary.high >= 1, true);

  const sarif = JSON.parse(formatSarif(result, '1.2.3'));
  assert.equal(sarif.version, '2.1.0');
  assert.equal(sarif.runs[0].tool.driver.version, '1.2.3');
  assert.equal(sarif.runs[0].results.length, result.findings.length);
  assert.ok(sarif.runs[0].tool.driver.rules.length === RULES.length);
  const r = sarif.runs[0].results[0];
  assert.ok(r.locations[0].physicalLocation.region.startLine >= 1);
  assert.ok(['error', 'warning', 'note'].includes(r.level));
});

test('no report format ever contains a full secret', () => {
  const token = fake.github();
  const findings = scanSource(`const t = "${token}";`, { filename: 'a.js' });
  const result = { findings, filesScanned: 1, skipped: [], errors: [] };
  for (const out of [formatText(result), formatJson(result), formatSarif(result)]) assert.ok(!out.includes(token));
});

test('performance: a 1 MB file scans in a reasonable time', () => {
  const chunk = 'const value = compute(a, b);\nfunction f(x) { return x.y; }\n// a comment with words\nconst s = `template ${value} text`;\n';
  const source = chunk.repeat(Math.ceil(1_000_000 / chunk.length));
  const t0 = performance.now();
  scan(source);
  assert.ok(performance.now() - t0 < 5000, `took ${performance.now() - t0}ms`);
});
