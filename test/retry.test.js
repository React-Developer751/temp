import { test } from 'node:test';
import assert from 'node:assert/strict';
import { retry, computeDelay, AbortError, TimeoutError } from '../src/index.js';

const fast = { minTimeout: 1, jitter: false };

function flaky(failures, value = 'ok') {
  let calls = 0;
  const fn = async () => {
    calls++;
    if (calls <= failures) throw new Error(`fail ${calls}`);
    return value;
  };
  return { fn, calls: () => calls };
}

test('returns value on first success without waiting', async () => {
  const { fn, calls } = flaky(0);
  assert.equal(await retry(fn, fast), 'ok');
  assert.equal(calls(), 1);
});

test('retries until success', async () => {
  const { fn, calls } = flaky(2);
  assert.equal(await retry(fn, { ...fast, retries: 3 }), 'ok');
  assert.equal(calls(), 3);
});

test('rejects with last error after retries are exhausted (retries + 1 calls)', async () => {
  const { fn, calls } = flaky(10);
  await assert.rejects(retry(fn, { ...fast, retries: 2 }), { message: 'fail 3' });
  assert.equal(calls(), 3);
});

test('retries: 0 means a single attempt', async () => {
  const { fn, calls } = flaky(1);
  await assert.rejects(retry(fn, { ...fast, retries: 0 }));
  assert.equal(calls(), 1);
});

test('passes attempt number to fn', async () => {
  const seen = [];
  await retry(async (attempt) => {
    seen.push(attempt);
    if (attempt < 3) throw new Error('x');
  }, fast);
  assert.deepEqual(seen, [1, 2, 3]);
});

test('works with sync functions', async () => {
  assert.equal(await retry(() => 42, fast), 42);
});

test('exponential delays: 1s, 2s, 4s without jitter', () => {
  const o = { minTimeout: 1000, factor: 2, jitter: false };
  assert.deepEqual([0, 1, 2].map((i) => computeDelay(i, o)), [1000, 2000, 4000]);
});

test('maxTimeout caps the delay', () => {
  const o = { minTimeout: 1000, factor: 2, jitter: false, maxTimeout: 3000 };
  assert.deepEqual([0, 1, 2, 3].map((i) => computeDelay(i, o)), [1000, 2000, 3000, 3000]);
});

test('equal jitter stays within [base/2, base]', () => {
  const o = { minTimeout: 1000, factor: 2, jitter: true };
  assert.equal(computeDelay(1, o, () => 0), 1000);
  assert.equal(computeDelay(1, o, () => 1), 2000);
  for (let i = 0; i < 200; i++) {
    const d = computeDelay(2, o);
    assert.ok(d >= 2000 && d <= 4000, `delay ${d} out of range`);
  }
});

test('full jitter stays within [0, base]', () => {
  const o = { minTimeout: 1000, factor: 2, jitter: 'full' };
  assert.equal(computeDelay(1, o, () => 0), 0);
  assert.equal(computeDelay(1, o, () => 0.5), 1000);
});

test('actually waits between attempts', async () => {
  const { fn } = flaky(2);
  const start = Date.now();
  await retry(fn, { minTimeout: 30, factor: 2, jitter: false, retries: 2 }); // 30 + 60
  assert.ok(Date.now() - start >= 85);
});

test('AbortError stops retrying and unwraps the original error', async () => {
  let calls = 0;
  const original = new TypeError('bad input');
  await assert.rejects(
    retry(async () => { calls++; throw new AbortError(original); }, fast),
    (err) => err === original,
  );
  assert.equal(calls, 1);
});

test('shouldRetry can veto a retry', async () => {
  let calls = 0;
  await assert.rejects(
    retry(async () => { calls++; throw new Error('4xx'); }, { ...fast, shouldRetry: () => false }),
    { message: '4xx' },
  );
  assert.equal(calls, 1);
});

test('onRetry receives error, failed attempt number and delay', async () => {
  const events = [];
  const { fn } = flaky(2);
  await retry(fn, {
    minTimeout: 1, factor: 2, jitter: false,
    onRetry: (err, attempt, delay) => events.push([err.message, attempt, delay]),
  });
  assert.deepEqual(events, [['fail 1', 1, 1], ['fail 2', 2, 2]]);
});

test('signal aborts a pending wait', async () => {
  const ac = new AbortController();
  const p = retry(() => { throw new Error('x'); }, { minTimeout: 10_000, jitter: false, signal: ac.signal });
  setTimeout(() => ac.abort(new Error('cancelled')), 20);
  const start = Date.now();
  await assert.rejects(p, { message: 'cancelled' });
  assert.ok(Date.now() - start < 1000);
});

test('already-aborted signal never calls fn', async () => {
  const ac = new AbortController();
  ac.abort();
  let calls = 0;
  await assert.rejects(retry(() => { calls++; }, { signal: ac.signal }));
  assert.equal(calls, 0);
});

test('validates options', async () => {
  await assert.rejects(retry(() => 1, { retries: -1 }), TypeError);
  await assert.rejects(retry(() => 1, { factor: 0.5 }), TypeError);
  await assert.rejects(retry(() => 1, { jitter: 'nope' }), TypeError);
  await assert.rejects(retry('nope'), TypeError);
});

test('delay never exceeds the 32-bit timer limit and is never NaN', () => {
  const MAX = 2 ** 31 - 1;
  for (const o of [{ minTimeout: 1000 }, { minTimeout: 0 }, { minTimeout: 1000, jitter: 'full' }]) {
    for (const i of [0, 40, 2000, 1e6]) {
      const d = computeDelay(i, o);
      assert.ok(Number.isFinite(d) && d >= 0 && d <= MAX, `bad delay ${d} for index ${i}`);
    }
  }
});

