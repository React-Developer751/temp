import { lstat, readdir, readFile, stat } from 'node:fs/promises';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { classify, looksMinified, RULES, scanSource, validateOptions } from './engine.js';
import { severityRank } from './util.js';
import { createGitIgnore } from './gitignore.js';
import { globToRegExp } from './glob.js';

export { globToRegExp };

export const DEFAULT_IGNORE = [
  'node_modules', '.git', '.hg', '.svn', 'dist', 'build', 'coverage', '.next', '.nuxt', '.turbo', '.cache', '.parcel-cache',
  'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml', '*.min.js', '*.map',
];

/**
 * gitignore-like matching: a pattern without "/" matches any path segment (dir or file name);
 * a pattern with "/" matches the path relative to the scan root.
 */
export function makeIgnore(patterns) {
  const matchers = patterns.map((p) => {
    const clean = p.replace(/\\/g, '/').replace(/^\.\//, '').replace(/\/$/, '');
    const re = globToRegExp(clean);
    return clean.includes('/') ? (rel) => re.test(rel) || rel.startsWith(`${clean}/`) : (rel) => rel.split('/').some((seg) => re.test(seg));
  });
  return (rel) => matchers.some((m) => m(rel));
}

// Generated-output folders skipped by default; unlike node_modules / .git they are listed under "skipped" so a
// real source folder that happens to be called "build" doesn't disappear without a trace.
const GENERATED_DIRS = new Set(['dist', 'build', 'coverage', '.next', '.nuxt', '.turbo', '.cache', '.parcel-cache']);

const CAP = { secret: 'medium', other: 'low' };
const ONLY_SECRETS = RULES.map((r) => r.id).filter((id) => id !== 'security/hardcoded-secret');

/**
 * A file git ignores is not in the repository: a secret in your local .env is not "committed". It is still worth a
 * look (backups, Docker images, logs), so secrets stay visible at medium; everything else drops to low.
 */
function downgradeGitIgnored(findings, minSeverity) {
  const out = [];
  for (const f of findings) {
    const isSecret = f.ruleId === 'security/hardcoded-secret';
    const cap = isSecret ? CAP.secret : CAP.other;
    const capped = severityRank(f.severity) > severityRank(cap) ? cap : f.severity;
    if (severityRank(capped) < severityRank(minSeverity)) continue;
    out.push({
      ...f,
      severity: capped,
      gitIgnored: true,
      message: isSecret ? `${f.message} [file is git-ignored: not in the repo, but keep it out of backups, images and logs]` : f.message,
    });
  }
  return out;
}

const toPosix = (p) => p.split(sep).join('/');

async function* walk(dir, root, ignore, cwd) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch (error) {
    yield { error: { file: toPosix(relative(root, dir)), message: error.message } };
    return;
  }
  entries.sort((a, b) => a.name.localeCompare(b.name));
  for (const entry of entries) {
    const full = join(dir, entry.name);
    const rel = toPosix(relative(root, full));
    const fromCwd = toPosix(relative(cwd, full));
    // Default patterns match from the scan root (so "pure-guard src/build" still scans it); your own --ignore
    // patterns also match the path from the working directory, which is what reports show.
    if (ignore.byDefault(rel) || ignore.byUser(rel) || (!fromCwd.startsWith('..') && ignore.byUser(fromCwd))) {
      if (entry.isDirectory() && GENERATED_DIRS.has(entry.name)) yield { skipped: { file: fromCwd.startsWith('..') ? toPosix(full) : fromCwd, reason: 'build output, ignored by default (pass the folder itself to scan it)' } };
      continue;
    }
    if (entry.isSymbolicLink()) continue; // never follow links inside a tree: avoids loops and escaping the project
    if (entry.isDirectory()) yield* walk(full, root, ignore, cwd);
    else if (entry.isFile() && classify(entry.name)) yield { file: full };
  }
}

