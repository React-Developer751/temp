import { matchAll } from '../util.js';

// Text-handling mistakes that LLM-written code repeats: it is written against single-line ASCII examples, then
// meets CRLF, multi-line input, emoji and invisible characters in real data.

const textRule = (id, severity, description, check) => ({ id, engine: 'ai', severity, kinds: ['code'], description, check });

const splitNewline = textRule('ai/split-newline', 'medium', 'split("\\n") leaves a stray "\\r" on CRLF input', ({ source, tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*split\s*\(\s*(?=['"])/, tokens.masked)) {
    const arg = /^(['"])(\\r\\n|\\n)\1\s*[,)]/.exec(source.slice(m.index + m[0].length, m.index + m[0].length + 20));
    // Harmless in the same statement (a chain may span lines): .trim() / .trimEnd() drops the "\r", and a round
    // trip back through .join("\n") puts every "\r" back where it was.
    const rest = arg?.[2] === '\\n' ? source.slice(m.index + m[0].length + arg[0].length, m.index + m[0].length + arg[0].length + 400) : '';
    const harmless = /^[^;]*?\.\s*(?:trim(?:End|Right)?\s*\(|join\s*\(\s*(['"])\\n\1\s*\))/.test(rest.split(';')[0]);
    if (arg && !harmless) {
      out.push({
        start: m.index, end: m.index + m[0].length + arg[0].length,
        message: arg[2] === '\\n' ? 'split("\\n") keeps the "\\r" of Windows (CRLF) line endings' : 'split("\\r\\n") does not split LF-only text',
        fix: 'Use .split(/\\r?\\n/) (or /\\r\\n|\\r|\\n/).',
      });
    }
  }
  return out;
});

const splitChars = textRule('ai/split-empty', 'medium', 'split("") breaks emoji and other characters outside the BMP', ({ source, tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*split\s*\(\s*(?=['"])/, tokens.masked)) {
    const arg = /^(['"])\1\s*\)/.exec(source.slice(m.index + m[0].length, m.index + m[0].length + 8));
    if (arg) {
      out.push({
        start: m.index, end: m.index + m[0].length + arg[0].length,
        message: 'split("") cuts UTF-16 surrogate pairs in half: emoji and many scripts become garbage (and reverse() mangles them)',
        fix: 'Use Array.from(str) or [...str] for code points, or new Intl.Segmenter().segment(str) for user-visible characters.',
      });
    }
  }
  return out;
});

const splitSpace = textRule('ai/split-space', 'low', 'split(" ") ignores tabs and newlines between words', ({ source, tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*split\s*\(\s*(?=['"])/, tokens.masked)) {
    const arg = /^(['"]) \1\s*\)/.exec(source.slice(m.index + m[0].length, m.index + m[0].length + 8));
    if (arg) {
      out.push({
        start: m.index, end: m.index + m[0].length + arg[0].length,
        message: 'split(" ") does not split on tabs/newlines and yields empty strings for repeated spaces',
        fix: 'Use .split(/\\s+/) after .trim().',
      });
    }
  }
  return out;
});

const replaceFirstOnly = textRule('ai/replace-first-only', 'low', 'replace("literal", …) only replaces the first occurrence', ({ source, tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*replace\s*\(\s*(?=['"])/, tokens.masked)) {
    const arg = /^(['"])((?:\\.|(?!\1)[^\\])+)\1\s*,/.exec(source.slice(m.index + m[0].length, m.index + m[0].length + 80));
    if (!arg) continue;
    const multiline = /\\[nrt]/.test(arg[2]) || arg[2] === ' ';
    out.push({
      start: m.index, end: m.index + m[0].length + arg[0].length,
      severity: multiline ? 'medium' : 'low',
      message: `replace("${arg[2]}", …) replaces only the first match; multi-line or repeated input keeps the rest`,
      fix: 'Use .replaceAll("…", …) or a regex with the g flag.',
    });
  }
  return out;
});

const truncate = textRule('ai/truncate-by-length', 'low', 'slice(0, N) can cut an emoji or line in half', ({ tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*(?:slice|substring|substr)\s*\(\s*0\s*,\s*\d+\s*\)/, tokens.masked)) {
    out.push({
      start: m.index, end: m.index + m[0].length,
      message: 'truncating by UTF-16 length can split a surrogate pair (emoji) and ignores line breaks in the text',
      fix: 'Truncate on code points ([...str].slice(0, N).join("")) or graphemes (Intl.Segmenter); keep multi-line text in mind.',
    });
  }
  return out;
});

const repeatByLength = textRule('ai/width-from-length', 'low', 'repeat(text.length) assumes one column per UTF-16 unit', ({ tokens }) => {
  const out = [];
  for (const m of matchAll(/\.\s*repeat\s*\(\s*[^)]{0,200}\.length\b/, tokens.masked)) {
    out.push({
      start: m.index, end: m.index + m[0].length,
      message: 'building a border/padding from .length breaks for wide characters, emoji, and multi-line text',
      fix: 'Measure the longest line and use a display-width aware measure (Intl.Segmenter) if layout matters.',
    });
  }
  return out;
});

const anchoredDot = textRule('ai/regex-multiline', 'low', '^ $ and . in regexes behave differently on multi-line input', ({ tokens }) => {
  const out = [];
  for (const r of tokens.regexes) {
    if (r.flags.includes('m') || r.flags.includes('s')) continue;
    const body = r.body.replace(/\\./g, '').replace(/\[(?:\\.|[^\]\\])*\]/g, '');
    if (/\^/.test(body) && /\$/.test(body) && /\.[*+]/.test(body)) {
      out.push({
        start: r.start, end: r.end,
        message: 'regex is anchored with ^…$ around .* / .+ but has no m or s flag: on multi-line input the anchors only match the whole string and "." stops at "\\n"',
        fix: 'Add the m flag (per-line anchors) and/or the s flag (dot matches newline), or use [\\s\\S]*.',
      });
    }
  }
  return out;
});

// ---------------------------------------------------------------------------------------------------------
// Invisible / look-alike characters (copy-paste from chat UIs, Trojan Source)
// ---------------------------------------------------------------------------------------------------------

const BIDI = new Set([0x202a, 0x202b, 0x202c, 0x202d, 0x202e, 0x2066, 0x2067, 0x2068, 0x2069]);
const ZERO_WIDTH = new Set([0x200b, 0x200c, 0x200d, 0x2060, 0xfeff]);
const EXOTIC_SPACE = /^[   -   　]$/;
const SMART_PUNCTUATION = new Set([0x2018, 0x2019, 0x201c, 0x201d, 0x2013, 0x2014, 0x2212]);
const EMOJI_JOINER_NEIGHBOUR = /[\p{Extended_Pictographic}\u{1F3FB}-\u{1F3FF}️]/u;

const hex = (cp) => `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`;

function scanInvisible(ctx) {
  return (ctx.memo.invisible ??= computeInvisible(ctx));
}

function computeInvisible({ source, tokens }) {
  const bidi = [];
  const invisible = [];
  const smart = [];
  const masked = tokens?.masked;
  const chars = [...source];
  const regexes = tokens?.regexes ?? [];
  let regexIndex = 0;
  let offset = 0;
  for (let k = 0; k < chars.length; k++) {
    const ch = chars[k];
    const cp = ch.codePointAt(0);
    const at = offset;
    offset += ch.length;
    if (cp < 0x80) continue;
    const inCode = masked !== undefined && masked[at] === ch; // blanked (string/comment/regex) text differs from the original
    while (regexIndex < regexes.length && regexes[regexIndex].end <= at) regexIndex++;
    const inRegex = regexIndex < regexes.length && at > regexes[regexIndex].start && at < regexes[regexIndex].end;

    if (BIDI.has(cp)) bidi.push({ start: at, end: at + 1, cp });
    else if (ZERO_WIDTH.has(cp)) {
      if (cp === 0xfeff && at === 0) continue; // byte-order mark
      if (inRegex) continue; // /^\uFEFF/ and friends match these characters on purpose
      const next = chars[k + 1] ?? '';
      const prev = chars[k - 1] ?? '';
      if ((cp === 0x200d || cp === 0x200c) && (EMOJI_JOINER_NEIGHBOUR.test(prev) || EMOJI_JOINER_NEIGHBOUR.test(next) || next.codePointAt(0) > 0x7f || prev.codePointAt(0) > 0x7f)) continue; // emoji sequences, Indic/Persian scripts
      invisible.push({ start: at, end: at + 1, cp, inCode });
    } else if (inCode && EXOTIC_SPACE.test(ch)) invisible.push({ start: at, end: at + 1, cp, inCode, space: true });
    else if (inCode && SMART_PUNCTUATION.has(cp)) smart.push({ start: at, end: at + 1, cp });
  }
  return { bidi, invisible, smart };
}

/** One finding per line (the first), noting how many more characters are on that line. */
function onePerLine(items, position, build) {
  const byLine = new Map();
  for (const item of items) {
    const line = position(item.start).line;
    if (!byLine.has(line)) byLine.set(line, []);
    byLine.get(line).push(item);
  }
  return [...byLine.values()].map((group) => {
    const finding = build(group[0]);
    if (group.length > 1) finding.message += ` (+${group.length - 1} more on this line)`;
    return finding;
  });
}

const bidiControl = {
  id: 'security/bidi-control',
  engine: 'security',
  severity: 'critical',
  kinds: ['code', 'text'],
  description: 'Bidirectional control characters that make code display differently from what it does (Trojan Source, CVE-2021-42574)',
  check(ctx) {
    return onePerLine(scanInvisible(ctx).bidi, ctx.position, (f) => ({
      start: f.start, end: f.end,
      message: `bidirectional control character ${hex(f.cp)}: the code you read may not be the code that runs`,
      fix: 'Delete the character. If you need right-to-left text, put it in a string via an escape sequence.',
    }));
  },
};

const invisibleChar = {
  id: 'ai/invisible-char',
  engine: 'ai',
  severity: 'high',
  kinds: ['code', 'text'],
  description: 'Zero-width characters and non-breaking spaces pasted into source',
  check(ctx) {
    return onePerLine(scanInvisible(ctx).invisible, ctx.position, (f) => ({
      start: f.start, end: f.end,
      severity: f.inCode ? 'high' : 'medium',
      message: f.space ? `non-breaking/exotic space ${hex(f.cp)} in code: looks like a space but is a syntax error` : `invisible character ${hex(f.cp)}${f.inCode ? ' in code' : ''}: breaks comparisons and matching without being visible`,
      fix: f.inCode
        ? 'Delete it (re-type the line).'
        : `If it is intentional (e.g. a BOM for Excel), write it as an escape so it is visible: "\\u${f.cp.toString(16).toUpperCase().padStart(4, '0')}". Otherwise delete it; to clean input text use .replace(/[\\u200B-\\u200D\\u2060\\uFEFF]/g, "").`,
    }));
  },
};

const JSX_FILE = /\.[jt]sx$/i;
const JSX_MARKUP = /<\/[A-Za-z][\w.]*>|\/>/; // a closing tag or self-closing tag anywhere: this file has JSX, so prose is everywhere
const MARKUP = /<\/?[A-Za-z][^>]{0,200}>|\/>/;
const OPENING_QUOTES = new Set([0x2018, 0x201c]);
const VALUE_START = /[=(,:[?+&|!;{]/;

/**
 * "“" in JSX text or prose is typography; in code it is a syntax error. Decide by what surrounds the character:
 * a quote where a value should start, or a dash between two operands outside any markup.
 */
function isPunctuationUsedAsCode(source, filename, at, cp) {
  const lineStart = source.lastIndexOf('\n', at - 1) + 1;
  let lineEnd = source.indexOf('\n', at);
  if (lineEnd === -1) lineEnd = source.length;
  const before = source.slice(lineStart, at).trimEnd();
  const after = source.slice(at + 1, lineEnd).trimStart();
  if (OPENING_QUOTES.has(cp)) return before === '' ? false : VALUE_START.test(before.at(-1)) || /\b(?:return|case|yield|await|typeof)$/.test(before);
  if (cp === 0x2019 || cp === 0x201d) return false; // closing quotes are reported through the opening one on the same line
  // dashes
  if (JSX_FILE.test(filename) || MARKUP.test(source.slice(lineStart, lineEnd))) return false;
  return /[\w)\]]$/.test(before) && /^[\w([]/.test(after);
}

const smartPunctuation = {
  id: 'ai/smart-punctuation',
  engine: 'ai',
  severity: 'high',
  kinds: ['code'],
  description: 'Curly quotes and typographic dashes used as code (copied from chat or docs)',
  check(ctx) {
    if (JSX_FILE.test(ctx.filename) || JSX_MARKUP.test(ctx.source)) return []; // a build would reject real curly-quote code at once
    const used = scanInvisible(ctx).smart.filter((f) => isPunctuationUsedAsCode(ctx.source, ctx.filename, f.start, f.cp));
    return onePerLine(used, ctx.position, (f) => ({
      start: f.start, end: f.end,
      message: `typographic character ${hex(f.cp)} ("${String.fromCodePoint(f.cp)}") used as code: use a plain ASCII quote or hyphen`,
      fix: 'Replace with \' " or -.',
    }));
  },
};

// Cyrillic and Greek letters that render like Latin ones in common fonts.
const LOOKALIKES = /[аеорсухіјѕһӏԁԛԝАВЕКМНОРСТХЅІЈԌοινρΑΒΕΖΗΙΚΜΝΟΡΤΥΧ]/u;

const homoglyph = {
  id: 'ai/homoglyph-identifier',
  engine: 'ai',
  severity: 'high',
  kinds: ['code'],
  description: 'Identifiers mixing Latin letters with look-alike Cyrillic/Greek letters',
  check({ tokens }) {
    const out = [];
    for (const m of matchAll(/[\p{L}\p{N}_$]+/u, tokens.masked)) {
      // Only letters that pass for Latin ones count: "Δt", "μs" or "λx" are honest Greek, not a disguise.
      if (/[A-Za-z]/.test(m[0]) && LOOKALIKES.test(m[0])) {
        out.push({
          start: m.index, end: m.index + m[0].length,
          message: `identifier "${m[0]}" mixes Latin with Cyrillic/Greek look-alike letters: it is a different name than it looks`,
          fix: 'Retype the identifier using only Latin letters.',
        });
      }
    }
    return out;
  },
};

export const aiRules = [
  splitNewline, splitChars, splitSpace, replaceFirstOnly, truncate, repeatByLength, anchoredDot,
  invisibleChar, smartPunctuation, homoglyph,
];
export const unicodeSecurityRules = [bidiControl];
