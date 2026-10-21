import { test } from 'node:test';
import assert from 'node:assert/strict';
import { has, scan } from './helpers.js';

const EMPTY = 'crash/empty-catch';
const CHAIN = 'crash/unsafe-property-chain';
const PARSE = 'crash/unguarded-json-parse';

test('empty catch blocks of every shape', () => {
  for (const code of [
    'try { run(); } catch (e) {}',
    'try { run(); } catch (e) { }',
    'try { run(); } catch {}',
    'try { run(); } catch (error) {\n\n}',
    'try { run(); } catch (e) { /* TODO */ }',
  ]) assert.ok(has(code, EMPTY), code);
});

test('empty promise .catch() is its own, medium rule', () => {
  for (const code of ['p.catch(() => {});', 'p.catch((e) => { });', 'p.catch(e => {});', 'p.catch(function () {});', 'p.catch(async () => {});']) {
    const f = scan(code).find((x) => x.ruleId === 'crash/empty-promise-catch');
    assert.ok(f, code);
    assert.equal(f.severity, 'medium');
    assert.ok(!has(code, EMPTY), 'the block rule does not fire on the promise form');
  }
  assert.ok(!has('p.catch(() => { /* best effort */ });', 'crash/empty-promise-catch'));
  assert.ok(!has('p.catch(() => log("x"));', 'crash/empty-promise-catch'));
});

test('catch blocks that do something, or are documented, are fine', () => {
  for (const code of [
    'try { run(); } catch (e) { log(e); }',
    'try { run(); } catch (e) { throw e; }',
    'try { run(); } catch { /* ignore: file may already be gone */ }',
    'try { run(); } catch (e) { // intentionally ignored\n}',
    'p.catch(() => log("x"));',
    'p.catch(handle);',
    'p.catch(() => {}); // pure-guard-ignore crash/empty-promise-catch',
    'const s = "catch (e) {}";',
    '// catch (e) {}',
  ]) assert.ok(!has(code, EMPTY), code);
});

test('unsafe property chains on runtime data', () => {
  assert.ok(has('const user = await getUser();\nconsole.log(user.profile.name);', CHAIN));
  assert.ok(has('function f(user) { return user.profile.name; }', CHAIN));
  assert.ok(has('const { data } = await axios.get(u);\nuse(data.items.length);', CHAIN));
  assert.ok(has('const j = JSON.parse(s);\nuse(j.a.b);', CHAIN));
  assert.ok(has('use(response.data.user.id);', CHAIN));
  assert.ok(has('use(user?.profile.name);', CHAIN), 'optional only at the first step still throws if profile is null');
  assert.ok(has('use(req.body.user.name);', CHAIN));
});

test('chain finding suggests the optional-chaining fix', () => {
  const f = scan('function f(user) { return user.profile.address.city; }').find((x) => x.ruleId === CHAIN);
  assert.match(f.fix, /user\?\.profile\?\.address\?\.city/);
});

test('chains that are safe or unknowable are not flagged', () => {
  for (const code of [
    'use(user?.profile?.name);',
    'use(user.name);',
    'use(req.body.name);',
    'use(req.query.id);',
    'const config = { a: { b: { c: 1 } } };\nuse(config.a.b.c);',
    'import fs from "node:fs";\nuse(fs.promises.readFile);',
    'const path = require("node:path");\nuse(path.posix.join);',
    'use(this.state.user.name);',
    'use(process.env.HOME.length);',
    'use(Math.PI.toFixed(2));',
    'use(module.exports.a.b);',
    'use(MAX_LIMITS.http.port);',
    'if (user && user.profile) use(user.profile.name);',
    'const n = user && user.profile && user.profile.name;',
    'if (user.profile) {\n  use(user.profile.name);\n}',
    'function f(opts) { return opts.a.b; }',
  ]) assert.ok(!has(code, CHAIN), code);
});

test('chain rule reports once per root per line', () => {
  const found = scan('function f(user) { return [user.a.b, user.c.d, user.e.f]; }').filter((x) => x.ruleId === CHAIN);
  assert.equal(found.length, 1);
});

test('JSON.parse outside try/catch', () => {
  assert.ok(has('const cfg = JSON.parse(text);', PARSE));
  assert.ok(has('function f(s) { return JSON.parse(s); }', PARSE));
  assert.ok(has('try { a(); } catch (e) { log(e); }\nconst x = JSON.parse(s);', PARSE), 'a try earlier in the file does not cover it');
});

test('JSON.parse inside try, or on a literal, is fine', () => {
  assert.ok(!has('try {\n  const cfg = JSON.parse(text);\n} catch (e) {\n  log(e);\n}', PARSE));
  assert.ok(!has('try { if (x) { JSON.parse(text); } } catch (e) { log(e); }', PARSE));
  assert.ok(!has('const a = JSON.parse("{}");', PARSE));
  assert.ok(!has('const s = "JSON.parse(text)";', PARSE));
});
