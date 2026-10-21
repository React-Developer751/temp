import { test } from 'node:test';
import assert from 'node:assert/strict';
import { has, ids, scan } from './helpers.js';

test('split("\\n") and split("\\r\\n")', () => {
  assert.ok(has("text.split('\\n');", 'ai/split-newline'));
  assert.ok(has('text.split("\\n").map(trim);', 'ai/split-newline'));
  assert.ok(has('text.split("\\r\\n");', 'ai/split-newline'));
  assert.ok(!has('text.split(/\\r?\\n/);', 'ai/split-newline'));
  assert.ok(!has('text.split(",");', 'ai/split-newline'));
  assert.ok(!has('const s = "a.split(\'\\\\n\')";', 'ai/split-newline'));
});

test('split("") and split(" ")', () => {
  assert.ok(has("word.split('').reverse().join('');", 'ai/split-empty'));
  assert.ok(has('word.split("");', 'ai/split-empty'));
  assert.ok(!has('word.split(/(?:)/u);', 'ai/split-empty'));
  assert.ok(has('line.split(" ");', 'ai/split-space'));
  assert.ok(!has('line.split(/\\s+/);', 'ai/split-space'));
});

test('replace with a string pattern only replaces the first match', () => {
  const nl = scan("s.replace('\\n', '<br>');").find((f) => f.ruleId === 'ai/replace-first-only');
  assert.equal(nl.severity, 'medium');
  const other = scan("s.replace('foo', 'bar');").find((f) => f.ruleId === 'ai/replace-first-only');
  assert.equal(other.severity, 'low');
  assert.ok(!has("s.replaceAll('\\n', '<br>');", 'ai/replace-first-only'));
  assert.ok(!has("s.replace(/\\n/g, '<br>');", 'ai/replace-first-only'));
  assert.ok(!has('s.replace(pattern, "x");', 'ai/replace-first-only'));
});

test('truncating and sizing by length', () => {
  assert.ok(has('title.slice(0, 40) + "…";', 'ai/truncate-by-length'));
  assert.ok(has('title.substring(0, 10);', 'ai/truncate-by-length'));
  assert.ok(!has('title.slice(1, 40);', 'ai/truncate-by-length'));
  assert.ok(has('"-".repeat(title.length);', 'ai/width-from-length'));
  assert.ok(!has('"-".repeat(20);', 'ai/width-from-length'));
});

test('anchored regex with dot but no m/s flag', () => {
  assert.ok(has('const re = /^Title: (.*)$/;', 'ai/regex-multiline'));
  assert.ok(!has('const re = /^Title: (.*)$/m;', 'ai/regex-multiline'));
  assert.ok(!has('const re = /^Title: (.*)$/s;', 'ai/regex-multiline'));
  assert.ok(!has('const re = /https?:\\/\\/[^/]+\\/(.*)$/;', 'ai/regex-multiline'), 'only $ - not a whole-string match');
  assert.ok(!has('const re = /^[.*]+$/;', 'ai/regex-multiline'), 'dot inside a character class is a literal');
});

// ---- hidden characters -----------------------------------------------------------------------------------------

test('Trojan Source: bidi controls are critical anywhere, even in strings and comments', () => {
  for (const code of ['const isAdmin = "user‮";', '// access ⁦level⁩ check', 'x = 1;‭y = 2;']) {
    const f = scan(code).find((x) => x.ruleId === 'security/bidi-control');
    assert.ok(f, JSON.stringify(code));
    assert.equal(f.severity, 'critical');
  }
});

test('zero-width characters: in code and in strings', () => {
  const inCode = scan('const na​me = 1;').find((f) => f.ruleId === 'ai/invisible-char');
  assert.equal(inCode.severity, 'high');
  const inString = scan('const s = "ad​min";').find((f) => f.ruleId === 'ai/invisible-char');
  assert.equal(inString.severity, 'medium');
  assert.ok(has('const s = "a⁠b";', 'ai/invisible-char'));
});

test('legitimate joiners are not flagged: emoji sequences, byte-order mark, Indic/Persian text', () => {
  assert.ok(!has('const family = "👨‍👩‍👧";', 'ai/invisible-char'));
  assert.ok(!has('﻿const a = 1;', 'ai/invisible-char'));
  assert.ok(!has('const s = "क्‍ष";', 'ai/invisible-char'));
  assert.ok(!has('const s = "می‌خواهم";', 'ai/invisible-char'));
});

test('non-breaking space in code is an error, inside a string it is data', () => {
  assert.ok(has('const x = 1;', 'ai/invisible-char'));
  assert.ok(!has('const s = "a b";', 'ai/invisible-char'));
  assert.ok(!has('// a b', 'ai/invisible-char'));
});

test('smart quotes and dashes used as code, one finding per line', () => {
  const found = scan('const x = \u201Chello\u201D;').filter((f) => f.ruleId === 'ai/smart-punctuation');
  assert.equal(found.length, 1);
  assert.ok(has('print(\u201Chi\u201D);', 'ai/smart-punctuation'));
  assert.ok(has('function f() { return \u2018x\u2019; }', 'ai/smart-punctuation'));
  assert.ok(has('const n = a \u2013 b;', 'ai/smart-punctuation'));
  assert.ok(!has('const s = "it\u2019s fine \u2014 really";', 'ai/smart-punctuation'));
  assert.ok(!has('// it\u2019s fine', 'ai/smart-punctuation'));
});

test('homoglyph identifiers: Latin mixed with Cyrillic/Greek', () => {
  assert.ok(has('const pаssword = 1;', 'ai/homoglyph-identifier')); // Cyrillic "а"
  assert.ok(has('const οbj = 1;', 'ai/homoglyph-identifier')); // Greek omicron
  assert.ok(!has('const привет = 1;', 'ai/homoglyph-identifier'), 'a fully Cyrillic name is legitimate');
  assert.ok(!has('const s = "pаssword";', 'ai/homoglyph-identifier'), 'strings are data');
});

test('hidden characters are also found in config/text files', () => {
  assert.deepEqual(ids('{"a": "x‮y"}', { filename: 'c.json' }), ['security/bidi-control']);
  assert.deepEqual(ids('KEY=a​b', { filename: '.env' }), ['ai/invisible-char']);
});

test('clean multilingual text raises nothing', () => {
  assert.deepEqual(ids('const greeting = "नमस्ते 世界 🌍 مرحبا";\n// こんにちは'), []);
});
