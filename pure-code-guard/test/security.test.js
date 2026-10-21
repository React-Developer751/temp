import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fake, has, ids, scan } from './helpers.js';

const SECRET = 'security/hardcoded-secret';

test('known-format secrets are critical', () => {
  for (const [label, value] of [['aws', fake.awsKey()], ['github', fake.github()], ['stripe', fake.stripe()], ['jwt', fake.jwt()]]) {
    const f = scan(`const v = "${value}";`).find((x) => x.ruleId === SECRET);
    assert.ok(f, label);
    assert.equal(f.severity, 'critical', label);
  }
});

test('private key block and credentialed database URLs', () => {
  assert.ok(has('const k = `-----BEGIN RSA PRIVATE KEY-----\nabc`;', SECRET));
  const f = scan('const u = "postgres://admin:Sup3rS3cretPw@db.internal/app";').find((x) => x.ruleId === SECRET);
  assert.equal(f.severity, 'critical');
  assert.ok(!f.snippet.includes('Sup3rS3cretPw'), 'password must be redacted in output');
});

test('database URLs without a password or with a placeholder are fine', () => {
  assert.ok(!has('const u = "postgres://db.internal/app";', SECRET));
  assert.ok(!has('const u = "postgres://user:${PASSWORD}@db/app";', SECRET));
  assert.ok(!has('const u = "mongodb://user:<password>@cluster/app";', SECRET));
  assert.ok(!has('const u = "redis://:password@localhost:6379";', SECRET));
});

test('JWT lookalikes that do not decode are ignored', () => {
  assert.ok(!has('const s = "eyJhaaaaaaaa.eyJbbbbbbbb.cccccccccc";', SECRET));
});

test('provider documentation example keys are allowed', () => {
  assert.ok(!has('const k = "AKIAIOSFODNN7EXAMPLE";', SECRET));
});

test('secrets in comments are found too', () => {
  assert.ok(has(`// temporary: ${fake.github()}`, SECRET));
});

test('named assignments: high-entropy value flagged, with the name in the message', () => {
  const f = scan(`const apiKey = "${fake.highEntropy()}";`).find((x) => x.ruleId === SECRET);
  assert.ok(f);
  assert.equal(f.severity, 'high');
  assert.match(f.message, /apiKey/);
});

test('object keys, JSON-style keys and ||-fallbacks are recognised', () => {
  assert.ok(has(`const c = { clientSecret: "${fake.highEntropy()}" };`, SECRET));
  assert.ok(has(`const c = { "api_key": "${fake.highEntropy()}" };`, SECRET));
  assert.ok(has(`const k = process.env.API_KEY || "${fake.highEntropy()}";`, SECRET));
  assert.ok(has('config.password = "Xk9#mP2$vL8@qR4z";', SECRET));
});

test('hardcoded password heuristics', () => {
  assert.ok(has('const dbPassword = "Xk9#mP2$vL8@qR4z";', SECRET));
  assert.ok(!has('const dbPassword = "changeme";', SECRET));
  assert.ok(!has('const password = "your_password_here";', SECRET));
  assert.ok(!has('const password = "password";', SECRET));
  assert.ok(!has('const password = "hunter";', SECRET), 'too short to judge');
});

test('no false alarms: env lookups, labels, identifiers, constants, URLs, placeholders', () => {
  for (const code of [
    'const key = process.env.API_KEY;',
    'const passwordLabel = "Enter your password";',
    'const tokenUrl = "https://auth.example.com/oauth/token";',
    'const PASSWORD_MIN_LENGTH = 12;',
    'const errorCode = "authenticationFailedError";',
    'const secretKeyName = "JWT_SECRET_KEY";',
    'const apiKeyHeader = "x-api-key";',
    'const token = "";',
    'const token = `${prefix}-${id}`;',
    'const secret = "<your-secret>";',
    'const authType = "bearer-token-auth";',
    'const sessionToken = req.headers.authorization;',
  ]) assert.ok(!has(code, SECRET), code);
});

test('test files and *.example files get a lower severity for generic assignments', () => {
  const f = scan(`const apiKey = "${fake.highEntropy()}";`, { filename: 'test/auth.test.js' }).find((x) => x.ruleId === SECRET);
  assert.equal(f.severity, 'medium');
  const ex = scan('SEED_PASSWORD=Xk9#mP2$vL8@qR4z', { filename: '.env.example' }).find((x) => x.ruleId === SECRET);
  assert.equal(ex.severity, 'medium');
});

test('secrets in .env and JSON config files', () => {
  const env = scan(`DB_PASSWORD=Xk9#mP2$vL8@qR4z\nPORT=3000\nAPI_URL=https://x.test\nGITHUB_TOKEN=${fake.github()}\n`, { filename: '.env' });
  assert.deepEqual(env.map((f) => f.line), [1, 4]);
  const json = scan(`{ "apiKey": "${fake.highEntropy()}", "name": "demo" }`, { filename: 'config.json' });
  assert.equal(json.length, 1);
});

test('the same secret found by two paths is reported once', () => {
  const found = scan(`const githubToken = "${fake.github()}";`).filter((f) => f.ruleId === SECRET);
  assert.equal(found.length, 1);
  assert.equal(found[0].severity, 'critical');
});

