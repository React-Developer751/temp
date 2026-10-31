import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createUpiPay, memoryStore, parseUpiLink, UpiPayError } from '../src/index.js';

const plans = { monthly: { price: 99, name: 'Monthly' }, yearly: 799 };
const make = (opts = {}) => createUpiPay({ upiId: 'shop@okaxis', name: 'My Shop', plans, ...opts });
const code = (c) => (err) => err instanceof UpiPayError && err.code === c;

test('plans are normalised', () => {
  assert.deepEqual(make().plans(), [
    { price: '99.00', name: 'Monthly', id: 'monthly' },
    { price: '799.00', id: 'yearly', name: 'yearly' },
  ]);
  assert.throws(() => make({ plans: {} }), TypeError);
  assert.throws(() => make({ plans: { x: -5 } }), RangeError);
  assert.throws(() => make({ upiId: 'nope' }), TypeError);
});

test('createOrder: unique amount within 1-99 paise and a matching link', async () => {
  const pay = make();
  const { order, link } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  assert.equal(order.status, 'pending');
  assert.match(order.id, /^[0-9A-Z]{10}$/);
  assert.ok(order.amountPaise > 9900 && order.amountPaise < 10000);
  const parsed = parseUpiLink(link);
  assert.equal(parsed.amount, order.amount);
  assert.equal(parsed.note, `Order ${order.id}`);
  assert.equal(parsed.upiId, 'shop@okaxis');
  assert.match(pay.qrFor(order), /^<svg/);
});

test('99 concurrent orders for one plan all get different amounts', async () => {
  const pay = make();
  const amounts = new Set();
  for (let i = 0; i < 99; i++) amounts.add((await pay.createOrder({ userId: `u${i}`, plan: 'monthly' })).order.amountPaise);
  assert.equal(amounts.size, 99);
  // 100th: all slots busy, still works
  const { order } = await pay.createOrder({ userId: 'x', plan: 'monthly' });
  assert.ok(order.amountPaise > 9900 && order.amountPaise < 10000);
});

test('expired pending orders free their amount; submitted ones keep it', async () => {
  let t = 1_000_000;
  const pay = make({ now: () => t, holdMs: 1000 });
  const first = [];
  for (let i = 0; i < 99; i++) first.push((await pay.createOrder({ userId: 'u', plan: 'monthly' })).order);
  await pay.submitUtr({ orderId: first[0].id, utr: '400000000001' });
  t += 2000;
  const seen = new Set();
  for (let i = 0; i < 98; i++) seen.add((await pay.createOrder({ userId: 'v', plan: 'monthly' })).order.amountPaise);
  assert.equal(seen.size, 98);
  assert.ok(!seen.has(first[0].amountPaise), 'submitted order still holds its amount');
});

test('uniqueAmount: false charges the exact price', async () => {
  const { order } = await make({ uniqueAmount: false }).createOrder({ userId: 1, plan: 'yearly' });
  assert.equal(order.amount, '799.00');
  assert.equal(order.userId, '1');
});

test('happy path: submit UTR -> approve runs onApproved', async () => {
  const granted = [];
  const submitted = [];
  const pay = make({ onApproved: (o) => granted.push(o.userId), onSubmitted: (o) => submitted.push(o.id) });
  const { order } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  const s = await pay.submitUtr({ orderId: order.id, userId: 'u1', utr: '4123 4567 8901' });
  assert.equal(s.status, 'submitted');
  assert.equal(s.utr, '412345678901');
  assert.deepEqual(submitted, [order.id]);
  const a = await pay.approve(order.id, { by: 'admin' });
  assert.equal(a.status, 'approved');
  assert.equal(a.decidedBy, 'admin');
  assert.deepEqual(granted, ['u1']);
  await assert.rejects(pay.approve(order.id), code('BAD_STATE'));
  await assert.rejects(pay.reject(order.id), code('BAD_STATE'));
});

test('submitUtr guards', async () => {
  const pay = make();
  const { order } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  await assert.rejects(pay.submitUtr({ orderId: order.id, userId: 'u1', utr: '123' }), code('INVALID_UTR'));
  await assert.rejects(pay.submitUtr({ orderId: order.id, userId: 'someone-else', utr: '412345678901' }), code('NOT_FOUND'));
  await assert.rejects(pay.submitUtr({ orderId: 'NOPE', userId: 'u1', utr: '412345678901' }), code('NOT_FOUND'));
  await pay.submitUtr({ orderId: order.id, userId: 'u1', utr: '412345678901' });
  await assert.rejects(pay.submitUtr({ orderId: order.id, userId: 'u1', utr: '412345678902' }), code('BAD_STATE'));
});

