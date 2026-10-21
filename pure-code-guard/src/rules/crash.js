import { braceMap } from '../tokenizer.js';
import { matchAll } from '../util.js';

// ---------------------------------------------------------------------------------------------------------
// Empty catch blocks
// ---------------------------------------------------------------------------------------------------------

const DOCUMENTED_IGNORE = /ignor|intentional|expected|best.?effort|swallow|noop|no-op|not.?an?.?error|safe to|optional|fall.?back/i;

const emptyCatch = {
  id: 'crash/empty-catch',
  engine: 'crash',
  severity: 'high',
  kinds: ['code'],
  description: 'catch blocks and .catch() handlers that silently swallow errors',
  check({ tokens }) {
    const out = [];
    const { masked, comments } = tokens;
    const documented = (from, to) => comments.some((c) => c.start >= from && c.end <= to && DOCUMENTED_IGNORE.test(c.text));

    for (const m of matchAll(/(?<!\.\s*)\bcatch\s*(?:\([^)]{0,200}\))?\s*\{(\s*)\}/, masked)) {
      if (documented(m.index, m.index + m[0].length)) continue;
      out.push({
        start: m.index, end: m.index + m[0].length,
        message: 'empty catch block swallows the error: failures become silent',
        fix: 'Handle it, log it, or rethrow. If ignoring is intentional, say why in a comment.',
      });
    }
    return out;
  },
};

// ---------------------------------------------------------------------------------------------------------
// JSON.parse outside try/catch
// ---------------------------------------------------------------------------------------------------------

