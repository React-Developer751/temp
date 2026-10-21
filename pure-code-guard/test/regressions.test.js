// Each test pins a false positive (or miss) found by running the scanner on real projects.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { scanPaths } from '../src/index.js';
import { looksMinified } from '../src/engine.js';
import { fake, has, scan } from './helpers.js';

test('JSX text and prose with curly quotes / dashes is not "code"', () => {
  for (const [code, filename] of [
    ['<T v="small">“{preview}”</T>', 'a.tsx'],
    ['<div className="v">—</div>', 'a.tsx'],
    ['<option value="">— Not sent —</option>', 'a.js'],
    ['<b>0 – {qty} {unit}</b>', 'a.jsx'],
    ['<p>Everyone is tagged “{tag}”.</p>', 'a.js'],
  ]) assert.ok(!has(code, 'ai/smart-punctuation', { filename }), code);
});

test('a BOM-stripping regex may contain U+FEFF', () => {
  assert.ok(!has('const clean = text.replace(/^﻿/, "");', 'ai/invisible-char'));
  assert.ok(has('const na​me = 1;', 'ai/invisible-char'), 'still caught elsewhere');
});

test('db.exec() / regex.exec() are not shell commands; child_process.exec is', () => {
  assert.ok(!has('conn.exec(`ALTER TABLE t ADD COLUMN ${name} REAL`);', 'security/command-injection'));
  assert.ok(!has('const m = re.exec(`${a}-${b}`);', 'security/command-injection'));
  assert.ok(has('child_process.exec(`git log ${branch}`);', 'security/command-injection'));
  assert.ok(has('cp.execSync("ls " + dir);', 'security/command-injection'));
  assert.ok(has('exec(`git log ${branch}`);', 'security/command-injection'));
  assert.ok(has('await exec(`git log ${branch}`);', 'security/command-injection'));
});

test('SQL: constants and literal ternaries are not injection; parameterised queries with a fragment are medium', () => {
  assert.ok(!has('db.query(`SELECT * FROM calls WHERE status IN ${ACTIVE_SQL}`);', 'security/sql-injection'));
  assert.ok(!has('db.query(`SELECT * FROM t WHERE a = ?${campaignId ? " AND c = ?" : ""}`, [a]);', 'security/sql-injection'));
  const f = scan('db.prepare(`SELECT COUNT(*) AS n FROM leads l WHERE ${clause}`).get(...params);').find((x) => x.ruleId === 'security/sql-injection');
  assert.equal(f.severity, 'medium');
  assert.match(f.message, /parameterised/);
  const bad = scan('db.query(`SELECT * FROM t WHERE id = ${req.params.id}`);').find((x) => x.ruleId === 'security/sql-injection');
  assert.equal(bad.severity, 'high');
});

test('sha1/md5 is low for cache keys, medium near secrets or tokens', () => {
  assert.equal(scan("const k = crypto.createHash('sha1').update(file).digest('hex');").find((f) => f.ruleId === 'security/weak-crypto').severity, 'low');
  assert.equal(scan("const sig = crypto.createHash('sha1').update(base + secret).digest('hex');").find((f) => f.ruleId === 'security/weak-crypto').severity, 'medium');
});

test('*_id names are identifiers, not secrets (Google service account private_key_id)', () => {
  assert.ok(!has('{ "private_key_id": "d3321a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f" }', 'security/hardcoded-secret', { filename: 'sa.json' }));
  assert.ok(has('{ "private_key": "-----BEGIN PRIVATE KEY-----\\nabc" }', 'security/hardcoded-secret', { filename: 'sa.json' }));
});

test('the same secret repeated in a file is reported once, with the other lines listed', () => {
  const pwd = 'Xk9#mP2$vL8@qR4z';
  const src = Array.from({ length: 8 }, (_, i) => `transport${i}({ auth: { pass: "${pwd}" } });`).join('\n');
  const found = scan(src).filter((f) => f.ruleId === 'security/hardcoded-secret');
  assert.equal(found.length, 1);
  assert.equal(found[0].occurrences, 8);
  assert.match(found[0].message, /also at lines 2, 3, 4, 5, 6, \+2 more/);
  assert.ok(!JSON.stringify(found).includes(pwd));
  const different = scan('a({ pass: "Xk9#mP2$vL8@qR4z" });\nb({ pass: "Zq7!rT5&nB3*wY1u" });').filter((f) => f.ruleId === 'security/hardcoded-secret');
  assert.equal(different.length, 2, 'different values stay separate');
});

test('looksMinified: bundles yes, normal and long-data files no', () => {
  assert.equal(looksMinified('a();\n'.repeat(1000)), false);
  assert.equal(looksMinified(`${'function a(b){return b+1}'.repeat(500)}\n`), true);
  const dataLine = `const blob = "${'x'.repeat(8000)}";\n`;
  assert.equal(looksMinified(`${'const a = 1;\n'.repeat(500)}${dataLine}`), false, 'one long data line in an otherwise normal file');
  assert.equal(looksMinified('tiny'), false);
});

