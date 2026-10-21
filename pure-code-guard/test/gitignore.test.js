import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { scanPaths } from '../src/index.js';
import { createGitIgnore, parseGitIgnore } from '../src/gitignore.js';
import { fake } from './helpers.js';

let root;
const secretLine = () => `API_TOKEN=${fake.github()}\n`;

before(async () => {
  root = await mkdtemp(join(tmpdir(), 'pure-guard-git-'));
  await mkdir(join(root, '.git'));
  await writeFile(join(root, '.gitignore'), '# local\n.env\n.env.local\nbackups/\n/secret-root.json\n*.log\n!keep.log\nbuild-*/\n');
  for (const d of ['sub', 'backups/old', 'build-1', 'other']) await mkdir(join(root, d), { recursive: true });
  await writeFile(join(root, 'sub/.gitignore'), 'local.json\n');
  const files = {
    '.env': secretLine(), '.env.production': secretLine(), 'config.json': `{"apiKey": "${fake.highEntropy()}"}`,
    'backups/old/.env': secretLine(), 'secret-root.json': secretLine(), 'sub/secret-root.json': secretLine(),
    'sub/local.json': `{"token": "${fake.highEntropy()}"}`, 'other/local.json': `{"token": "${fake.highEntropy()}"}`,
    'build-1/x.env': secretLine(), 'app.js': 'eval(x);\n', 'backups/old/app.js': 'eval(x);\n',
  };
  for (const [name, content] of Object.entries(files)) await writeFile(join(root, name), content);
});

after(() => rm(root, { recursive: true, force: true }));

test('parseGitIgnore: comments, negation, directory-only and anchoring', () => {
  const rules = parseGitIgnore('# c\n\n!keep\nbuild/\n/root\ndir/file\n');
  assert.deepEqual(rules.map((r) => [r.negate, r.dirOnly, r.anchored]), [[true, false, false], [false, true, false], [false, false, true], [false, false, true]]);
});

test('isIgnored follows .gitignore semantics', async () => {
  const gi = await createGitIgnore(root);
  const ign = (p, dir = false) => gi.isIgnored(join(root, p), dir);
  assert.equal(await ign('.env'), true);
  assert.equal(await ign('.env.production'), false);
  assert.equal(await ign('config.json'), false);
  assert.equal(await ign('backups/old/.env'), true, 'inside an ignored directory');
  assert.equal(await ign('secret-root.json'), true);
  assert.equal(await ign('sub/secret-root.json'), false, 'leading / anchors to the root');
  assert.equal(await ign('sub/local.json'), true, 'nested .gitignore');
  assert.equal(await ign('other/local.json'), false, 'nested .gitignore only applies below it');
  assert.equal(await ign('build-1/x.env'), true);
  assert.equal(await ign('x.log'), true);
  assert.equal(await ign('keep.log'), false, 'negation');
});

test('no repository: nothing is ignored', async () => {
  const bare = await mkdtemp(join(tmpdir(), 'pure-guard-nogit-'));
  try {
    assert.equal(await createGitIgnore(bare), null);
  } finally {
    await rm(bare, { recursive: true, force: true });
  }
});

const find = (result, file) => result.findings.filter((f) => f.file === file);

test('default: findings in git-ignored files are downgraded and labelled; tracked files keep full severity', async () => {
  const result = await scanPaths(['.'], { cwd: root, minSeverity: 'low' });
  const ignoredEnv = find(result, '.env');
  assert.ok(ignoredEnv.length > 0);
  assert.ok(ignoredEnv.every((f) => f.gitIgnored === true && f.severity === 'medium'));
  assert.match(ignoredEnv[0].message, /git-ignored/);
  const tracked = find(result, '.env.production');
  assert.ok(tracked.length > 0 && tracked.every((f) => f.severity === 'critical' && !f.gitIgnored));
  assert.ok(find(result, 'config.json').every((f) => f.severity === 'high'));
  assert.ok(find(result, 'app.js').some((f) => f.ruleId === 'security/eval' && f.severity === 'high'));
  const ignoredCode = find(result, 'backups/old/app.js');
  assert.ok(ignoredCode.every((f) => f.severity === 'low' && f.gitIgnored));
});

test('--gitignored skip / include', async () => {
  const skip = await scanPaths(['.'], { cwd: root, gitIgnored: 'skip' });
  assert.ok(!skip.findings.some((f) => f.file === '.env' || f.file.startsWith('backups/')));
  assert.ok(skip.skipped.some((s) => s.file === '.env' && s.reason === 'git-ignored'));
  const include = await scanPaths(['.'], { cwd: root, gitIgnored: 'include' });
  assert.ok(find(include, '.env').every((f) => f.severity === 'critical' && !f.gitIgnored));
  await assert.rejects(scanPaths(['.'], { cwd: root, gitIgnored: 'maybe' }), RangeError);
});

test('minSeverity applies after the downgrade', async () => {
  const result = await scanPaths(['.'], { cwd: root, minSeverity: 'high' });
  assert.ok(!result.findings.some((f) => f.file === 'backups/old/app.js'));
  assert.ok(!result.findings.some((f) => f.file === '.env'));
});