test('a UTR can be used once; rejecting frees it', async () => {
  const pay = make();
  const a = (await pay.createOrder({ userId: 'u1', plan: 'monthly' })).order;
  const b = (await pay.createOrder({ userId: 'u2', plan: 'monthly' })).order;
  await pay.submitUtr({ orderId: a.id, utr: '412345678901' });
  await assert.rejects(pay.submitUtr({ orderId: b.id, utr: '412345678901' }), code('UTR_USED'));
  assert.equal((await pay.getOrder(b.id)).status, 'pending', 'failed submit leaves the order untouched');
  const r = await pay.reject(a.id, { reason: 'not received' });
  assert.equal(r.status, 'rejected');
  assert.equal(r.utr, undefined);
  assert.equal(r.rejectedUtr, '412345678901');
  assert.equal(r.reason, 'not received');
  assert.equal((await pay.submitUtr({ orderId: b.id, utr: '412345678901' })).status, 'submitted');
});

test('approve straight from pending with a UTR the admin saw in the bank app', async () => {
  const pay = make();
  const { order } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  const a = await pay.approve(order.id, { utr: '499999999999' });
  assert.equal(a.utr, '499999999999');
  await assert.rejects(pay.approve(order.id, { utr: 'x' }), code('INVALID_UTR'));
});

test('if onApproved throws, the approval is rolled back', async () => {
  let fail = true;
  const pay = make({ onApproved: () => { if (fail) throw new Error('db down'); } });
  const { order } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  await pay.submitUtr({ orderId: order.id, utr: '412345678901' });
  await assert.rejects(pay.approve(order.id, { by: 'admin' }), /db down/);
  const back = await pay.getOrder(order.id);
  assert.equal(back.status, 'submitted');
  assert.equal(back.utr, '412345678901');
  assert.equal(back.decidedAt, undefined);
  assert.equal(back.decidedBy, undefined);
  fail = false;
  assert.equal((await pay.approve(order.id)).status, 'approved');

  // rollback of an approve-from-pending also removes the UTR it set
  fail = true;
  const o2 = (await pay.createOrder({ userId: 'u2', plan: 'monthly' })).order;
  await assert.rejects(pay.approve(o2.id, { utr: '411111111111' }));
  assert.equal((await pay.getOrder(o2.id)).utr, undefined);
  const o3 = (await pay.createOrder({ userId: 'u3', plan: 'monthly' })).order;
  fail = false;
  assert.equal((await pay.approve(o3.id, { utr: '411111111111' })).status, 'approved', 'UTR was freed');
});

test('list filters, newest first, and lookup by amount', async () => {
  let t = 0;
  const pay = make({ now: () => ++t });
  const o1 = (await pay.createOrder({ userId: 'u1', plan: 'monthly' })).order;
  const o2 = (await pay.createOrder({ userId: 'u2', plan: 'yearly' })).order;
  await pay.submitUtr({ orderId: o2.id, utr: '412345678901' });
  assert.deepEqual((await pay.list()).map((o) => o.id), [o2.id, o1.id]);
  assert.deepEqual((await pay.list({ status: 'submitted' })).map((o) => o.id), [o2.id]);
  assert.deepEqual((await pay.list({ userId: 'u1' })).map((o) => o.id), [o1.id]);
  assert.deepEqual((await pay.list({ amount: o1.amount })).map((o) => o.id), [o1.id]);
  assert.equal((await pay.list({ limit: 1 })).length, 1);
});

test('store returns copies: mutating a result does not change stored data', async () => {
  const store = memoryStore();
  const pay = make({ store });
  const { order } = await pay.createOrder({ userId: 'u1', plan: 'monthly' });
  order.status = 'approved';
  (await pay.getOrder(order.id)).status = 'approved';
  assert.equal((await pay.getOrder(order.id)).status, 'pending');
});

test('unknown plan / missing user', async () => {
  const pay = make();
  await assert.rejects(pay.createOrder({ userId: 'u', plan: 'lifetime' }), code('INVALID_PLAN'));
  await assert.rejects(pay.createOrder({ userId: 'u', plan: 'toString' }), code('INVALID_PLAN'));
  await assert.rejects(pay.createOrder({ plan: 'monthly' }), code('UNAUTHORIZED'));
});
