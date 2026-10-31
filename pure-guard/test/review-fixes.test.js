// Regressions for issues found in the pre-publish review (JSX lexing, false positives, misses, I/O edge cases).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { scanPaths } from '../src/index.js';
import { formatSarif } from '../src/report.js';
import { fake, has, ids, scan } from './helpers.js';

const jsx = { filename: 'App.jsx' };

test('JSX: closing tags, apostrophes and backticks in text do not hide real code', () => {
  assert.ok(has('const A = () => <div><b>hi</b>{eval(x)}<i>y</i></div>;', 'security/eval', jsx));
  assert.ok(has("const B = () => <p>Don't {eval(y)}</p>;", 'security/eval', jsx));
  assert.ok(has("const C = () => <p>it's <span dangerouslySetInnerHTML={{ __html: h }} /></p>;", 'security/xss', jsx));
  // A backtick in JSX text used to swallow the rest of the file.
  assert.ok(has('const D = () => <p>Press the ` key</p>;\neval(z);', 'security/eval', jsx));
});

test('JSX: attribute strings are checked for secrets; TSX generic arrows are not JSX', () => {
  assert.ok(has(`const M = <Map apiKey="${fake.awsKey()}" />;`, 'security/hardcoded-secret', jsx));
  assert.ok(has('const id = <T,>(v: T) => v;\neval(x);', 'security/eval', { filename: 'a.tsx' }));
  // .ts files: <T>value is a type assertion
  assert.ok(has('const n = <number>value;\neval(x);', 'security/eval', { filename: 'a.ts' }));
});

test('JSX: a non-breaking space in JSX text is content, not an invisible character in code', () => {
  assert.equal(has('const P = () => <p>5 € only</p>;', 'ai/invisible-char', jsx), false);
});

test('SQL: prose and HTML strings are not SQL; real fragments still are', () => {
  for (const safe of ["x = '<p>Tom and Jerry</p>' + name", "x = 'Logged in as <b>' + user", "x = 'Please set your name (' + n + ')'", "x = 'Price is > ' + p"]) {
    assert.equal(has(safe, 'security/sql-injection'), false, safe);
  }
  for (const bad of ["q = ' AND age > ' + age", "q = \" WHERE name LIKE '%\" + s", "q = ' OR id IN (' + ids", "q = ' LIMIT ' + n"]) {
    assert.ok(has(bad, 'security/sql-injection'), bad);
  }
});

test('empty catch: a long whitespace/comment run is scanned in linear time', () => {
  const started = performance.now();
  scan(`try {} catch${' '.repeat(200_000)}{ g() }\ntry {} catch /*${'x'.repeat(200_000)}*/ { g() }`);
  assert.ok(performance.now() - started < 2000);
});

test('empty catch: any explanatory comment documents an intentional ignore', () => {
  assert.equal(has('try { a() } catch { /* the file may not exist yet */ }', 'crash/empty-catch'), false);
  assert.equal(has('try { a() } catch (e) { // keep as is\n}', 'crash/empty-catch'), false);
  assert.ok(has('try { a() } catch (e) { /* TODO */ }', 'crash/empty-catch'));
  assert.ok(has('try { a() } catch (e) {}', 'crash/empty-catch'));
});

test('secrets are redacted even when the secret rule is off', () => {
  const key = fake.awsKey();
  const src = `const apiKey = '${key}'; s.split('\\n');`;
  for (const options of [{ rulesOff: ['security/hardcoded-secret'] }, { engines: ['ai'] }]) {
    const out = JSON.stringify(scan(src, options));
    assert.ok(out.includes('split'), 'still reports the other finding');
    assert.equal(out.includes(key), false, JSON.stringify(options));
  }
});

