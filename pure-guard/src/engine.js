import { extname, basename } from 'node:path';
import { tokenize } from './tokenizer.js';
import { aiRules, unicodeSecurityRules } from './rules/ai.js';
import { crashRules } from './rules/crash.js';
import { securityRules } from './rules/security.js';
import { fingerprint, isTestPath, makePosition, redact, severityRank, SEVERITIES } from './util.js';

export const RULES = [...securityRules, ...unicodeSecurityRules, ...crashRules, ...aiRules];
const SECRET_RULE = RULES.find((r) => r.id === 'security/hardcoded-secret');
export const ENGINES = ['security', 'crash', 'ai'];

const CODE_EXT = new Set(['.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.mts', '.cts']);
const TEXT_EXT = new Set(['.json', '.yml', '.yaml', '.env', '.properties', '.conf', '.ini', '.toml', '.sh', '.bash', '.zsh', '.txt', '.xml', '.cfg', '.tf', '.tfvars', '.pem', '.key']);

/** 'code' (JS/TS: all engines), 'text' (config files: secrets + hidden characters), or null (not scanned). */
export function classify(filename) {
  const ext = extname(filename).toLowerCase();
  const name = basename(filename);
  if (CODE_EXT.has(ext)) return 'code';
  if (TEXT_EXT.has(ext) || name.startsWith('.env') || name === 'Dockerfile') return 'text';
  return null;
}

// Rule ids always contain "/" (security/xss). Anything else after the directive is a reason, not a rule list:
// "// pure-guard-ignore because the input is trusted" ignores every rule on that line and the next.
const DIRECTIVE = /pure-guard-ignore(-file)?(?:[ \t]+([a-z0-9_-]+\/[a-z0-9_-]+(?:[ \t]*,[ \t]*[a-z0-9_-]+\/[a-z0-9_-]+)*))?/i;

/** Inline suppressions: `// pure-guard-ignore [rule, rule]` covers its own line and the next one. */
function collectSuppressions(source, kind, tokens, position) {
  const lines = new Map(); // line -> Set(ruleId | '*')
  let file = null; // null | Set
  const add = (target, ids) => { for (const id of ids) target.add(id); };
  const parse = (text, startLine, endLine) => {
    const m = DIRECTIVE.exec(text);
    if (!m) return;
    const ids = m[2] ? m[2].split(',').map((x) => x.trim().toLowerCase()) : ['*'];
    if (m[1]) { file ??= new Set(); add(file, ids); return; }
    for (let l = startLine; l <= endLine + 1; l++) {
      if (!lines.has(l)) lines.set(l, new Set());
      add(lines.get(l), ids);
    }
  };
  if (kind === 'code') {
    for (const c of tokens.comments) parse(c.text, position(c.start).line, position(c.end).line);
  } else {
    // pure-guard-ignore ai/split-newline: offsets must stay exact; a trailing \r is harmless to the directive regex
    source.split('\n').forEach((text, k) => parse(text, k + 1, k + 1));
  }
  return { lines, file };
}

const suppressed = (set, ruleId) => set !== undefined && set !== null && (set.has('*') || set.has(ruleId));

/** Throws RangeError for an unknown engine, severity or rule id. */
export function validateOptions({ engines = ENGINES, rulesOff = [], minSeverity = 'low' } = {}) {
  for (const e of engines) if (!ENGINES.includes(e)) throw new RangeError(`pure-guard: unknown engine "${e}" (use ${ENGINES.join(', ')})`);
  if (!SEVERITIES.includes(minSeverity)) throw new RangeError(`pure-guard: unknown severity "${minSeverity}" (use ${SEVERITIES.join(', ')})`);
  const known = new Set(RULES.map((r) => r.id));
  for (const id of rulesOff) if (!known.has(id)) throw new RangeError(`pure-guard: unknown rule "${id}" (see --list-rules)`);
}

/**
 * Scan one file's text.
 * @param {string} source
 * @param {{ filename?: string, kind?: 'code' | 'text', engines?: string[], rulesOff?: string[], minSeverity?: string }} [options]
 */