function tryRanges(masked, memo) {
  const braces = (memo.braces ??= braceMap(masked));
  const ranges = [];
  for (const m of matchAll(/\btry\s*\{/, masked)) {
    const open = m.index + m[0].length - 1;
    const close = braces.get(open);
    if (close !== undefined && close !== -1) ranges.push([open, close]);
  }
  return ranges;
}

const unguardedJsonParse = {
  id: 'crash/unguarded-json-parse',
  engine: 'crash',
  severity: 'medium',
  kinds: ['code'],
  description: 'JSON.parse on non-literal input outside any try/catch',
  check({ source, tokens, memo, isTest }) {
    if (isTest) return [];
    const out = [];
    const ranges = tryRanges(tokens.masked, memo);
    for (const m of matchAll(/(?<![\w$.])JSON\s*\.\s*parse\s*\(/, tokens.masked)) {
      const arg = source.slice(m.index + m[0].length, m.index + m[0].length + 80).trimStart();
      if (/^(['"`])(?:(?!\1).)*\1\s*[,)]/.test(arg)) continue; // parsing a literal
      if (ranges.some(([a, b]) => m.index > a && m.index < b)) continue;
      out.push({
        start: m.index, end: m.index + m[0].length,
        message: 'JSON.parse throws on malformed input and nothing here catches it: one bad payload can crash the request or process',
        fix: 'Wrap in try/catch, or validate before parsing.',
      });
    }
    return out;
  },
};

// ---------------------------------------------------------------------------------------------------------
// Unsafe property chains on dynamic data (null-pointer tracker)
// ---------------------------------------------------------------------------------------------------------

// Parameter-like names that almost always carry external data (HTTP request/response bodies, parsed JSON, user records).
const DYNAMIC_NAMES = /^(?:req|request|res|response|resp|data|payload|body|json|user|users|profile|order|customer|params|query)$/;
const SKIP_ROOTS = new Set([
  'this', 'self', 'window', 'document', 'globalThis', 'global', 'process', 'console', 'Math', 'JSON', 'Object', 'Array',
  'Number', 'String', 'Promise', 'Buffer', 'Intl', 'Date', 'Symbol', 'Reflect', 'module', 'exports', 'require', 'navigator',
  'location', 'Error', 'RegExp', 'Map', 'Set', 'URL', 'super',
]);
// Values that certainly come from outside the program: HTTP clients, parsed JSON, request bodies.
const STRONG_SOURCE = new RegExp(
  '^(?:await\\s+[\\w$.]*?\\b(?:fetch|axios|got|request|superagent|ky)\\w*\\s*[(.]' +
  '|JSON\\s*\\.\\s*parse\\s*\\(|fetch\\s*\\(|[\\w$.]+\\s*\\.\\s*(?:json|text)\\s*\\(' +
  '|(?:req|request)\\s*\\.\\s*(?:body|query|params)\\b)', 'i');
// Probably external, but could just as well be an internal helper with a known shape: reported at low severity.
const EXTERNAL_CALL = '(?:get|post|put|patch|delete|query|find|exec|load|read|call|send|parse|retrieve)\\w*';
const WEAK_SOURCE = new RegExp(`^(?:await\\s+[\\w$.]*?\\b${EXTERNAL_CALL}\\s*[(.]|[\\w$]+\\s*\\.\\s*data\\b)`, 'i');

/** Names whose value arrives at runtime versus names bound to local literals/imports. */
function classifyBindings(masked) {
  const strong = new Set();
  const weak = new Set();
  const safe = new Set();
  const classify = (name, rhs) => {
    if (STRONG_SOURCE.test(rhs)) strong.add(name);
    else if (WEAK_SOURCE.test(rhs)) weak.add(name);
    else if (/^[{[]/.test(rhs) || /^(?:new\s+(?:Map|Set)|require\s*\()/.test(rhs)) safe.add(name);
  };
  for (const m of matchAll(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;\n]{0,300})/, masked)) classify(m[1], m[2].trim());
  for (const m of matchAll(/\b(?:const|let|var)\s*\{([^}]{0,500})\}\s*=\s*([^;\n]{0,300})/, masked)) {
    const rhs = m[2].trim();
    const target = STRONG_SOURCE.test(rhs) ? strong : WEAK_SOURCE.test(rhs) ? weak : null;
    if (!target) continue;
    for (const part of m[1].split(',')) {
      const name = part.split(':').pop().split('=')[0].trim();
      if (/^[A-Za-z_$][\w$]*$/.test(name)) target.add(name);
    }
  }
  for (const m of matchAll(/\bimport\s+(?:([A-Za-z_$][\w$]*)|\*\s+as\s+([A-Za-z_$][\w$]*)|\{([^}]{0,1000})\})/, masked)) {
    for (const name of [m[1], m[2], ...(m[3] ?? '').split(',').map((p) => p.split(/\bas\b/).pop().trim())]) if (name) safe.add(name);
  }
  return { strong, weak, safe };
}

const nullChain = {
  id: 'crash/unsafe-property-chain',
  engine: 'crash',
  severity: 'medium',
  kinds: ['code'],
  description: 'a.b.c on runtime data without optional chaining (heuristic: medium for JSON.parse/fetch/request bodies, low when guessed from names)',
  check({ source, tokens, isTest }) {
    if (isTest) return []; // a test that throws on a missing property is doing its job
    const out = [];
    const { masked, lineStarts } = tokens;
    const { strong, weak, safe } = classifyBindings(masked);
    const seen = new Set();
    const lineOf = (offset) => {
      let lo = 0;
      let hi = lineStarts.length - 1;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (lineStarts[mid] <= offset) lo = mid; else hi = mid - 1;
      }
      return lo;
    };

    for (const m of matchAll(/(?<![\w$.\])])([A-Za-z_$][\w$]*)((?:\s*\??\.\s*[A-Za-z_$][\w$]*){2,})/, masked)) {
      const root = m[1];
      if (SKIP_ROOTS.has(root) || safe.has(root) || /^[A-Z][A-Z0-9_]*$/.test(root)) continue;
      const known = strong.has(root) || weak.has(root);
      if (!known && !DYNAMIC_NAMES.test(root)) continue;

      const steps = [...m[2].matchAll(/(\?\.|\.)\s*([A-Za-z_$][\w$]*)/g)];
      // Property k (k >= 1) is read from the value of property k-1. A plain "." there throws if that value is null/undefined.
      const unsafe = steps.slice(1).some((s) => s[1] === '.');
      if (!unsafe) continue;
      // Express/Koa request objects: middleware sets req.user, req.tenant, req.session...; body/query/params always exist.
      // Only a property nested inside the payload (req.body.user.name) is untrusted.
      if (/^(?:req|request)$/.test(root) && (!/^(?:body|query|params|headers|cookies)$/.test(steps[0][2]) || steps.length < 3)) continue;

      const line = lineOf(m.index);
      const key = `${line}:${root}`;
      if (seen.has(key)) continue;
      seen.add(key);

      // Already guarded earlier on this statement/line or within the 3 lines above?
      const guardFrom = lineStarts[Math.max(0, line - 3)];
      const before = masked.slice(guardFrom, m.index);
      const r = root.replace(/\$/g, '\\$');
      const guard = new RegExp(`\\b${r}(?:\\s*\\??\\.\\s*[\\w$]+)*\\s*(?:&&|\\?\\?|\\|\\||\\?\\s)|\\b${r}\\s*\\?\\.|\\bif\\s*\\(\\s*!?\\s*${r}\\b`);
      if (guard.test(before)) continue;

      const suggestion = `${root}?.${steps.map((s) => s[2]).join('?.')}`;
      out.push({
        start: m.index, end: m.index + m[0].length,
        message: `"${source.slice(m.index, m.index + m[0].length).replace(/\s+/g, '')}" throws a TypeError if an intermediate value is null/undefined`,
        fix: `Use optional chaining: ${suggestion}`,
        // Certain external sources are a real risk; a name like "data" or a generic call is only a hint.
        severity: strong.has(root) || /^(?:req|request)$/.test(root) ? 'medium' : 'low',
      });
    }
    return out;
  },
};

const emptyPromiseCatch = {
  id: 'crash/empty-promise-catch',
  engine: 'crash',
  severity: 'medium',
  kinds: ['code'],
  description: '.catch(() => {}) handlers that silently swallow promise rejections',
  check({ tokens }) {
    const out = [];
    const { masked, comments } = tokens;
    const documented = (from, to) => comments.some((c) => c.start >= from && c.end <= to && DOCUMENTED_IGNORE.test(c.text));
    // promise.catch(() => {})  /  promise.catch(function () {})  /  promise.catch(e => {})
    const emptyHandler = /\.\s*catch\s*\(\s*(?:async\s*)?(?:\([^)]{0,200}\)|[A-Za-z_$][\w$]*)\s*=>\s*\{\s*\}\s*\)|\.\s*catch\s*\(\s*(?:async\s*)?function\s*[\w$]*\s*\([^)]{0,200}\)\s*\{\s*\}\s*\)/;
    for (const m of matchAll(emptyHandler, masked)) {
      if (documented(m.index, m.index + m[0].length)) continue;
      out.push({
        start: m.index, end: m.index + m[0].length,
        message: 'empty .catch() swallows the rejection: failures become silent (fine for best-effort calls, risky for anything that matters)',
        fix: 'Handle or log the error, or remove the .catch and let the caller decide.',
      });
    }
    return out;
  },
};

export const crashRules = [emptyCatch, emptyPromiseCatch, unguardedJsonParse, nullChain];