test('scanPaths skips minified bundles unless includeMinified', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'pure-guard-min-'));
  try {
    await mkdir(join(dir, 'assets'));
    await writeFile(join(dir, 'assets/bundle.js'), `${'function a(b){return new Function("x",b)}'.repeat(300)}\n`);
    await writeFile(join(dir, 'app.js'), 'eval(x);\n');
    const normal = await scanPaths(['.'], { cwd: dir });
    assert.deepEqual(normal.findings.map((f) => f.file), ['app.js']);
    assert.deepEqual(normal.skipped, [{ file: 'assets/bundle.js', reason: 'minified or bundled' }]);
    const all = await scanPaths(['.'], { cwd: dir, includeMinified: true });
    assert.ok(all.findings.some((f) => f.file === 'assets/bundle.js'));
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('known-format secrets still found when the variable name says nothing', () => {
  assert.ok(has(`transporter.send({ x: "${fake.github()}" });`, 'security/hardcoded-secret'));
});

test('names: author / tokenizers / passport are not secrets; accessToken / AUTH_KEY still are', () => {
  const v = fake.highEntropy();
  for (const name of ['author', 'tokenizers', 'passport', 'secretary', 'authority']) {
    assert.ok(!has(`const ${name} = "${v}";`, 'security/hardcoded-secret'), name);
  }
  for (const name of ['accessToken', 'AUTH_KEY', 'authorization', 'basic_auth', 'clientSecret']) {
    assert.ok(has(`const ${name} = "${v}";`, 'security/hardcoded-secret'), name);
  }
});

test('PascalCase enum values and documentation fillers are not secrets', () => {
  assert.ok(!has('AndroidKeystoreBuildCredentials = "AndroidKeystoreBuildCredentials",', 'security/hardcoded-secret'));
  assert.ok(!has('const smtpPass = "abcdefghijklmnop";', 'security/hardcoded-secret'));
  assert.ok(!has('const password = "12345678901";', 'security/hardcoded-secret'));
  assert.ok(has('const smtpPass = "qwXe9rTy2uIo5pAs";', 'security/hardcoded-secret'), 'random value is still caught');
});

test('innerHTML with a literal that contains ";" is not XSS', () => {
  assert.ok(!has('form.innerHTML = "&gt;&gt;&gt; ";', 'security/xss'));
  assert.ok(!has("el.innerHTML = '<p>a; b</p>'\nnext();", 'security/xss'));
  assert.ok(has('el.innerHTML = "<p>" + name + "; </p>";', 'security/xss'));
  assert.ok(has('el.innerHTML = "<p>x</p>" + more;', 'security/xss'));
});

test('curly quotes inside files that contain JSX are prose; in plain code they are errors', () => {
  const jsxInJs = 'export default function A() {\n  return <p>Removing it moves leads to the first status (“New”).</p>;\n}\nconst x = f(“bad”);\n';
  assert.ok(!has(jsxInJs, 'ai/smart-punctuation', { filename: 'page.js' }));
  assert.ok(has('const x = f(“bad”);\n', 'ai/smart-punctuation', { filename: 'plain.js' }));
});

test('null-chain: Express middleware props are fine, nested payload fields are not, tests are exempt', () => {
  const CHAIN = 'crash/unsafe-property-chain';
  assert.ok(!has('use(req.user._id.toString());', CHAIN));
  assert.ok(!has('use(req.tenant.settings.waRates);', CHAIN));
  assert.ok(!has('use(req.body.name);', CHAIN));
  assert.ok(has('use(req.body.user.name);', CHAIN));
  assert.ok(!has('const c = await getCall();\nuse(c.tags.includes("x"));', CHAIN, { filename: 'tests/a.mjs' }));
  assert.ok(!has('const x = JSON.parse(s);', 'crash/unguarded-json-parse', { filename: 'test/a.js' }));
});

test('null-chain severity: medium for certain external data, low when guessed from a name or helper', () => {
  const sev = (code) => scan(code).find((f) => f.ruleId === 'crash/unsafe-property-chain')?.severity;
  assert.equal(sev('const j = JSON.parse(raw);\nuse(j.a.b);'), 'medium');
  assert.equal(sev('const r = await fetch(u).then((x) => x.json());\nuse(r.a.b);'), 'medium');
  assert.equal(sev('const { data } = await axios.get(u);\nuse(data.items.length);'), 'medium');
  assert.equal(sev('use(req.body.user.name);'), 'medium');
  assert.equal(sev('function f(user) { return user.profile.name; }'), 'low');
  assert.equal(sev('const u = await getUser();\nuse(u.profile.name);'), 'low');
});

test('hardcoded credential COMPARISONS are found: password === "…", token !== "…"', () => {
  const v = 'Xk9#mP2$vL8@qR4z';
  for (const op of ['===', '==', '!==', '!=']) {
    assert.ok(has(`if (email === "a@b.co" && password ${op} "${v}") { grant(); }`, 'security/hardcoded-secret'), op);
  }
  assert.ok(has(`if (req.body.password === "${v}") ok();`, 'security/hardcoded-secret'));
  assert.ok(!has('if (type === "password") ok();', 'security/hardcoded-secret'), 'comparing a field name is fine');
  assert.ok(!has('if (password === "changeme") warn();', 'security/hardcoded-secret'));
  assert.ok(!has('if (a >= "Xk9#mP2$vL8@qR4z") ok();', 'security/hardcoded-secret'), 'only equality comparisons');
});