test('options set to undefined fall back to defaults', async () => {
  assert.equal(await retry(() => 'ok', { retries: undefined, factor: undefined, jitter: undefined }), 'ok');
});

test('retries: Infinity keeps going until success', async () => {
  const { fn, calls } = flaky(5);
  assert.equal(await retry(fn, { ...fast, retries: Infinity }), 'ok');
  assert.equal(calls(), 6);
});

test('abort during fn skips shouldRetry/onRetry and rejects with reason', async () => {
  const ac = new AbortController();
  let hooks = 0;
  await assert.rejects(
    retry(async () => { ac.abort(new Error('stop')); throw new Error('x'); }, {
      ...fast, signal: ac.signal, shouldRetry: () => { hooks++; return true; }, onRetry: () => { hooks++; },
    }),
    { message: 'stop' },
  );
  assert.equal(hooks, 0);
});

test('errors thrown by onRetry/shouldRetry propagate', async () => {
  await assert.rejects(retry(() => { throw new Error('a'); }, { ...fast, onRetry: () => { throw new Error('hook'); } }), { message: 'hook' });
  await assert.rejects(retry(() => { throw new Error('a'); }, { ...fast, shouldRetry: async () => { throw new Error('sr'); } }), { message: 'sr' });
});

test('non-Error rejections are passed through', async () => {
  await assert.rejects(retry(() => Promise.reject('plain'), { ...fast, retries: 1 }), (e) => e === 'plain');
});

test('rejects bad option shapes', async () => {
  await assert.rejects(retry(() => 1, { retries: 1.5 }), TypeError);
  await assert.rejects(retry(() => 1, { shouldRetry: 'x' }), TypeError);
  await assert.rejects(retry(() => 1, { signal: {} }), TypeError);
  await assert.rejects(retry(() => 1, null), TypeError);
});

test('timeout fails a hung attempt with TimeoutError and retries it', async () => {
  let calls = 0;
  const result = await retry(async (attempt, { signal }) => {
    calls++;
    if (attempt === 1) await new Promise((_, rej) => signal.addEventListener('abort', () => rej(signal.reason)));
    return 'recovered';
  }, { ...fast, timeout: 20 });
  assert.equal(result, 'recovered');
  assert.equal(calls, 2);
});

test('timeout works even if fn ignores the signal; exhausted retries throw TimeoutError', async () => {
  await assert.rejects(
    retry(() => new Promise(() => {}), { ...fast, retries: 1, timeout: 10 }),
    (e) => e instanceof TimeoutError && /10ms/.test(e.message),
  );
});

test('late rejection of a timed-out attempt does not cause an unhandled rejection', async () => {
  const unhandled = [];
  const onUnhandled = (e) => unhandled.push(e);
  process.on('unhandledRejection', onUnhandled);
  await assert.rejects(retry(() => new Promise((_, rej) => setTimeout(() => rej(new Error('late')), 30)), { ...fast, retries: 0, timeout: 5 }), TimeoutError);
  await new Promise((r) => setTimeout(r, 60));
  process.off('unhandledRejection', onUnhandled);
  assert.deepEqual(unhandled, []);
});

test('timeout clears its timer on success (no leaked handles)', async () => {
  await retry(() => 'fast', { ...fast, timeout: 60_000 }); // would keep the process alive 60s if leaked
});

test('shouldRetry can decline TimeoutError', async () => {
  await assert.rejects(
    retry(() => new Promise(() => {}), { ...fast, timeout: 5, shouldRetry: (e) => !(e instanceof TimeoutError) }),
    TimeoutError,
  );
});

test('fn receives a signal that aborts when the caller aborts mid-attempt, even if fn ignores it', async () => {
  const ac = new AbortController();
  let seen;
  const p = retry((attempt, { signal }) => { seen = signal; return new Promise(() => {}); }, { signal: ac.signal });
  setTimeout(() => ac.abort(new Error('user cancelled')), 10);
  await assert.rejects(p, { message: 'user cancelled' });
  assert.equal(seen.aborted, true);
});

test('maxRetryTime stops retrying when the next wait would blow the budget', async () => {
  let calls = 0;
  const start = Date.now();
  // waits would be 50ms then 100ms; after attempt 2 (~50ms elapsed) 50 + 100 > 120 => give up
  await assert.rejects(
    retry(async () => { calls++; throw new Error(`fail ${calls}`); },
      { retries: 10, minTimeout: 50, factor: 2, jitter: false, maxRetryTime: 120 }),
    { message: 'fail 2' },
  );
  assert.equal(calls, 2);
  assert.ok(Date.now() - start < 200);
});

test('validates timeout and maxRetryTime', async () => {
  await assert.rejects(retry(() => 1, { timeout: 0 }), TypeError);
  await assert.rejects(retry(() => 1, { timeout: 'x' }), TypeError);
  await assert.rejects(retry(() => 1, { maxRetryTime: -1 }), TypeError);
});

test('package is usable via require() (CommonJS consumers)', async () => {
  const { createRequire } = await import('node:module');
  const cjs = createRequire(import.meta.url)('../src/index.js');
  assert.equal(typeof cjs.retry, 'function');
  assert.equal(await cjs.retry(() => 7, { minTimeout: 1 }), 7);
});