export function scanSource(source, options = {}) {
  const { filename = '<input>', engines = ENGINES, rulesOff = [], minSeverity = 'low' } = options;
  validateOptions({ engines, rulesOff, minSeverity });

  const kind = options.kind ?? classify(filename) ?? 'text';
  // In .ts files "<T>value" is a type assertion, not JSX.
  const tokens = kind === 'code' ? tokenize(source, { jsx: !/\.[cm]?ts$/i.test(filename) }) : null;
  const { position } = tokens ?? makePosition(source);
  const suppressions = collectSuppressions(source, kind, tokens, position);
  const ctx = { source, filename, kind, tokens, position, isTest: isTestPath(filename), memo: {} };
  // pure-guard-ignore ai/split-newline: split on \n only so line numbers match; the \r is stripped when a snippet is built
  const lines = source.split('\n');

  const raw = [];
  let secretRuleRan = false;
  for (const rule of RULES) {
    if (!engines.includes(rule.engine) || rulesOff.includes(rule.id) || !rule.kinds.includes(kind)) continue;
    if (suppressed(suppressions.file, rule.id)) continue;
    if (rule === SECRET_RULE) secretRuleRan = true;
    for (const f of rule.check(ctx)) raw.push({ rule, f });
  }

  // Every secret in this file is redacted everywhere it would be printed (snippets, messages) — even when the
  // secret rule itself is switched off or suppressed, so no report ever shows a full secret.
  const found = raw.map(({ f }) => f.secret);
  if (!secretRuleRan && SECRET_RULE.kinds.includes(kind)) {
    for (const f of SECRET_RULE.check({ ...ctx, isTest: false })) found.push(f.secret);
  }
  const secrets = [...new Set(found.filter(Boolean))].sort((a, b) => b.length - a.length);
  const scrub = (text) => secrets.reduce((acc, s) => acc.split(s).join(redact(s)), text);

  const seen = new Set();
  const findings = [];
  for (const { rule, f } of raw) {
    const start = position(f.start);
    if (suppressed(suppressions.lines.get(start.line), rule.id)) continue;
    const key = `${rule.id}:${f.start}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const severity = f.severity ?? rule.severity;
    if (severityRank(severity) < severityRank(minSeverity)) continue;
    const end = position(Math.max(f.start, (f.end ?? f.start + 1) - 1));
    const lineText = (lines[start.line - 1] ?? '').replace(/\r$/, '');
    findings.push({
      ruleId: rule.id,
      engine: rule.engine,
      severity,
      message: scrub(f.message),
      fix: f.fix,
      file: filename,
      line: start.line,
      column: start.column,
      endLine: end.line,
      endColumn: end.column + 1,
      snippet: scrub(lineText.trim()).slice(0, 200),
      fingerprint: fingerprint(rule.id, filename, f.secret ?? lineText.trim()),
    });
  }
  return collapseRepeatedSecrets(findings).sort((a, b) => a.line - b.line || a.column - b.column || a.ruleId.localeCompare(b.ruleId));
}

/** The same secret pasted 50 times in one file is one problem: report it once and list where else it appears. */
function collapseRepeatedSecrets(findings) {
  const first = new Map();
  const out = [];
  for (const f of findings) {
    if (f.ruleId !== 'security/hardcoded-secret') { out.push(f); continue; }
    const seen = first.get(f.fingerprint);
    if (!seen) { first.set(f.fingerprint, { finding: f, lines: [] }); out.push(f); } else seen.lines.push(f.line);
  }
  for (const { finding, lines } of first.values()) {
    if (lines.length > 0) {
      const shown = lines.slice(0, 5).join(', ');
      finding.message += ` (same value also at line${lines.length > 1 ? 's' : ''} ${shown}${lines.length > 5 ? `, +${lines.length - 5} more` : ''})`;
      finding.occurrences = lines.length + 1;
    }
  }
  return out;
}

/** Minified / bundled output (Vite, webpack, terser): huge lines, no formatting. Findings there are library internals, not your code. */
export function looksMinified(text) {
  if (text.length < 2000) return false;
  let longest = 0;
  let lines = 1;
  let start = 0;
  for (let k = 0; k <= text.length; k++) {
    if (k === text.length || text.charCodeAt(k) === 10) {
      if (k - start > longest) longest = k - start;
      start = k + 1;
      if (k < text.length) lines++;
    }
  }
  const average = text.length / lines;
  return (longest > 5000 && average > 150) || average > 400;
}
