# pure-guard

Zero-dependency scanner for JavaScript / TypeScript (Node >= 20.19). One CLI and API, three engines:

| Engine | Finds |
|---|---|
| `security` | hardcoded secrets, SQL / command injection, XSS sinks, `eval`, weak crypto / disabled TLS, Trojan-Source characters |
| `crash` | empty `catch` blocks (high) and `.catch(() => {})` (low: usually deliberate), `a.b.c` on runtime data without `?.`, `JSON.parse` outside `try` |
| `ai` | text-handling bugs LLM-written code repeats: `split('\n')`, `split('')`, first-only `replace`, invisible characters, smart quotes, look-alike letters |

```bash
npx pure-guard src                      # scan a folder
npx pure-guard src --format sarif > guard.sarif
npx pure-guard --list-rules
```

```js
import { scanSource, scanPaths } from 'pure-guard';

const findings = scanSource('el.innerHTML = name;', { filename: 'app.js' });
// [{ ruleId: 'security/xss', severity: 'high', line: 1, column: 3, fix: '…', … }]

const { findings: all } = await scanPaths(['src'], { minSeverity: 'medium' });
```

## How it avoids false alarms

Rules never run on raw text. A small lexer first blanks out comments, string/template text and regex bodies (offsets
preserved), so `// eval(x)` or `"el.innerHTML = x"` can never trigger a rule. Secrets are judged by **shape** (AWS, GitHub,
JWT that really decodes, credentialed DB URLs…) or by **name + entropy** (`apiKey = "…"`), with placeholders,
`process.env` lookups, identifiers, URLs, labels and provider example keys (`…EXAMPLE`) ignored.

Reports never contain a full secret: it is shown as `AKIA…(20 chars)` and fingerprints are one-way hashes (`node:crypto`).

## Rules and severities

Run `pure-guard --list-rules`. Severities: `low < medium < high < critical`. The CLI shows **medium and above** by default
(`--min-severity low` adds advisories such as `slice(0, N)` truncation); `--fail-on` defaults to `high`.

## What it does with real projects

- **Git-aware.** A secret in a file that `.gitignore` covers (a local `.env`) is not "committed": it is kept visible at
  *medium* and labelled `git-ignored`; other findings in ignored files drop to *low* (vendored / installed code). A secret in a
  tracked file stays *critical*. Use `--gitignored include` to turn this off or `--gitignored skip` to ignore such files entirely.
- **Skips generated code.** Minified / bundled files (Vite, webpack...) are only checked for secrets (a key baked into
  a bundle is a real leak) and listed under "Skipped"; `--include-minified` runs every rule on them.
- **Understands JSX.** Text between tags (apostrophes, backticks, `</b>`) is treated as text, `{…}` as code, and
  attribute strings are checked for secrets. In `.ts` files `<T>value` stays a type assertion.
- **One finding per secret.** The same value pasted 50 times in a file is reported once ("same value also at lines …").
- **Test and `.example` files** get lower severity for generic secret assignments; the null-chain and `JSON.parse` rules do not run on tests.
- **Bounded work.** Every regex is length-bounded and brace matching is linear, so a minified or hostile file cannot hang CI
  (a regression suite feeds 22 adversarial inputs at 100 KB each).

## CLI

```
pure-guard [options] [paths...]     default path: .      "-" reads stdin
  --format text|json|sarif          --engine security,crash,ai      --min-severity low|medium|high|critical
  --fail-on <level|never>  (default high; exit 1 at or above it)    --ignore <glob> (repeatable)
  --gitignored downgrade|skip|include     --include-minified
  --rule-off <id,id>   --max-file-size <bytes>   --stdin-filename <name>   --config <file>   --no-color
```

Exit codes: `0` clean, `1` findings at/above `--fail-on`, `2` usage or I/O error (with `--fail-on never`, only when
nothing could be scanned). `node_modules`, `.git`, lockfiles and `*.min.js` are always skipped; `dist`, `build`,
`coverage`, `.next`… are skipped inside a scanned folder and listed in the report (name the folder itself to scan it).
Symlinks inside a folder are never followed (a path you pass explicitly is). Binary and > 1 MB files are skipped
(listed in the report). `--ignore` patterns match from the scanned folder and from the working directory.

Library use: `import { scanSource, scanPaths } from 'pure-guard'` (ESM) or `require('pure-guard')` on Node >= 20.19 / 22.12.
TypeScript types are included (ESM projects: any recent TypeScript; CommonJS projects: TypeScript >= 5.8 with `"module": "nodenext"`).

Config (`pure-guard.config.json`, flags override it): `ignore`, `ruleOff`, `engines`, `minSeverity`, `failOn`,
`maxFileSize`, `format`, `includeMinified`, `gitIgnored`.

### Suppressing

```js
eval(trusted); // pure-guard-ignore security/eval
/* pure-guard-ignore-file crash/empty-catch */
```

A directive covers its own line and the next. Without rule ids it covers every rule; anything after it that isn't a
rule id is a reason (`// pure-guard-ignore security/eval: input is a fixed config`, or just
`// pure-guard-ignore because …`). Directives inside strings are ignored.

An empty `catch {}` with an explanatory comment inside (`catch { /* the file may not exist yet */ }`) is treated as
intentional. Output of `DOMPurify.sanitize(…)` / `sanitizeHtml(…)` is not reported as XSS.

### GitHub code scanning

```yaml
- run: npx pure-guard src --format sarif --fail-on never > guard.sarif
- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: guard.sarif }
```

## Not covered (use other tools for these)

Dependency vulnerabilities (the core of Snyk: needs an advisory database), secrets in **git history**, NoSQL / LDAP / XPath
injection (`$where`), reflected XSS through `res.send` / template engines, path traversal, SSRF, open redirects, prototype
pollution, ReDoS in your own regexes, insecure deserialisation, and any language other than JavaScript / TypeScript.

## Honest limits

This is a heuristic, text-based scanner: **no AST, no type information, no data-flow**.

- `crash/unsafe-property-chain` cannot know whether a property is really nullable. It is **medium** only for data that is certainly
  external (`JSON.parse`, `fetch`/`axios`, `.json()`, `req.body.x.y`) and **low** when guessed from a name (`user`, `data`) or a
  generic call (`getX()`); Express middleware props (`req.user`, `req.tenant`) are ignored.
- Injection rules see string building (`+`, `${}`) at the sink; they cannot follow a tainted value through variables.
- Entropy rules favour few false alarms over catching every secret. Pair with a secret scanner on git history.
- Only JS/TS source is analysed in depth. Config/text files (`.env`, `.json`, `.yml`, `.pem`…) get secret and hidden-character checks.

## Validation on real code

Run on about 4,000 source files from five real projects plus the installed npm, yarn and eas-cli packages. Every secret
finding was reviewed one by one; the other rules were reviewed by sampling each rule's findings (not exhaustively). Real leaks
were found (committed Google service-account keys, hard-coded SMTP passwords, AWS keys in `.env`). The false-positive classes that
surfaced (bundled output, JSX text, `db.exec()`, `author` / `tokenizers` as secret names, enum values, entity-containing literals,
`req.user` chains, quadratic regexes) are each pinned by a test in `test/regressions.test.js` / `test/robustness.test.js`.
Recall is checked against 26 patterns modelled on OWASP Juice Shop, NodeGoat and DVNA (`test/known-vulnerabilities.test.js`).
That is evidence, not a guarantee: heuristics always have misses and noise, and no precision/recall figure is claimed.

## Dev

```bash
npm test     # node:test, no dependencies. Includes a self-scan: the scanner must pass its own rules
```
