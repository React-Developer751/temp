// Recall check: patterns from deliberately vulnerable apps (OWASP Juice Shop, NodeGoat, DVNA) and well-known incidents.
// Each snippet must be reported by the named rule. See README "Not covered" for what this scanner does not look for.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fake, ids } from './helpers.js';

const CASES = [
  ['Juice Shop: SQL login by string concatenation',
    "models.sequelize.query(\"SELECT * FROM Users WHERE email = '\" + (req.body.email || '') + \"' AND password = '\" + security.hash(req.body.password || '') + \"' AND deletedAt IS NULL\", { model: models.User, plain: true })",
    'security/sql-injection'],
  ['Juice Shop: product search interpolated into SQL',
    'models.sequelize.query(`SELECT * FROM Products WHERE ((name LIKE \'%${criteria}%\' OR description LIKE \'%${criteria}%\') AND deletedAt IS NULL) ORDER BY name`)',
    'security/sql-injection'],
  ['NodeGoat: eval on request body (server-side JS injection)',
    'const preTax = eval(req.body.preTax);\nconst afterTax = eval(req.body.afterTax);',
    'security/eval'],
  ['NodeGoat: setTimeout with a string built from input',
    'setTimeout("poll(" + req.query.id + ")", 1000);',
    'security/eval'],
  ['DVNA: command injection through exec',
    'const out = exec("ping -c 2 " + req.body.address);',
    'security/command-injection'],
  ['Classic: command injection through a template string',
    'child_process.exec(`convert ${req.query.file} out.png`, cb);',
    'security/command-injection'],
  ['Reflected DOM XSS: location.hash into innerHTML',
    'document.getElementById("greeting").innerHTML = "Hello " + decodeURIComponent(location.hash.slice(1));',
    'security/xss'],
  ['React: dangerouslySetInnerHTML with user content',
    'const C = ({ post }) => <div dangerouslySetInnerHTML={{ __html: post.body }} />;',
    'security/xss'],
  ['document.write of a query parameter',
    'document.write("<h1>" + new URLSearchParams(location.search).get("name") + "</h1>");',
    'security/xss'],
  ['Hardcoded AWS key in a config module',
    `module.exports = { aws: { accessKeyId: "${fake.awsKey()}", region: "eu-west-1" } };`,
    'security/hardcoded-secret'],
  ['Hardcoded JWT signing secret fallback',
    `const secret = process.env.JWT_SECRET || "${fake.highEntropy()}";\njwt.sign(payload, secret);`,
    'security/hardcoded-secret'],
  ['Committed GitHub token in a CI helper',
    `const headers = { Authorization: "token ${fake.github()}" };`,
    'security/hardcoded-secret'],
  ['Committed service-account private key',
    '{ "type": "service_account", "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvAIBADANBgkqhkiG9w0B\\n-----END PRIVATE KEY-----\\n" }',
    'security/hardcoded-secret',
    'sa.json'],
  ['Database URL with credentials',
    'const url = "mongodb+srv://admin:Sup3rS3cretPw@cluster0.abc12.mongodb.net/app";',
    'security/hardcoded-secret'],
  ['TLS verification switched off "temporarily"',
    'const agent = new https.Agent({ rejectUnauthorized: false });',
    'security/weak-crypto'],
  ['Password hashed with MD5',
    'const hash = crypto.createHash("md5").update(req.body.password).digest("hex");',
    'security/weak-crypto'],
  ['Silent failure: empty catch around a payment call',
    'try {\n  await chargeCard(order);\n} catch (e) {}\nmarkPaid(order);',
    'crash/empty-catch'],
  ['Crash: JSON.parse of a request body outside try',
    'app.post("/hook", (req, res) => {\n  const event = JSON.parse(req.body.payload);\n  res.sendStatus(200);\n});',
    'crash/unguarded-json-parse'],
  ['Crash: nested property of an API response',
    'const res = await fetch(url);\nconst body = await res.json();\nreturn body.data.user.email;',
    'crash/unsafe-property-chain'],
  ['Trojan Source: bidi override hides an if-condition',
    'if (accessLevel != "user‮ ⁦// Check if admin⁩ ⁦") {\n  grant();\n}',
    'security/bidi-control'],
  ['AI paste: curly quotes break the file',
    'const message = “Hello world”;\nconsole.log(message);',
    'ai/smart-punctuation'],
  ['AI paste: zero-width space inside an identifier',
    'const isAdm​in = false;',
    'ai/invisible-char'],
  ['AI text bug: split on \\n leaves \\r on Windows input',
    "const rows = csv.split('\\n').map((l) => l.split(','));",
    'ai/split-newline'],
  ['AI text bug: reversing a string by characters breaks emoji',
    "const reversed = name.split('').reverse().join('');",
    'ai/split-empty'],
  ['AI text bug: replace("\\n", "<br>") only converts the first line break',
    "const html = text.replace('\\n', '<br>');",
    'ai/replace-first-only'],
  ['Homoglyph attack: Cyrillic "а" in an identifier',
    'const pаssword = req.body.password;',
    'ai/homoglyph-identifier'],
];

for (const [name, code, rule, filename = 'app.js'] of CASES) {
  test(`detects: ${name}`, () => {
    assert.ok(ids(code, { filename }).includes(rule), `${rule} not reported for: ${code.slice(0, 80)}`);
  });
}

const SAFE_VARIANTS = [
  ['parameterised login query', 'models.sequelize.query("SELECT * FROM Users WHERE email = ? AND password = ?", { replacements: [email, hash] })'],
  ['Number() instead of eval', 'const preTax = Number(req.body.preTax);'],
  ['execFile with an argument array', 'execFile("ping", ["-c", "2", req.body.address], cb);'],
  ['textContent', 'el.textContent = "Hello " + name;'],
  ['secret read from the environment', 'const secret = process.env.JWT_SECRET;'],
  ['logged catch', 'try { await charge(o); } catch (e) { logger.error(e); throw e; }'],
  ['guarded JSON.parse', 'try { const e = JSON.parse(body); use(e); } catch (err) { return bad(err); }'],
];

for (const [name, code] of SAFE_VARIANTS) {
  test(`stays quiet on the fixed version: ${name}`, () => {
    const hits = ids(code).filter((id) => !id.startsWith('ai/') && id !== 'crash/unsafe-property-chain');
    assert.deepEqual(hits, []);
  });
}