test('injection patterns that were missed before', () => {
  assert.ok(has("require('child_process').exec(`ls ${d}`)", 'security/command-injection'));
  assert.ok(has("require('node:child_process').execSync('rm -rf ' + p)", 'security/command-injection'));
  assert.ok(has('await execAsync(`git log ${b}`)', 'security/command-injection'));
  assert.ok(has("jwt.sign(p, 'my-super-secret-jwt-key-2024')", 'security/hardcoded-secret'));
  assert.ok(has("crypto.createHmac('sha256', 'k3y-for-hmac-123')", 'security/hardcoded-secret'));
  assert.ok(has('window.eval(x)', 'security/eval'));
  assert.ok(has("Function('return ' + x)()", 'security/eval'));
  assert.equal(ids("new Function('a', body)").filter((id) => id === 'security/eval').length, 1);
  assert.equal(has('jwt.verify(token, process.env.JWT_SECRET)', 'security/hardcoded-secret'), false);
  assert.equal(has('re.exec(text)', 'security/command-injection'), false);
});

test('false positives that are gone', () => {
  assert.equal(has('el.innerHTML = DOMPurify.sanitize(x)', 'security/xss'), false);
  assert.equal(has('const C = () => <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(h) }} />', 'security/xss', jsx), false);
  assert.equal(has('const Δt = 1, μs = 2, αBeta = 3;', 'ai/homoglyph-identifier'), false);
  assert.ok(has('const pаssword = 1;', 'ai/homoglyph-identifier')); // Cyrillic "а"
  assert.equal(has("lines = s.split('\\n').map((l) => l.trim());", 'ai/split-newline'), false);
  assert.equal(has('async function f(u) { const response = await fetch(u); return response.headers.get("x"); }', 'crash/unsafe-property-chain', { minSeverity: 'low' }), false);
  assert.ok(has('async function f(u) { const data = await fetch(u).then((r) => r.json()); return data.user.name; }', 'crash/unsafe-property-chain', { minSeverity: 'low' }));
});

test('a suppression with a prose reason ignores the next line', () => {
  assert.equal(has('// pure-guard-ignore because the input is trusted\neval(x)', 'security/eval'), false);
  assert.ok(has('// pure-guard-ignore security/xss\neval(x)', 'security/eval'), 'a different rule id does not suppress');
});

test('scanPaths: string path, followed top-level symlink, cwd-relative --ignore, listed build folders', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'pure-guard-review-'));
  try {
    await mkdir(join(dir, 'real'));
    await mkdir(join(dir, 'sub/deep'), { recursive: true });
    await mkdir(join(dir, 'src/build'), { recursive: true });
    await writeFile(join(dir, 'real/a.js'), 'eval(x);\n');
    await writeFile(join(dir, 'sub/b.js'), 'eval(x);\n');
    await writeFile(join(dir, 'sub/deep/c.js'), 'eval(x);\n');
    await writeFile(join(dir, 'src/build/h.js'), 'eval(x);\n');
    await symlink(join(dir, 'real'), join(dir, 'linkdir'));

    const one = await scanPaths('real', { cwd: dir });
    assert.deepEqual(one.findings.map((f) => f.file), ['real/a.js']);

    const linked = await scanPaths(['linkdir'], { cwd: dir });
    assert.equal(linked.filesScanned, 1);

    const ignored = await scanPaths(['sub'], { cwd: dir, ignore: ['sub/deep'] });
    assert.deepEqual(ignored.findings.map((f) => f.file), ['sub/b.js']);

    const src = await scanPaths(['src'], { cwd: dir });
    assert.deepEqual(src.skipped.map((s) => s.file), ['src/build']);
    const explicit = await scanPaths(['src/build'], { cwd: dir });
    assert.equal(explicit.findings.length, 1);

    await assert.rejects(scanPaths(42, { cwd: dir }), TypeError);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('SARIF: absolute paths become file:// URIs', () => {
  const finding = { ruleId: 'security/eval', severity: 'high', message: 'm', file: '/tmp/a b/x.js', line: 1, column: 1, endLine: 1, endColumn: 2, fingerprint: 'f' };
  const sarif = JSON.parse(formatSarif({ findings: [finding, { ...finding, file: 'src/a b.js' }], filesScanned: 2, skipped: [], errors: [] }));
  const uris = sarif.runs[0].results.map((r) => r.locations[0].physicalLocation.artifactLocation.uri);
  assert.deepEqual(uris, ['file:///tmp/a%20b/x.js', 'src/a%20b.js']);
});