/**
 * Scan files and directories.
 * @param {string[]} paths
 * @param {{ cwd?: string, ignore?: string[], maxFileSize?: number, engines?: string[], rulesOff?: string[], minSeverity?: string }} [options]
 */
export async function scanPaths(paths, options = {}) {
  if (typeof paths === 'string') paths = [paths];
  if (!Array.isArray(paths) || paths.some((p) => typeof p !== 'string')) throw new TypeError('pure-guard: paths must be a string or an array of strings');
  const { cwd = process.cwd(), ignore = [], maxFileSize = 1_000_000, includeMinified = false, gitIgnored = 'downgrade', ...scanOptions } = options;
  if (!['downgrade', 'skip', 'include'].includes(gitIgnored)) throw new RangeError(`pure-guard: gitIgnored must be downgrade, skip or include (got "${gitIgnored}")`);
  validateOptions(scanOptions);
  const ignorers = { byDefault: makeIgnore(DEFAULT_IGNORE), byUser: makeIgnore(ignore) };
  const result = { findings: [], filesScanned: 0, skipped: [], errors: [] };
  const gitRules = new Map();
  const gitByDir = new Map();
  const gitFor = (dir) => {
    if (!gitByDir.has(dir)) gitByDir.set(dir, createGitIgnore(dir, gitRules));
    return gitByDir.get(dir);
  };

  const targets = [];
  for (const p of paths) {
    const abs = resolve(cwd, p);
    let info;
    try {
      info = await lstat(abs);
      if (info.isSymbolicLink()) info = await stat(abs); // a link you name explicitly is followed
    } catch (error) {
      result.errors.push({ file: p, message: error.code === 'ENOENT' ? 'no such file or directory' : error.message });
      continue;
    }
    if (info.isDirectory()) {
      for await (const item of walk(abs, abs, ignorers, cwd)) {
        if (item.error) result.errors.push(item.error);
        else if (item.skipped) result.skipped.push(item.skipped);
        else targets.push({ abs: item.file, base: cwd });
      }
    } else if (info.isFile()) targets.push({ abs, base: cwd, explicit: true });
    else result.errors.push({ file: p, message: 'not a regular file or directory' });
  }

  for (let i = 0; i < targets.length; i += 32) {
    await Promise.all(targets.slice(i, i + 32).map(async ({ abs, base }) => {
      const rel = toPosix(relative(base, abs));
      const file = rel === '' || rel.startsWith('..') ? toPosix(abs) : rel; // outside the working directory: show the full path
      try {
        const git = gitIgnored === 'include' ? null : await gitFor(dirname(abs));
        const ignoredByGit = git ? await git.isIgnored(abs) : false;
        if (ignoredByGit && gitIgnored === 'skip') { result.skipped.push({ file, reason: 'git-ignored' }); return; }
        if ((await stat(abs)).size > maxFileSize) { result.skipped.push({ file, reason: `larger than ${maxFileSize} bytes` }); return; }
        const buffer = await readFile(abs);
        if (buffer.subarray(0, 8000).includes(0)) { result.skipped.push({ file, reason: 'binary file' }); return; }
        const text = buffer.toString('utf8');
        // Minified / bundled code: library internals would only be noise, but a key baked into a bundle is a real leak.
        const minified = !includeMinified && classify(file) === 'code' && looksMinified(text);
        if (minified) result.skipped.push({ file, reason: 'minified or bundled: only checked for secrets' });
        result.filesScanned++;
        const found = scanSource(text, minified ? { ...scanOptions, filename: file, rulesOff: ONLY_SECRETS } : { ...scanOptions, filename: file });
        result.findings.push(...(ignoredByGit ? downgradeGitIgnored(found, scanOptions.minSeverity ?? 'low') : found));
      } catch (error) {
        result.errors.push({ file, message: error.message });
      }
    }));
  }
  result.findings.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line || a.column - b.column);
  return result;
}
