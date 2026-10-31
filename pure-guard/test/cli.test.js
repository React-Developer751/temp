import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Readable } from 'node:stream';
import { run } from '../src/cli.js';

const BIN = new URL('../bin/pure-guard.js', import.meta.url).pathname;
let dir;

before(async () => {
  dir = await mkdtemp(join(tmpdir(), 'pure-guard-cli-'));
  await mkdir(join(dir, 'src'));
  await writeFile(join(dir, 'src/bad.js'), 'eval(x);\ntry { a(); } catch (e) {}\nconst s = t.split("\\n");\n');
  await writeFile(join(dir, 'src/ok.js'), 'export const a = 1;\n');
  await writeFile(join(dir, 'src/medium.js'), 'const s = t.split("\\n");\n');
});

after(() => rm(dir, { recursive: true, force: true }));

function sink() {
  let text = '';
  return { write: (s) => { text += s; }, get text() { return text; }, isTTY: false };
}

async function cli(args, { stdin = '', cwd = dir } = {}) {
  const stdout = sink();
  const stderr = sink();
  const code = await run(args, { stdout, stderr, stdin: Readable.from([stdin]), cwd, env: {} });
  return { code, out: stdout.text, err: stderr.text };
}

test('findings at/above --fail-on (default high) exit 1', async () => {
  const r = await cli(['src/bad.js']);
  assert.equal(r.code, 1);
  assert.match(r.out, /security\/eval/);
});

test('clean files exit 0', async () => {
  const r = await cli(['src/ok.js']);
  assert.equal(r.code, 0);
  assert.match(r.out, /No issues found/);
});

test('--fail-on controls the exit code: medium-only findings pass at high, fail at medium, pass at never', async () => {
  assert.equal((await cli(['src/medium.js'])).code, 0);
  assert.equal((await cli(['src/medium.js', '--fail-on', 'medium'])).code, 1);
  assert.equal((await cli(['src/bad.js', '--fail-on', 'never'])).code, 0);
});

test('default path is the current directory', async () => {
  const r = await cli([]);
  assert.equal(r.code, 1);
  assert.match(r.out, /src\/bad\.js/);
});

test('--format json is valid JSON with a summary', async () => {
  const r = await cli(['src', '--format', 'json']);
  const data = JSON.parse(r.out);
  assert.equal(data.filesScanned, 3);
  assert.ok(data.findings.length >= 3);
  assert.ok(data.summary.high >= 2);
});

test('--format sarif is valid SARIF', async () => {
  const data = JSON.parse((await cli(['src', '--format', 'sarif'])).out);
  assert.equal(data.version, '2.1.0');
  assert.ok(data.runs[0].results.length >= 3);
});

test('--engine, --rule-off, --min-severity, --ignore', async () => {
  const crash = JSON.parse((await cli(['src', '--format', 'json', '--engine', 'crash'])).out);
  assert.ok(crash.findings.every((f) => f.engine === 'crash'));
  const off = JSON.parse((await cli(['src', '--format', 'json', '--rule-off', 'security/eval,ai/split-newline'])).out);
  assert.ok(!off.findings.some((f) => f.ruleId === 'security/eval' || f.ruleId === 'ai/split-newline'));
  const high = JSON.parse((await cli(['src', '--format', 'json', '--min-severity', 'high'])).out);
  assert.ok(high.findings.every((f) => ['high', 'critical'].includes(f.severity)));
  const ignored = JSON.parse((await cli(['src', '--format', 'json', '--ignore', 'bad.js', '--ignore', 'medium.js'])).out);
  assert.equal(ignored.findings.length, 0);
});

test('stdin with --stdin-filename', async () => {
  const r = await cli(['-', '--stdin-filename', 'x.js', '--format', 'json'], { stdin: 'eval(y);' });
  assert.equal(r.code, 1);
  assert.equal(JSON.parse(r.out).findings[0].file, 'x.js');
});

test('usage errors exit 2 with a helpful message', async () => {
  for (const args of [['--nope'], ['--format', 'xml'], ['--fail-on', 'bad'], ['--engine', 'x', 'src'], ['--min-severity', 'huge', 'src'], ['--rule-off', 'nope/nope', 'src'], ['--max-file-size', '-1']]) {
    const r = await cli(args);
    assert.equal(r.code, 2, args.join(' '));
    assert.match(r.err, /pure-guard:/, args.join(' '));
  }
});

test('missing path exits 2 and still reports', async () => {
  const r = await cli(['nope.js']);
  assert.equal(r.code, 2);
  assert.match(r.out, /no such file/);
});

test('--help, --version, --list-rules', async () => {
  assert.match((await cli(['--help'])).out, /Usage: pure-guard/);
  assert.match((await cli(['--version'])).out, /^\d+\.\d+\.\d+/);
  const list = (await cli(['--list-rules'])).out;
  assert.match(list, /security\/hardcoded-secret/);
  assert.match(list, /crash\/empty-catch/);
  assert.match(list, /ai\/split-newline/);
});

test('config file: used by default, validated, overridden by flags', async () => {
  await writeFile(join(dir, 'pure-guard.config.json'), JSON.stringify({ ignore: ['bad.js'], failOn: 'low', format: 'json' }));
  try {
    const r = await cli(['src']);
    assert.equal(JSON.parse(r.out).findings.every((f) => f.file !== 'src/bad.js'), true);
    assert.equal(r.code, 1, 'medium.js still fails at failOn=low');
    assert.equal((await cli(['src', '--fail-on', 'critical'])).code, 0, 'flag overrides config');

    await writeFile(join(dir, 'pure-guard.config.json'), JSON.stringify({ bogus: 1 }));
    const bad = await cli(['src']);
    assert.equal(bad.code, 2);
    assert.match(bad.err, /unknown key "bogus"/);

    await writeFile(join(dir, 'pure-guard.config.json'), '{ not json');
    assert.equal((await cli(['src'])).code, 2);
  } finally {
    await rm(join(dir, 'pure-guard.config.json'), { force: true });
  }
});

test('real process: shebang works, exit codes propagate, output has no ANSI when piped', () => {
  const bad = spawnSync(process.execPath, [BIN, 'src/bad.js'], { cwd: dir, encoding: 'utf8' });
  assert.equal(bad.status, 1);
  assert.ok(!bad.stdout.includes('\x1b['));
  const ok = spawnSync(process.execPath, [BIN, 'src/ok.js'], { cwd: dir, encoding: 'utf8' });
  assert.equal(ok.status, 0);
  const usage = spawnSync(process.execPath, [BIN, '--wat'], { cwd: dir, encoding: 'utf8' });
  assert.equal(usage.status, 2);
  assert.match(usage.stderr, /unknown option/i);
});
