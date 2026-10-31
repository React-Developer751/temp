import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { createUpiPay, upiHandler } from '../src/index.js';
import { createUpiClient, canOpenUpiApp, UpiClientError } from '../src/client.js';

// Fake auth: the "x-user" header is the user id; user "admin" is the admin.
const getUser = (req) => req.headers['x-user'] || null;
const isAdmin = (req) => req.headers['x-user'] === 'admin';

async function start(handler) {
  const server = http.createServer(handler);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  return { base, close: () => new Promise((r) => server.close(r)) };
}

const clientFor = (base, user) => createUpiClient({ baseUrl: `${base}/api/upi`, headers: user ? { 'x-user': user } : {} });

test('full flow over HTTP with the browser client', async (t) => {
  const premium = new Set();
  const pay = createUpiPay({
    upiId: 'shop@okaxis', name: 'My Shop', plans: { monthly: { price: 99 } },
    onApproved: (o) => premium.add(o.userId),
  });
  const srv = await start(upiHandler(pay, { getUser, isAdmin, basePath: '/api/upi' }));
  t.after(srv.close);

  const user = clientFor(srv.base, 'u1');
  const admin = clientFor(srv.base, 'admin');

  assert.deepEqual(await clientFor(srv.base).plans(), [{ price: '99.00', id: 'monthly', name: 'monthly' }]);

  const { order, link, qrSvg } = await user.createOrder('monthly');
  assert.equal(order.status, 'pending');
  assert.match(link, /^upi:\/\/pay\?pa=shop@okaxis&pn=My%20Shop&am=99\.\d\d&cu=INR&tn=Order%20/);
  assert.match(qrSvg, /^<svg/);

  assert.equal((await user.getOrder(order.id)).order.id, order.id);
  assert.equal((await user.myOrders()).length, 1);

  await assert.rejects(user.submitUtr(order.id, '12'), (e) => e instanceof UpiClientError && e.status === 400 && e.code === 'INVALID_UTR');
  const s = await user.submitUtr(order.id, '412345678901');
  assert.equal(s.status, 'submitted');

  // a submitted order no longer returns the QR
  assert.equal((await user.getOrder(order.id)).qrSvg, undefined);

  await assert.rejects(user.admin.list(), (e) => e.status === 403 && e.code === 'FORBIDDEN');
  const pending = await admin.admin.list({ status: 'submitted' });
  assert.deepEqual(pending.map((o) => o.id), [order.id]);
  assert.deepEqual((await admin.admin.list({ amount: order.amount })).map((o) => o.id), [order.id]);

  const approved = await admin.admin.approve(order.id);
  assert.equal(approved.status, 'approved');
  assert.equal(approved.decidedBy, 'admin');
  assert.ok(premium.has('u1'));
  await assert.rejects(admin.admin.approve(order.id), (e) => e.status === 409 && e.code === 'BAD_STATE');
});

test('auth, ownership, reject and errors', async (t) => {
  const pay = createUpiPay({ upiId: 'shop@okaxis', name: 'S', plans: { p: 10 } });
  const srv = await start(upiHandler(pay, { getUser, isAdmin, basePath: '/api/upi' }));
  t.after(srv.close);
  const anon = clientFor(srv.base);
  const u1 = clientFor(srv.base, 'u1');
  const u2 = clientFor(srv.base, 'u2');
  const admin = clientFor(srv.base, 'admin');

  await assert.rejects(anon.createOrder('p'), (e) => e.status === 401 && e.code === 'UNAUTHORIZED');
  await assert.rejects(u1.createOrder('nope'), (e) => e.status === 400 && e.code === 'INVALID_PLAN');
  const { order } = await u1.createOrder('p');
  await assert.rejects(u2.getOrder(order.id), (e) => e.status === 404);
  await assert.rejects(u2.submitUtr(order.id, '412345678901'), (e) => e.status === 404);
  assert.equal((await admin.getOrder(order.id)).order.id, order.id, 'admin can view any order');

  await u1.submitUtr(order.id, '412345678901');
  const other = (await u2.createOrder('p')).order;
  await assert.rejects(u2.submitUtr(other.id, '412345678901'), (e) => e.status === 409 && e.code === 'UTR_USED');

  const r = await admin.admin.reject(order.id, 'payment not received');
  assert.equal(r.status, 'rejected');
  assert.equal(r.reason, 'payment not received');
  assert.equal((await u2.submitUtr(other.id, '412345678901')).status, 'submitted');

  const res = await fetch(`${srv.base}/api/upi/orders`, { method: 'POST', headers: { 'x-user': 'u1' }, body: '{bad json' });
  assert.equal(res.status, 400);
  assert.equal((await res.json()).error, 'BAD_REQUEST');
  const big = await fetch(`${srv.base}/api/upi/orders`, { method: 'POST', headers: { 'x-user': 'u1' }, body: 'x'.repeat(20000) });
  assert.equal(big.status, 400);
  const amountBad = await fetch(`${srv.base}/api/upi/admin/orders?amount=abc`, { headers: { 'x-user': 'admin' } });
  assert.equal(amountBad.status, 400);
  assert.equal((await fetch(`${srv.base}/api/upi/nothing`)).status, 404);
  assert.equal((await fetch(`${srv.base}/elsewhere`)).status, 404);
});

test('express-style mounting: pre-parsed body, stripped url, next() for unknown routes', async () => {
  const pay = createUpiPay({ upiId: 'shop@okaxis', name: 'S', plans: { p: 10 } });
  const handle = upiHandler(pay, { getUser: (req) => req.user, isAdmin: () => false });
  const res = {
    headers: {}, statusCode: 0, body: '',
    setHeader(k, v) { this.headers[k] = v; }, end(b) { this.body = b; },
  };
  const req = { method: 'POST', url: '/orders', headers: {}, user: { _id: 'mongo-id-1' }, body: { plan: 'p' } };
  await handle(req, res);
  assert.equal(res.statusCode, 201);
  assert.equal(JSON.parse(res.body).order.userId, 'mongo-id-1');

  let nextCalled = false;
  await handle({ method: 'GET', url: '/unknown', headers: {} }, res, () => { nextCalled = true; });
  assert.ok(nextCalled);
});

test('unexpected errors become 500 without leaking details', async (t) => {
  const pay = createUpiPay({ upiId: 'shop@okaxis', name: 'S', plans: { p: 10 } });
  pay.store.list = async () => { throw new Error('secret db detail'); };
  const seen = [];
  const srv = await start(upiHandler(pay, { getUser, isAdmin, basePath: '/api/upi', onError: (e) => seen.push(e.message) }));
  t.after(srv.close);
  const res = await fetch(`${srv.base}/api/upi/orders`, { headers: { 'x-user': 'u1' } });
  assert.equal(res.status, 500);
  assert.doesNotMatch(await res.text(), /secret/);
  assert.deepEqual(seen, ['secret db detail']);
});

test('handler option checks and device detection', () => {
  const pay = createUpiPay({ upiId: 'shop@okaxis', name: 'S', plans: { p: 10 } });
  assert.throws(() => upiHandler(pay, { isAdmin }), TypeError);
  assert.throws(() => upiHandler(pay, { getUser }), TypeError);
  assert.ok(canOpenUpiApp('Mozilla/5.0 (Linux; Android 14) Chrome/120'));
  assert.ok(canOpenUpiApp('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)'));
  assert.ok(!canOpenUpiApp('Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0)'));
});
