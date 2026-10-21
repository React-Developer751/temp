import { charClasses, matchAll, shannon } from '../util.js';

// ---------------------------------------------------------------------------------------------------------
// Hardcoded secrets
// ---------------------------------------------------------------------------------------------------------

/** Formats with a distinctive prefix/shape: no entropy guessing needed, so very few false alarms. */
const KNOWN_SECRETS = [
  { name: 'AWS access key ID', re: /\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA)[0-9A-Z]{16}\b/g },
  { name: 'GitHub token', re: /\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{50,255})\b/g },
  { name: 'Slack token', re: /\bxox[abprs]-[A-Za-z0-9-]{10,}\b/g },
  { name: 'Stripe live key', re: /\b[rs]k_live_[0-9A-Za-z]{20,}\b/g },
  { name: 'Google API key', re: /\bAIza[0-9A-Za-z_-]{35}\b/g },
  { name: 'npm token', re: /\bnpm_[A-Za-z0-9]{36}\b/g },
  { name: 'SendGrid key', re: /\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b/g },
  { name: 'private key block', re: /-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----/g },
];

const JWT_RE = /\beyJ[A-Za-z0-9_-]{8,4096}\.eyJ[A-Za-z0-9_-]{8,4096}\.[A-Za-z0-9_-]{8,1024}\b/g;
const BEARER_RE = /\bBearer\s+([A-Za-z0-9\-._~+/]{24,2048}=*)/g;
const DB_URL_RE = /\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|amqps?|mssql):\/\/[^\s:/@'"`<>]{1,200}:([^\s@'"`<>]{1,200})@[^\s'"`<>]{1,300}/gi;

const PLACEHOLDER = new RegExp(
  '^(?:x+|\\*+|\\.+|-+|_+|<.*>|\\{\\{.*\\}\\}|\\$\\{.*\\}|%[sd]|\\$[A-Z_]+|your[-_ ].*|change[-_]?me.*|' +
  'example.*|sample.*|dummy.*|placeholder.*|redacted|secret|password|passwd|token|apikey|api[-_]key|todo|fixme|null|undefined|none|' +
  'test|testing|abc+|a?b?c?d?e?f?|1234.*|foo|bar|baz|admin|root|user|username|default|string|empty|unset)$', 'i');

/** abcdefgh, 12345678, ponmlkji: documentation-style fillers. */
function isSequential(value) {
  if (value.length < 6) return false;
  let steps = 0;
  for (let k = 1; k < value.length; k++) if (Math.abs(value.charCodeAt(k) - value.charCodeAt(k - 1)) === 1) steps++;
  return steps / (value.length - 1) > 0.7;
}

function isPlaceholder(value) {
  const v = value.trim();
  return isSequential(v) || PLACEHOLDER.test(v) || /x{4,}|your[-_]|change[-_]?me|example|<[^>]+>|\$\{|\{\{|\[REDACTED\]|\*{4,}/i.test(v);
}

/** camelCase / kebab-case / snake_case / CONSTANT_CASE words are identifiers or messages, not secrets. */
function looksLikeIdentifier(value) {
  // camelCase / PascalCase words have long humps and almost no digits; random strings have short humps and digits.
  if (/^[A-Za-z0-9]+$/.test(value) && (value.match(/\d/g) ?? []).length <= 1) {
    const humps = value.split(/(?=[A-Z])/);
    if (humps.length >= 2 && value.length / humps.length >= 3.5) return true;
  }
  return /^[A-Za-z]+(?:[-_.][A-Za-z]+)+$/.test(value) || /^[A-Z0-9]+(?:_[A-Z0-9]+)+$/.test(value);
}

function looksLikePathOrUrl(value) {
  return /^(?:\.{0,2}\/|~\/|[a-z][a-z0-9+.-]*:\/\/)/i.test(value) && !/^[a-z][a-z0-9+.-]*:\/\/[^/\s:@]+:[^/\s@]+@/i.test(value);
}

// (?![a-z]) keeps "author", "tokenizers", "passport" and "secretary" from looking like secrets; "accessToken" and "AUTH_KEY" still match.
const SECRET_NAME = /(?:pass(?:word|wd|phrase)?|pwd|secret|token|api[_-]?key|apikey|private[_-]?key|access[_-]?key|auth(?:orization)?|credential|signing[_-]?key|encryption[_-]?key|client[_-]?secret)(?![a-z])/i;
const NOT_A_SECRET_NAME = /(label|placeholder|field|type|name|regex|pattern|length|min|max|url|uri|path|header|prefix|suffix|expires?|expiry|ttl|count|hint|message|msg|error|text|title|description|required|valid|strength|policy|input|selector|route|endpoint|header|schema|enabled|flag|id)s?$/i;

/** Decides whether `value` assigned to `name` is a real secret. Returns a reason string or null. */
export function judgeAssignment(name, value) {
  const last = name.split('.').pop();
  if (!SECRET_NAME.test(last) || NOT_A_SECRET_NAME.test(last)) return null;
  if (value.length < 8 || value.length > 512 || /\s/.test(value)) return null;
  if (isPlaceholder(value) || looksLikeIdentifier(value) || looksLikePathOrUrl(value)) return null;

  const isPassword = /pass(?:word|wd|phrase)?|pwd/i.test(last);
  const bits = shannon(value);
  const classes = charClasses(value);
  if (isPassword) {
    return classes >= 2 || bits >= 3.2 ? `hardcoded password in "${name}"` : null;
  }
  const hex = /^[0-9a-f]+$/i.test(value);
  if (value.length < 16 || classes < 2) return null;
  if (hex ? value.length >= 32 && bits >= 3 : bits >= 3.5) return `high-entropy secret in "${name}" (${bits.toFixed(1)} bits/char)`;
  return null;
}

function jwtIsReal(token) {
  try {
    const header = JSON.parse(Buffer.from(token.split('.')[0], 'base64url').toString('utf8'));
    return typeof header === 'object' && header !== null && 'alg' in header;
  } catch {
    return false;
  }
}

/** Known-format secrets inside any chunk of text. `base` is the chunk's offset in the file. */
function* findKnownSecrets(text, base) {
  for (const { name, re } of KNOWN_SECRETS) {
    for (const m of matchAll(re, text)) {
      if (/EXAMPLE/.test(m[0])) continue; // keys from the providers' own documentation (e.g. AKIAIOSFODNN7EXAMPLE)
      yield { start: base + m.index, end: base + m.index + m[0].length, secret: m[0], message: `${name} committed in source`, severity: 'critical' };
    }
  }
  for (const m of matchAll(JWT_RE, text)) {
    if (jwtIsReal(m[0])) yield { start: base + m.index, end: base + m.index + m[0].length, secret: m[0], message: 'JWT committed in source', severity: 'critical' };
  }
  for (const m of matchAll(DB_URL_RE, text)) {
    if (!isPlaceholder(m[1])) {
      const at = m.index + m[0].indexOf(m[1]);
      yield { start: base + at, end: base + at + m[1].length, secret: m[1], message: 'database connection string contains a password', severity: 'critical' };
    }
  }
  for (const m of matchAll(BEARER_RE, text)) {
    if (!isPlaceholder(m[1]) && shannon(m[1]) >= 3.5 && charClasses(m[1]) >= 2) {
      yield { start: base + m.index + m[0].length - m[1].length, end: base + m.index + m[0].length, secret: m[1], message: 'hardcoded Bearer token', severity: 'high' };
    }
  }
}

/** Names that could describe the string literal starting at `start`: `name = '…'`, `name: '…'`, `x = process.env.NAME || '…'`. */
function namesBeforeString(source, start) {
  const window = source.slice(Math.max(0, start - 160), start);
  const fallback = /([A-Za-z_$][\w$.-]*)['"\]]?\s*[:=]\s*([\w$.[\]'"]+)\s*(?:\|\||\?\?)\s*$/.exec(window); // x = process.env.Y || 'lit'
  if (fallback) return [fallback[1], fallback[2].replace(/\[['"]?|['"]?\]/g, '.')];
  // name = '…'   name: '…'   "name": '…'   and comparisons: password === '…', secret !== '…' (a hardcoded credential check)
  const direct = /([A-Za-z_$][\w$.-]*)['"\]]?\s*(?:[!=]==?|[:=]|\+=)\s*$/.exec(window);
  return direct ? [direct[1]] : [];
}

const secrets = {
  id: 'security/hardcoded-secret',
  engine: 'security',
  severity: 'high',
  kinds: ['code', 'text'],
  description: 'Hardcoded API keys, tokens, passwords, private keys and credentialed connection strings',
  check({ source, kind, tokens, isTest }) {
    const out = [];
    if (kind === 'code') {
      for (const s of tokens.strings) {
        out.push(...findKnownSecrets(source.slice(s.start, s.end), s.start));
        if (s.hasExpr || s.quote === '`') continue;
        const reason = namesBeforeString(source, s.start).map((name) => judgeAssignment(name, s.value)).find(Boolean);
        if (reason) out.push({ start: s.start + 1, end: s.end - 1, secret: s.value, message: reason, severity: isTest ? 'medium' : 'high' });
      }
      for (const c of tokens.comments) out.push(...findKnownSecrets(c.text, c.start + 2));
    } else {
      out.push(...findKnownSecrets(source, 0));
      let offset = 0;
      // pure-guard-ignore ai/split-newline: offsets must stay exact; \r is whitespace to the value regex
      for (const line of source.split('\n')) {
        if (line.length > 20_000) { offset += line.length + 1; continue; } // minified / generated line: not config
        // key=value, key: value and "key": "value" - several per line for minified JSON.
        for (const m of matchAll(/["']?([A-Za-z_][\w.-]{0,80})["']?[ \t]{0,8}[:=][ \t]{0,8}["']?([^"'\s,]{1,600})["']?/, line)) {
          const reason = judgeAssignment(m[1], m[2]);
          if (reason) {
            const at = offset + m.index + m[0].lastIndexOf(m[2]);
            out.push({ start: at, end: at + m[2].length, secret: m[2], message: reason, severity: isTest ? 'medium' : 'high' });
          }
        }
        offset += line.length + 1;
      }
    }
    // Same secret reported by two paths (known pattern + named assignment): keep the most severe one.
    const best = new Map();
    for (const f of out) {
      const key = `${f.start}`;
      const old = best.get(key);
      if (!old || (f.severity === 'critical' && old.severity !== 'critical')) best.set(key, f);
    }
    return [...best.values()];
  },
};

// ---------------------------------------------------------------------------------------------------------
// Injection: SQL, command, XSS, eval
// ---------------------------------------------------------------------------------------------------------

const COLUMN = '[\\w."`()*]+(?:\\s+as\\s+\\w+)?'; // one column / function / alias: prose ("an option") has bare words, SQL has commas
const SQL_STATEMENT = new RegExp(
  '^\\s*(?:' +
  `select\\s+(?:distinct\\s+)?(?:\\*|${COLUMN}(?:\\s*,\\s*${COLUMN})*)\\s+from\\s+[\\w."\`[\\]]+` +
  '|insert\\s+into\\s+[\\w."`[\\]]+\\s*(?:\\(|values\\b|select\\b)' +
  '|update\\s+[\\w."`[\\]]+\\s+set\\b' +
  '|delete\\s+from\\s+[\\w."`[\\]]+\\s*(?:where\\b|;|$)' +
  '|drop\\s+(?:table|database)\\b|alter\\s+table\\b|truncate\\s+table\\b|merge\\s+into\\b|with\\s+[\\w"]+\\s+as\\s*\\()', 'i');
const SQL_KEYWORD = /\b(?:where|and|or|values|set|like|limit|offset|in)\b/i;
const SQL_OPEN_ENDED = /(?:[=<>(,']|\blike|\bin)[ \t]{0,8}\(?[ \t]{0,8}['"]?[ \t]{0,8}$/i;
const MAX_SQL_STRING = 4000; // real queries are short; bounding the length bounds the regex work
// ALL_CAPS constants and "cond ? 'literal' : 'literal'" can only produce text the developer wrote.
const LITERAL = String.raw`(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")`;
const CONSTANT_EXPR = new RegExp(`^\\s*(?:[A-Z][A-Z0-9_]*|${LITERAL}|[^?:]{1,200}\\?\\s*${LITERAL}\\s*:\\s*${LITERAL})\\s*$`);
const SAFE_IDENTIFIER_EXPR = /placeholder|\?|\.join\(|table|column|field|orderBy|direction|limit|offset/i;

/** True when string token `s` is followed by "+ <something that is not a literal>". */
function concatenatedWithDynamic(source, masked, s) {
  let k = s.end;
  while (k < masked.length && /\s/.test(masked[k])) k++;
  if (masked[k] !== '+' || masked[k + 1] === '+' || masked[k + 1] === '=') return false;
  k++;
  while (k < masked.length && /\s/.test(masked[k])) k++;
  return k < source.length && !/['"\d]/.test(source[k]);
}

const sqlInjection = {
  id: 'security/sql-injection',
  engine: 'security',
  severity: 'high',
  kinds: ['code'],
  description: 'SQL built by string concatenation or template interpolation instead of parameters',
  check({ source, tokens }) {
    const out = [];
    for (const s of tokens.strings) {
      if (s.value.length > MAX_SQL_STRING) continue;
      if (s.quote === '`') {
        if (!s.hasExpr || s.tagged || !SQL_STATEMENT.test(s.value.replaceAll('\0', '?'))) continue;
        const exprs = s.exprs.map((e) => source.slice(e.start, e.end));
        if (exprs.every((e) => CONSTANT_EXPR.test(e))) continue;
        const allSafe = exprs.every((e) => CONSTANT_EXPR.test(e) || SAFE_IDENTIFIER_EXPR.test(e));
        // Values bound as parameters (…, [a, b]) / .get(...params): only the interpolated fragment is in question.
        const parameterised = /^\s*(?:,\s*[[\w.]|\)\s*\.\s*(?:get|all|run|iterate|pluck)\s*\(\s*(?:\.\.\.|\[|\w))/.test(source.slice(s.end, s.end + 80));
        out.push({
          start: s.start, end: s.end,
          severity: allSafe ? 'low' : parameterised ? 'medium' : 'high',
          message: allSafe ? 'SQL built with template interpolation (identifiers/placeholders only: make sure they are allow-listed)'
            : parameterised ? 'SQL fragment interpolated into a parameterised query: make sure the fragment is built from constants, never from user input'
              : 'SQL query built with template interpolation: user input can change the query',
          fix: 'Use parameters: db.query("SELECT … WHERE id = $1", [id]) (or ? placeholders), never ${…} inside SQL.',
        });
      } else if ((SQL_STATEMENT.test(s.value) || (SQL_KEYWORD.test(s.value) && SQL_OPEN_ENDED.test(s.value))) && concatenatedWithDynamic(source, tokens.masked, s)) {
        out.push({
          start: s.start, end: s.end,
          message: 'SQL query built by string concatenation: user input can change the query',
          fix: 'Use parameters: db.query("SELECT … WHERE id = $1", [id]).',
        });
      }
    }
    return out;
  },
};

const commandInjection = {
  id: 'security/command-injection',
  engine: 'security',
  severity: 'high',
  kinds: ['code'],
  description: 'Shell commands built from dynamic strings (exec / execSync)',
  check({ source, tokens }) {
    const out = [];
    for (const s of tokens.strings) {
      const before = source.slice(Math.max(0, s.start - 40), s.start);
      // bare exec()/execSync() or child_process.exec(): not db.exec() (SQLite), regex.exec(), etc.
      if (!/(?:^|[^.\w$])(?:exec|execSync)\s*\(\s*$/.test(before) && !/\b(?:child_process|childProcess|cp|shelljs)\s*\.\s*(?:exec|execSync)\s*\(\s*$/.test(before)) continue;
      const dynamic = (s.quote === '`' && s.hasExpr) || (s.quote !== '`' && concatenatedWithDynamic(source, tokens.masked, s));
      if (dynamic) {
        out.push({
          start: s.start, end: s.end,
          message: 'shell command built from dynamic input: command injection',
          fix: 'Use execFile / spawn with an argument array (no shell), e.g. execFile("git", ["log", branch]).',
        });
      }
    }
    return out;
  },
};

const xss = {
  id: 'security/xss',
  engine: 'security',
  severity: 'high',
  kinds: ['code'],
  description: 'Writing non-literal values into innerHTML / outerHTML / insertAdjacentHTML / document.write',
  check({ source, tokens }) {
    const out = [];
    const { masked } = tokens;
    const byStart = new Map(tokens.strings.map((t) => [t.start, t]));
    for (const m of matchAll(/\.\s*(innerHTML|outerHTML)\s*(\+?=)(?!=)/, masked)) {
      // A lone string literal (even one containing ";" like "&gt;") has nothing to inject.
      let at = m.index + m[0].length;
      while (/[ \t]/.test(source[at] ?? '')) at++;
      const literal = byStart.get(at);
      if (literal && !literal.hasExpr) {
        let end = literal.end;
        while (/[ \t]/.test(source[end] ?? '')) end++;
        if (end >= source.length || /[;\n\r}),]/.test(source[end])) continue;
      }
      out.push({
        start: m.index, end: m.index + m[0].length,
        message: `${m[1]} assigned a non-literal value: XSS if any part is user-controlled`,
        fix: 'Use textContent for text, or sanitise the HTML (e.g. DOMPurify / Sanitizer API) before inserting.',
      });
    }
    for (const m of matchAll(/\.\s*(insertAdjacentHTML)\s*\(\s*[^,)]{1,200},\s*([^)]{0,500})\)/, masked)) {
      const arg = source.slice(m.index, m.index + m[0].length).split(',').slice(1).join(',').replace(/\)\s*$/, '').trim();
      if (/^(['"])(?:(?!\1).)*\1$/.test(arg)) continue;
      out.push({ start: m.index, end: m.index + m[0].length, message: 'insertAdjacentHTML with a non-literal value: XSS if any part is user-controlled', fix: 'Use insertAdjacentText, or sanitise the HTML first.' });
    }
    for (const m of matchAll(/\bdocument\s*\.\s*write(?:ln)?\s*\(/, masked)) {
      out.push({ start: m.index, end: m.index + m[0].length, message: 'document.write injects raw HTML', fix: 'Build DOM nodes (createElement / textContent) instead.' });
    }
    for (const m of matchAll(/\bdangerouslySetInnerHTML\b/, masked)) {
      out.push({ start: m.index, end: m.index + m[0].length, message: 'dangerouslySetInnerHTML bypasses React escaping', fix: 'Render as text, or sanitise the HTML before passing it in.' });
    }
    return out;
  },
};

const dynamicCode = {
  id: 'security/eval',
  engine: 'security',
  severity: 'high',
  kinds: ['code'],
  description: 'eval(), new Function() and string-based setTimeout/setInterval',
  check({ tokens }) {
    const out = [];
    const { masked } = tokens;
    const report = (index, length, message) => out.push({ start: index, end: index + length, message, fix: 'Parse data with JSON.parse; pass real functions, not strings.' });
    for (const m of matchAll(/(?<![\w$.])eval\s*\(/, masked)) report(m.index, m[0].length, 'eval() runs arbitrary code');
    for (const m of matchAll(/\bnew\s+Function\s*\(/, masked)) report(m.index, m[0].length, 'new Function() runs arbitrary code');
    for (const m of matchAll(/\b(?:setTimeout|setInterval)\s*\(\s*(?=['"`])/, masked)) {
      report(m.index, m[0].length, 'setTimeout/setInterval with a string argument behaves like eval()');
    }
    return out;
  },
};

const weakCrypto = {
  id: 'security/weak-crypto',
  engine: 'security',
  severity: 'medium',
  kinds: ['code'],
  description: 'MD5/SHA-1 hashing and disabled TLS certificate verification',
  check({ source, tokens }) {
    const out = [];
    const { masked } = tokens;
    for (const m of matchAll(/\bcreateHash\s*\(\s*(?=['"])/, masked)) {
      const arg = /^(['"])([\w-]+)\1/.exec(source.slice(m.index + m[0].length));
      if (arg && /^(?:md5|sha1|md4)$/i.test(arg[2])) {
        const context = source.slice(Math.max(0, m.index - 120), m.index + 300);
        const securityUse = /pass|secret|token|sign|auth|hmac|credential|session|csrf|nonce/i.test(context);
        out.push({
          start: m.index, end: m.index + m[0].length,
          severity: securityUse ? 'medium' : 'low',
          message: securityUse ? `${arg[2]} is broken for security use` : `${arg[2]} is fine for cache keys / checksums but broken if this value protects anything`,
          fix: 'Use sha256+ (and scrypt/argon2/bcrypt for passwords).',
        });
      }
    }
    for (const m of matchAll(/\brejectUnauthorized\s*:\s*false\b/, masked)) {
      out.push({ start: m.index, end: m.index + m[0].length, severity: 'high', message: 'TLS certificate verification is disabled (man-in-the-middle risk)', fix: 'Remove rejectUnauthorized: false; trust a custom CA via the `ca` option instead.' });
    }
    for (const m of matchAll(/\bNODE_TLS_REJECT_UNAUTHORIZED\b/, masked)) {
      if (/^\s*\]?\s*=\s*['"]?0/.test(source.slice(m.index + m[0].length))) {
        out.push({ start: m.index, end: m.index + m[0].length, severity: 'high', message: 'NODE_TLS_REJECT_UNAUTHORIZED=0 disables TLS verification process-wide', fix: 'Remove it; trust a custom CA with NODE_EXTRA_CA_CERTS.' });
      }
    }
    return out;
  },
};

export const securityRules = [secrets, sqlInjection, commandInjection, xss, dynamicCode, weakCrypto];
