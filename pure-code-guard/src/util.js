import { createHash } from 'node:crypto';

/** Shannon entropy in bits per character. */
export function shannon(text) {
  if (text.length === 0) return 0;
  const counts = new Map();
  for (const ch of text) counts.set(ch, (counts.get(ch) ?? 0) + 1);
  let bits = 0;
  for (const count of counts.values()) {
    const p = count / text.length;
    bits -= p * Math.log2(p);
  }
  return bits;
}

/** How many of lowercase / uppercase / digit / symbol appear in `text`. */
export function charClasses(text) {
  return [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z\d]/].filter((re) => re.test(text)).length;
}

/** Keeps just enough of a secret to recognise it. Reports never contain the full value. */
export function redact(secret) {
  if (secret.length <= 8) return `${secret.slice(0, 2)}…(${secret.length} chars)`;
  return `${secret.slice(0, 4)}…(${secret.length} chars)`;
}

/** Stable id for a finding that does not depend on line numbers and never stores the secret itself. */
export function fingerprint(...parts) {
  return createHash('sha256').update(parts.join('\0')).digest('hex').slice(0, 16);
}

export function isTestPath(filename) {
  return /(^|[\\/])(__tests?__|tests?|specs?|fixtures?|mocks?|__mocks__|examples?)([\\/]|$)|\.(test|spec)\.[cm]?[jt]sx?$|\.(example|sample|template|dist)$|\.(example|sample)\./i.test(filename);
}

export const SEVERITIES = ['low', 'medium', 'high', 'critical'];
export const severityRank = (s) => SEVERITIES.indexOf(s);

/** Regex global match iterator that never loops forever on empty matches. */
export function* matchAll(re, text) {
  const flags = re.flags.includes('g') ? re.flags : `${re.flags}g`;
  const g = new RegExp(re.source, flags);
  let m;
  while ((m = g.exec(text)) !== null) {
    if (m[0] === '') g.lastIndex++;
    yield m;
  }
}

/** Offset -> 1-based { line, column } lookup for `source`. */
export function makePosition(source) {
  const lineStarts = [0];
  for (let k = 0; k < source.length; k++) if (source[k] === '\n') lineStarts.push(k + 1);
  function position(offset) {
    let lo = 0;
    let hi = lineStarts.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (lineStarts[mid] <= offset) lo = mid; else hi = mid - 1;
    }
    return { line: lo + 1, column: offset - lineStarts[lo] + 1 };
  }
  return { lineStarts, position };
}
