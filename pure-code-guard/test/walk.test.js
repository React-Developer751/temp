import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { scanPaths } from '../src/index.js';
import { globToRegExp, makeIgnore } from '../src/walk.js';
import { fake } from './helpers.js';

let root;

before(async () => {
  root = await mkdtemp(join(tmpdir(), 'pure-guard-'));
  const files = {
    'src/app.js': 'eval(x);\n',
    'src/deep/util.ts': 'try { a(); } catch (e) {}\n',
    'src/clean.js': 'export const a = 1;\n',
    'node_modules/dep/index.js': 'eval(x);\n',
    'dist/bundle.js': 'eval(x);\n',
    'src/app.min.js': 'eval(x);\n',
    'package-lock.json': `{"integrity": "sha512-${'A1b2C3d4'.repeat(10)}"}`,
    'src/notes.md': `token ${fake.github()}`,
    'src/image.png': 'binary-ish',
    '.env': 'DB_PASSWORD=Xk9#mP2$vL8@qR4z\n',
    'big.js': `${'a();\n'.repeat(500)}eval(x);\n`,
    'ignored-by-user/x.js': 'eval(x);\n',
  };
  for (const [name, content] of Object.entries(files)) {
    await mkdir(join(root, name, '..'), { recursive: true });
    await writeFile(join(root, name), content);
  }
  await writeFile(join(root, 'src/binary.js'), Buffer.from([0x65, 0x76, 0x00, 0x61, 0x6c]));
  await symlink(join(root, 'src'), join(root, 'loop-link')).catch(() => {});
});

after(() => rm(root, { recursive: true, force: true }));

const files = (result) => [...new Set(result.findings.map((f) => f.file))].sort();

test('walks directories, skips node_modules/dist/minified/lockfiles/non-code', async () => {
  const result = await scanPaths(['.'], { cwd: root, ignore: ['ignored-by-user'] });
  assert.deepEqual(files(result), ['.env', 'big.js', 'src/app.js', 'src/deep/util.ts']);
  assert.deepEqual(result.errors, []);
});

test('binary files and oversized files are skipped with a reason', async () => {
  const result = await scanPaths(['src', 'big.js'], { cwd: root, maxFileSize: 1000 });
  assert.ok(result.skipped.some((s) => s.file === 'src/binary.js' && s.reason === 'binary file'));
  assert.ok(result.skipped.some((s) => s.file === 'big.js' && /larger than/.test(s.reason)));
  assert.ok(!files(result).includes('big.js'));
});

test('symlinks are never followed', async () => {
  const result = await scanPaths(['.'], { cwd: root });
  assert.ok(!result.findings.some((f) => f.file.startsWith('loop-link')));
});

test('explicit file paths are scanned even if the extension is unusual', async () => {
  const result = await scanPaths(['src/notes.md'], { cwd: root });
  assert.equal(result.filesScanned, 1);
  assert.equal(result.findings[0].ruleId, 'security/hardcoded-secret');
});

test('missing path is reported as an error, not a crash', async () => {
  const result = await scanPaths(['nope.js', 'src/clean.js'], { cwd: root });
  assert.equal(result.errors.length, 1);
  assert.match(result.errors[0].message, /no such file/);
  assert.equal(result.filesScanned, 1);
});

test('engine/severity options flow through', async () => {
  const result = await scanPaths(['src'], { cwd: root, engines: ['crash'] });
  assert.deepEqual(files(result), ['src/deep/util.ts']);
});

test('glob matching', () => {
  const m = (glob, path) => globToRegExp(glob).test(path);
  assert.ok(m('*.js', 'a.js') && !m('*.js', 'dir/a.js'));
  assert.ok(m('**/*.js', 'a/b/c.js') && m('**/*.js', 'c.js'));
  assert.ok(m('src/**', 'src/a/b'));
  assert.ok(m('a?.js', 'ab.js') && !m('a?.js', 'a/.js'));
  assert.ok(m('a.b', 'a.b') && !m('a.b', 'axb'), 'dots are literal');

  const ignored = makeIgnore(['node_modules', '*.min.js', 'src/generated', 'docs/**/*.js']);
  assert.ok(ignored('node_modules') && ignored('a/node_modules/x.js'));
  assert.ok(ignored('lib/a.min.js'));
  assert.ok(ignored('src/generated') && ignored('src/generated/a.js'));
  assert.ok(!ignored('other/src/generated2/a.js'));
  assert.ok(ignored('docs/a/b.js') && !ignored('docs/a/b.ts'));
});

test('files outside the working directory are reported with their absolute path, not ../../..', async () => {
  const inner = join(root, 'src');
  const result = await scanPaths([join(root, 'src/app.js')], { cwd: inner });
  assert.equal(result.findings[0].file, 'app.js');
  const outside = await scanPaths([join(root, 'src/app.js')], { cwd: join(root, 'src/deep') });
  assert.equal(outside.findings[0].file, join(root, 'src/app.js'));
  assert.ok(!outside.findings[0].file.includes('..'));
});
