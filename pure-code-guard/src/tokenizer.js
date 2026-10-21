import { makePosition } from './util.js';

// A small, error-tolerant JavaScript/TypeScript lexer. It never builds an AST; it only finds the regions of the
// source that are NOT code (comments, string/template text, regex bodies) so rules can run on `masked`, a copy
// of the source where those regions are blanked out with spaces. Offsets and line breaks are preserved, so a
// position in `masked` is the same position in the original.

const KEYWORDS_BEFORE_REGEX = new Set([
  'return', 'typeof', 'instanceof', 'in', 'of', 'new', 'delete', 'void', 'throw', 'case', 'do', 'else', 'yield', 'await',
]);
const IDENT_START = /[A-Za-z_$\u0080-￿]/;
const IDENT_PART = /[\w$\u0080-￿]/;

/**
 * @typedef {{ start: number, end: number, quote: string, value: string, hasExpr: boolean, tagged: boolean,
 *   exprs: { start: number, end: number }[] }} StringToken   value = static text (expressions replaced by "\0")
 * @typedef {{ start: number, end: number, text: string, block: boolean }} CommentToken
 * @typedef {{ start: number, end: number, body: string, flags: string }} RegexToken
 */

/** @param {string} source */
export function tokenize(source) {
  const n = source.length;
  // pure-guard-ignore ai/split-empty: UTF-16 units on purpose, so masked[i] lines up with source[i]
  const chars = source.split('');
  /** @type {CommentToken[]} */ const comments = [];
  /** @type {StringToken[]} */ const strings = [];
  /** @type {RegexToken[]} */ const regexes = [];
  let i = 0;
  let prev = { kind: 'start', value: '' }; // last significant token
  let templateDepth = 0;

  const blank = (from, to) => {
    for (let k = from; k < to; k++) {
      const c = chars[k];
      if (c !== '\n' && c !== '\r' && c !== ' ' && c !== ' ') chars[k] = ' ';
    }
  };

  const regexAllowed = () => {
    switch (prev.kind) {
      case 'start': return true;
      case 'ident': return KEYWORDS_BEFORE_REGEX.has(prev.value);
      case 'punct': return ![')', ']', '}', '++', '--'].includes(prev.value);
      default: return false; // number, string, regex
    }
  };

  function readLineComment() {
    const start = i;
    while (i < n && source[i] !== '\n' && source[i] !== '\r') i++;
    comments.push({ start, end: i, text: source.slice(start + 2, i), block: false });
    blank(start, i);
  }

  function readBlockComment() {
    const start = i;
    const close = source.indexOf('*/', i + 2);
    i = close === -1 ? n : close + 2;
    comments.push({ start, end: i, text: source.slice(start + 2, close === -1 ? n : close), block: true });
    blank(start, i);
  }

  function readString(quote) {
    const start = i;
    i++;
    while (i < n) {
      const c = source[i];
      if (c === '\\') { i += 2; continue; }
      if (c === quote || c === '\n') break; // an unterminated string ends at the line break
      i++;
    }
    i = Math.min(i, n);
    const closed = source[i] === quote;
    strings.push({ start, end: closed ? i + 1 : i, quote, value: source.slice(start + 1, i), hasExpr: false, tagged: false, exprs: [] });
    blank(start + 1, i);
    if (closed) i++;
    prev = { kind: 'string', value: quote };
  }

  function readTemplate() {
    const start = i;
    const tagged = (prev.kind === 'ident' && !KEYWORDS_BEFORE_REGEX.has(prev.value)) ||
      (prev.kind === 'punct' && (prev.value === ')' || prev.value === ']'));
    const exprs = [];
    let value = '';
    i++;
    let textStart = i;
    while (i < n) {
      const c = source[i];
      if (c === '\\') { i += 2; continue; }
      if (c === '`') break;
      if (c === '$' && source[i + 1] === '{' && templateDepth < 100) { // deeper nesting is treated as text: bounds recursion
        value += source.slice(textStart, i) + '\0';
        blank(textStart, i + 2); // static text and the "${"
        i += 2;
        const exprStart = i;
        templateDepth++;
        scanCode(true);
        templateDepth--;
        exprs.push({ start: exprStart, end: i });
        if (source[i] === '}') { blank(i, i + 1); i++; }
        textStart = i;
        continue;
      }
      i++;
    }
    i = Math.min(i, n);
    value += source.slice(textStart, i);
    blank(textStart, i);
    const closed = source[i] === '`';
    strings.push({ start, end: closed ? i + 1 : i, quote: '`', value, hasExpr: exprs.length > 0, tagged, exprs });
    if (closed) i++;
    prev = { kind: 'string', value: '`' };
  }

  function tryReadRegex() {
    let j = i + 1;
    let inClass = false;
    while (j < n) {
      const c = source[j];
      if (c === '\n' || c === '\r') return false;
      if (c === '\\') { j += 2; continue; }
      if (c === '[') inClass = true;
      else if (c === ']') inClass = false;
      else if (c === '/' && !inClass) break;
      j++;
    }
    if (j >= n) return false;
    let end = j + 1;
    while (end < n && /[a-z]/i.test(source[end])) end++;
    regexes.push({ start: i, end, body: source.slice(i + 1, j), flags: source.slice(j + 1, end) });
    blank(i + 1, j);
    i = end;
    prev = { kind: 'regex', value: '' };
    return true;
  }

  // Scans code until EOF, or (inside a template expression) until the "}" that closes it.
  function scanCode(stopAtCloseBrace) {
    let depth = 0;
    while (i < n) {
      const c = source[i];
      if (c === '/') {
        const next = source[i + 1];
        if (next === '/') readLineComment();
        else if (next === '*') readBlockComment();
        else if (regexAllowed() && tryReadRegex()) { /* consumed */ } else { i++; prev = { kind: 'punct', value: '/' }; }
      } else if (c === '"' || c === "'") readString(c);
      else if (c === '`') readTemplate();
      else if (c === '{') { depth++; i++; prev = { kind: 'punct', value: '{' }; }
      else if (c === '}') {
        if (stopAtCloseBrace && depth === 0) return;
        depth = Math.max(0, depth - 1);
        i++;
        prev = { kind: 'punct', value: '}' };
      } else if (IDENT_START.test(c)) {
        const s = i;
        while (i < n && IDENT_PART.test(source[i])) i++;
        prev = { kind: 'ident', value: source.slice(s, i) };
      } else if (c >= '0' && c <= '9') {
        while (i < n && /[\w.]/.test(source[i])) i++;
        prev = { kind: 'num', value: '' };
      } else if (c === ' ' || c === '\t' || c === '\n' || c === '\r') i++;
      else if ((c === '+' || c === '-') && source[i + 1] === c) { i += 2; prev = { kind: 'punct', value: c + c }; }
      else { i++; prev = { kind: 'punct', value: c }; }
    }
  }

  if (source.startsWith('#!')) { // hashbang
    while (i < n && source[i] !== '\n') i++;
    blank(0, i);
  }
  scanCode(false);

  const { lineStarts, position } = makePosition(source);

  return { masked: chars.join(''), comments, strings, regexes, lineStarts, position };
}

/**
 * For every "{" in masked code, the index of its matching "}" (or -1 when unbalanced). One linear pass, so rules can
 * ask about any block without rescanning the file.
 * @returns {Map<number, number>}
 */
export function braceMap(masked) {
  const map = new Map();
  const stack = [];
  for (let k = 0; k < masked.length; k++) {
    const c = masked[k];
    if (c === '{') stack.push(k);
    else if (c === '}' && stack.length > 0) map.set(stack.pop(), k);
  }
  for (const open of stack) map.set(open, -1);
  return map;
}
