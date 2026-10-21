import { readFile, stat } from 'node:fs/promises';
import { dirname, join, relative, sep } from 'node:path';
import { globToRegExp } from './glob.js';

// A small .gitignore evaluator (no git binary needed). It answers one question: "would git ignore this file?",
// so a secret in a local, ignored .env is not reported as "committed".
//
// Supported: comments, blank lines, "!" negation, trailing "/" (directories only), leading or inner "/" (anchored
// to the .gitignore's folder), "*", "?", "**", and the rule that a file inside an ignored directory is ignored.
// Not supported: character classes ([a-z]), .git/info/exclude and global excludes.

const toPosix = (p) => p.split(sep).join('/');

/** Parse the text of one .gitignore into matchers. */
export function parseGitIgnore(text) {
  const rules = [];
  for (let line of text.split(/\r?\n/)) {
    line = line.replace(/(?<!\\)\s+$/, '');
    if (line === '' || line.startsWith('#')) continue;
    let negate = false;
    if (line.startsWith('!')) { negate = true; line = line.slice(1); }
    line = line.replace(/^\\(?=[#!])/, '');
    const dirOnly = line.endsWith('/');
    if (dirOnly) line = line.slice(0, -1);
    const anchored = line.includes('/');
    if (line.startsWith('/')) line = line.slice(1);
    if (line === '') continue;
    rules.push({ negate, dirOnly, anchored, regex: globToRegExp(line) });
  }
  return rules;
}

/** Result of a folder's rules on `rel` (path relative to that folder): true, false, or null when no rule matches. */
function decide(rules, rel, isDir) {
  let result = null;
  const base = rel.slice(rel.lastIndexOf('/') + 1);
  for (const rule of rules) {
    if (rule.dirOnly && !isDir) continue;
    const hit = rule.anchored ? rule.regex.test(rel) : rule.regex.test(base);
    if (hit) result = !rule.negate;
  }
  return result;
}

/**
 * Finds the repository root above `startDir` (a folder containing .git) and answers `isIgnored(absolutePath)`.
 * Returns null when the path is not inside a git repository (then nothing can be called "ignored").
 */
export async function createGitIgnore(startDir, cache = new Map()) {
  let root = null;
  for (let dir = startDir; ; dir = dirname(dir)) {
    try {
      await stat(join(dir, '.git'));
      root = dir;
      break;
    } catch { /* ignore: not a repository root here, keep walking up */ }
    if (dirname(dir) === dir) break;
  }
  if (root === null) return null;

  // cache: folder -> rules (shareable between instances: keys are absolute folders)
  const rulesFor = async (folder) => {
    if (!cache.has(folder)) {
      let rules = [];
      try { rules = parseGitIgnore(await readFile(join(folder, '.gitignore'), 'utf8')); } catch { /* no .gitignore here */ }
      cache.set(folder, rules);
    }
    return cache.get(folder);
  };

  return {
    root,
    /** @param {string} absolute @param {boolean} [isDir] */
    async isIgnored(absolute, isDir = false) {
      const rel = toPosix(relative(root, absolute));
      if (rel === '' || rel.startsWith('..')) return false;
      const parts = rel.split('/');
      // Walk from the repo root down: an ignored directory hides everything under it.
      for (let depth = 1; depth <= parts.length; depth++) {
        const pathSoFar = parts.slice(0, depth).join('/');
        const last = depth === parts.length;
        let verdict = null;
        for (let owner = 0; owner < depth; owner++) { // .gitignore files from the root down to this entry's folder
          const folder = owner === 0 ? root : join(root, ...parts.slice(0, owner));
          const sub = pathSoFar.split('/').slice(owner).join('/');
          const result = decide(await rulesFor(folder), sub, last ? isDir : true);
          if (result !== null) verdict = result;
        }
        if (verdict === true) return true;
      }
      return false;
    },
  };
}