test('output never contains the full secret, anywhere', () => {
  const token = fake.github();
  const out = JSON.stringify(scan(`const githubToken = "${token}"; db.query(\`SELECT * FROM t WHERE a = '${token}' AND b = \${id}\`);`));
  assert.ok(!out.includes(token));
});

// ---- injection -------------------------------------------------------------------------------------------------

test('SQL injection: template interpolation and concatenation', () => {
  assert.ok(has('db.query(`SELECT * FROM users WHERE id = ${id}`);', 'security/sql-injection'));
  assert.ok(has('db.query("SELECT * FROM users WHERE id = " + id);', 'security/sql-injection'));
  assert.ok(has("db.query('DELETE FROM t WHERE name = \\'' + name + '\\'');", 'security/sql-injection'));
  assert.ok(has('db.query("UPDATE t SET a = 1 WHERE id = " + req.params.id);', 'security/sql-injection'));
  assert.ok(has('const q = "SELECT * FROM t"; q += " WHERE id = " + id;', 'security/sql-injection'));
});

test('SQL: parameters, tagged templates, literals and prose are fine', () => {
  for (const code of [
    'db.query("SELECT * FROM users WHERE id = $1", [id]);',
    'db.query("SELECT * FROM t WHERE id = ?", [id]);',
    'const rows = sql`SELECT * FROM users WHERE id = ${id}`;',
    'const q = "SELECT a FROM t WHERE x = 1" + " AND y = 2";',
    'const msg = `Select an option from the list ${n}`;',
    'log(`updated ${n} rows`);',
    'const label = "Delete from favourites: " + name;',
  ]) assert.ok(!has(code, 'security/sql-injection'), code);
});

test('SQL: dynamic identifiers/placeholders are only low severity', () => {
  const f = scan('db.query(`SELECT * FROM t WHERE id IN (${placeholders})`);').find((x) => x.ruleId === 'security/sql-injection');
  assert.equal(f.severity, 'low');
});

test('command injection', () => {
  assert.ok(has('exec(`git log ${branch}`);', 'security/command-injection'));
  assert.ok(has('execSync("ls " + dir);', 'security/command-injection'));
  assert.ok(!has('exec("git status");', 'security/command-injection'));
  assert.ok(!has('execFile("git", ["log", branch]);', 'security/command-injection'));
});

test('XSS sinks', () => {
  assert.ok(has('el.innerHTML = "<b>" + name + "</b>";', 'security/xss'));
  assert.ok(has('el.innerHTML = html;', 'security/xss'));
  assert.ok(has('el.innerHTML += `<li>${x}</li>`;', 'security/xss'));
  assert.ok(has('el.outerHTML = data;', 'security/xss'));
  assert.ok(has('el.insertAdjacentHTML("beforeend", html);', 'security/xss'));
  assert.ok(has('document.write(x);', 'security/xss'));
  assert.ok(has('<div dangerouslySetInnerHTML={{ __html: x }} />', 'security/xss', { filename: 'a.jsx' }));
});

test('XSS: literals, textContent, comparisons and mentions in strings/comments are fine', () => {
  for (const code of [
    'el.innerHTML = "<b>static</b>";',
    "el.innerHTML = '';",
    'el.textContent = userInput;',
    'if (el.innerHTML === html) {}',
    '// el.innerHTML = x',
    'const s = "el.innerHTML = x";',
    'el.insertAdjacentHTML("beforeend", "<hr>");',
  ]) assert.ok(!has(code, 'security/xss'), code);
});

test('eval, new Function, string timers', () => {
  assert.ok(has('eval(code);', 'security/eval'));
  assert.ok(has('const f = new Function("a", body);', 'security/eval'));
  assert.ok(has('setTimeout("tick()", 10);', 'security/eval'));
  for (const code of ['obj.eval(x);', 'const evaluate = 1; evaluate(x);', '// eval(x)', 'const s = "eval(x)";', 'setTimeout(() => tick(), 10);']) {
    assert.ok(!has(code, 'security/eval'), code);
  }
});

test('weak crypto and disabled TLS verification', () => {
  assert.ok(has('createHash("md5").update(x);', 'security/weak-crypto'));
  assert.ok(has("crypto.createHash('sha1');", 'security/weak-crypto'));
  assert.ok(!has('createHash("sha256");', 'security/weak-crypto'));
  assert.ok(has('https.request({ rejectUnauthorized: false });', 'security/weak-crypto'));
  assert.ok(has('process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";', 'security/weak-crypto'));
  assert.ok(!has('process.env.NODE_TLS_REJECT_UNAUTHORIZED = "1";', 'security/weak-crypto'));
});

test('suppression comments', () => {
  assert.deepEqual(ids('eval(x); // pure-guard-ignore security/eval'), []);
  assert.deepEqual(ids('// pure-guard-ignore security/eval\neval(x);'), []);
  assert.deepEqual(ids('// pure-guard-ignore\neval(x);'), []);
  assert.deepEqual(ids('/* pure-guard-ignore-file security/eval */\n\n\neval(x);'), []);
  assert.deepEqual(ids('// pure-guard-ignore crash/empty-catch\neval(x);'), ['security/eval']);
  assert.deepEqual(ids('const s = "pure-guard-ignore"; eval(x);'), ['security/eval'], 'text inside a string is not a directive');
});
