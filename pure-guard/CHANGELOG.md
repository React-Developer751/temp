# Changelog

## 0.2.0
- Package renamed to `pure-guard` (same as the CLI), so `npx pure-guard` works.
- JSX-aware lexing: text in tags (`Don't`, a backtick, `</b>`) no longer hides `eval`, `innerHTML` or
  `dangerouslySetInnerHTML` that follow; JSX attribute strings are checked for secrets.
- SQL injection: no more high-severity reports on prose / HTML strings (`'Logged in as <b>' + user`); a fragment must
  look like `WHERE col = '`, `LIKE '%`, `IN (`, `VALUES (`, `LIMIT`.
- Fixed: a long whitespace or comment run after `catch` made the scan quadratic (minutes on a 1 MB file).
- Fixed: with the secret rule off (`--rule-off`, `--engine ai`) other findings printed the full secret.
- New detections: `require('child_process').exec(…)`, `execAsync(…)`, `window.eval(…)`, `Function('…')`,
  literal keys in `jwt.sign/verify(…, 'key')` and `createHmac(alg, 'key')`.
- Fewer false positives: commented empty catch blocks, sanitised HTML (DOMPurify / sanitize-html), Greek letters in
  names (`Δt`, `μs`), `split('\n')` followed by `.trim()`, `response.headers` of a `fetch()` Response, NBSP in JSX text.
- Minified / bundled files are still checked for secrets.
- `crash/empty-promise-catch` is now `low` (an advisory): `.catch(() => {})` is usually a deliberate fire-and-forget.
- `split('\n')` is not reported when the same chain trims each line or joins back with `\n` (multi-line chains too).
- A symlink given on the command line is followed; `--ignore` paths also match from the working directory;
  skipped `build` / `dist` / `coverage` folders are listed; `scanPaths('src')` accepts a single string.
- Suppression directives accept a reason (`// pure-guard-ignore because …`).
- `--fail-on never` no longer exits 2 because one file was unreadable; SARIF uses `file://` URIs for absolute paths.
- File size is checked before reading.

## 0.1.0
- Initial release: security, crash and AI-text engines; CLI with text / JSON / SARIF output; inline and file suppression; config file.
- Git-aware severity (`.gitignore`), minified / bundled file skipping, repeated-secret collapsing, evidence-tiered null-chain rule.
- Bounded regexes and linear brace matching (no quadratic behaviour on minified or hostile input).
- Validated on real projects and a known-vulnerability recall suite.
