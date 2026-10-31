import { test } from 'node:test';
import assert from 'node:assert/strict';
import { upiLink, parseUpiLink, isValidVpa, isValidUtr, toPaise, formatPaise } from '../src/index.js';

test('builds a standard upi://pay link', () => {
  assert.equal(
    upiLink({ upiId: 'shop@okaxis', name: 'My Shop', amount: 99.07, note: 'Order K3J9' }),
    'upi://pay?pa=shop@okaxis&pn=My%20Shop&am=99.07&cu=INR&tn=Order%20K3J9',
  );
  assert.equal(upiLink({ upiId: 'a.b-c_d@ybl', name: 'X' }), 'upi://pay?pa=a.b-c_d@ybl&pn=X&cu=INR');
  assert.equal(upiLink({ upiId: 'x@paytm', name: 'X', amount: '5' }), 'upi://pay?pa=x@paytm&pn=X&am=5.00&cu=INR');
});

test('merchant-only params', () => {
  const link = upiLink({ upiId: 'shop@icici', name: 'S', amount: 1, ref: 'INV-1', merchantCode: 5411 });
  assert.match(link, /&tr=INV-1&mc=5411$/);
  assert.throws(() => upiLink({ upiId: 'shop@icici', name: 'S', merchantCode: 'abc' }), TypeError);
});

test('note and name are sanitised and capped', () => {
  const link = upiLink({ upiId: 'a@ybl', name: 'Rāj & Sons<script>', note: `${'n'.repeat(80)}&am=1` });
  const p = parseUpiLink(link);
  assert.equal(p.name, 'Rāj Sons script');
  assert.equal(p.note.length, 50);
  assert.equal(p.amount, undefined);
});

test('round trip through parseUpiLink', () => {
  const p = parseUpiLink(upiLink({ upiId: 'me@okhdfcbank', name: 'नमस्ते Store', amount: '1200.5', note: 'Premium #12' }));
  assert.deepEqual(p, { upiId: 'me@okhdfcbank', name: 'नमस्ते Store', currency: 'INR', amount: '1200.50', note: 'Premium #12' });
  assert.throws(() => parseUpiLink('https://x'), TypeError);
});

test('validates UPI IDs', () => {
  for (const ok of ['name@okicici', '9876543210@ybl', 'a.b@paytm', 'shop-1@axl']) assert.ok(isValidVpa(ok), ok);
  for (const bad of ['', 'noat', '@ybl', 'a@', 'a b@ybl', 'a@1bank', 'a@@ybl', 5, null]) assert.ok(!isValidVpa(bad), String(bad));
  assert.throws(() => upiLink({ upiId: 'bad', name: 'X' }), TypeError);
  assert.throws(() => upiLink({ upiId: 'a@ybl', name: '' }), TypeError);
});

test('validates UTRs', () => {
  assert.ok(isValidUtr('412345678901'));
  assert.ok(isValidUtr('4123 4567 8901'));
  for (const bad of ['41234567890', '4123456789012', 'abcdefghijkl', '', 412345678901]) assert.ok(!isValidUtr(bad), String(bad));
});

test('amounts are exact paise, never floats', () => {
  assert.equal(toPaise(99), 9900);
  assert.equal(toPaise(99.07), 9907);
  assert.equal(toPaise('0.1'), 10);
  assert.equal(toPaise('1200.50'), 120050);
  assert.equal(formatPaise(9907), '99.07');
  assert.equal(formatPaise(5), '0.05');
  for (const bad of [0, -1, 1.234, '1e3', 'abc', NaN, Infinity, 0.1 + 0.2, '', null]) {
    assert.throws(() => toPaise(bad), RangeError, String(bad));
  }
});
