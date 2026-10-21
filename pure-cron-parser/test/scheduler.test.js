import { test, mock } from 'node:test';
import assert from 'node:assert/strict';
import { schedule, parse } from '../src/index.js';

const DAY = 86_400_000;
const start = (ms) => mock.timers.enable({ apis: ['setTimeout', 'Date'], now: ms });

test('fires at the exact scheduled time and re-arms for the next day', () => {
  start(Date.UTC(2026, 0, 1, 23, 59, 0));
  const calls = [];
  const task = schedule('0 0 * * *', (d) => calls.push(d.toISOString()), { timeZone: 'UTC' });
  assert.equal(task.nextRun().toISOString(), '2026-01-02T00:00:00.000Z');

  mock.timers.tick(59_999);
  assert.equal(calls.length, 0);
  mock.timers.tick(1);
  assert.deepEqual(calls, ['2026-01-02T00:00:00.000Z']);
  mock.timers.tick(DAY);
  assert.deepEqual(calls, ['2026-01-02T00:00:00.000Z', '2026-01-03T00:00:00.000Z']);
  task.stop();
  mock.timers.reset();
});

test('waits longer than the 32-bit timer limit by chaining timers', () => {
  start(Date.UTC(2026, 0, 1, 0, 0, 1));
  let n = 0;
  const task = schedule('@yearly', () => n++, { timeZone: 'UTC' }); // ~364 days away
  mock.timers.tick(363 * DAY);
  assert.equal(n, 0);
  mock.timers.tick(2 * DAY);
  assert.equal(n, 1);
  task.stop();
  mock.timers.reset();
});

test('stop() cancels, start() resumes', () => {
  start(Date.UTC(2026, 0, 1));
  let n = 0;
  const task = schedule('* * * * *', () => n++, { timeZone: 'UTC' });
  mock.timers.tick(60_000);
  assert.equal(n, 1);
  task.stop();
  assert.equal(task.running, false);
  assert.equal(task.nextRun(), null);
  mock.timers.tick(5 * 60_000);
  assert.equal(n, 1);
  task.start();
  mock.timers.tick(60_000);
  assert.equal(n, 2);
  task.stop();
  mock.timers.reset();
});

test('a callback may stop its own task', () => {
  start(Date.UTC(2026, 0, 1));
  let n = 0;
  const task = schedule('* * * * *', () => { n++; task.stop(); }, { timeZone: 'UTC' });
  mock.timers.tick(10 * 60_000);
  assert.equal(n, 1);
  mock.timers.reset();
});

test('abort signal stops the task', () => {
  start(Date.UTC(2026, 0, 1));
  const ac = new AbortController();
  let n = 0;
  schedule('* * * * *', () => n++, { timeZone: 'UTC', signal: ac.signal });
  ac.abort();
  mock.timers.tick(5 * 60_000);
  assert.equal(n, 0);
  mock.timers.reset();
});

test('runOnInit calls the callback immediately', () => {
  start(Date.UTC(2026, 0, 1));
  let n = 0;
  const task = schedule('0 0 1 1 *', () => n++, { timeZone: 'UTC', runOnInit: true });
  assert.equal(n, 1);
  task.stop();
  mock.timers.reset();
});

test('errors (sync and async) go to onError and do not stop the schedule', async () => {
  start(Date.UTC(2026, 0, 1));
  const errors = [];
  let n = 0;
  const task = schedule('* * * * *', () => {
    n++;
    if (n === 1) throw new Error('sync');
    return Promise.reject(new Error('async'));
  }, { timeZone: 'UTC', onError: (e) => errors.push(e.message), overlap: true });
  mock.timers.tick(60_000);
  mock.timers.tick(60_000);
  await Promise.resolve();
  await Promise.resolve();
  assert.deepEqual(errors, ['sync', 'async']);
  assert.equal(task.running, true);
  task.stop();
  mock.timers.reset();
});

test('overlapping runs are skipped by default, allowed with overlap: true', async () => {
  start(Date.UTC(2026, 0, 1));
  let release;
  let started = 0;
  const skipped = [];
  const task = schedule('* * * * *', () => {
    started++;
    return new Promise((r) => { release = r; });
  }, { timeZone: 'UTC', onSkip: (d) => skipped.push(d.toISOString()) });
  mock.timers.tick(60_000);
  mock.timers.tick(60_000);
  assert.equal(started, 1);
  assert.deepEqual(skipped, ['2026-01-01T00:02:00.000Z']);
  release();
  await Promise.resolve();
  await Promise.resolve();
  mock.timers.tick(60_000);
  assert.equal(started, 2);
  task.stop();

  let overlapping = 0;
  const t2 = schedule('* * * * *', () => { overlapping++; return new Promise(() => {}); }, { timeZone: 'UTC', overlap: true });
  mock.timers.tick(60_000);
  mock.timers.tick(60_000);
  assert.equal(overlapping, 2);
  t2.stop();
  mock.timers.reset();
});

test('accepts a parsed CronExpression', () => {
  start(Date.UTC(2026, 0, 1));
  let n = 0;
  const task = schedule(parse('* * * * *', { timeZone: 'UTC' }), () => n++);
  mock.timers.tick(60_000);
  assert.equal(n, 1);
  task.stop();
  mock.timers.reset();
});

test('validates arguments', () => {
  assert.throws(() => schedule('* * * * *', 'nope'), TypeError);
  assert.throws(() => schedule('* * * * *', () => {}, { onError: 1 }), TypeError);
  assert.throws(() => schedule('bad', () => {}), SyntaxError);
});

test('real timers: 6-field expression fires roughly every second and stops cleanly', async () => {
  const times = [];
  const task = schedule('* * * * * *', () => times.push(Date.now()), { unref: false });
  await new Promise((r) => setTimeout(r, 2300));
  task.stop();
  assert.ok(times.length >= 2 && times.length <= 3, `got ${times.length} runs`);
  assert.ok(times.every((t) => t % 1000 < 100), 'runs should land on second boundaries');
});

test('maxWaitMs splits long waits into clock-checking chunks', () => {
  start(Date.UTC(2026, 0, 1, 0, 0, 1));
  let n = 0;
  const task = schedule('0 0 2 1 *', () => n++, { timeZone: 'UTC', maxWaitMs: 3_600_000 });
  // Simulate a clock that jumps forward 2 days while a chunk is pending (e.g. VM resume).
  mock.timers.tick(3_600_000);
  mock.timers.setTime(Date.UTC(2026, 0, 2, 0, 0, 0) + 1);
  mock.timers.tick(3_600_000);
  assert.equal(n, 1);
  task.stop();
  mock.timers.reset();
});

test('whenIdle resolves after in-flight async work finishes', async () => {
  start(Date.UTC(2026, 0, 1));
  let finish;
  const task = schedule('* * * * *', () => new Promise((r) => { finish = r; }), { timeZone: 'UTC' });
  mock.timers.tick(60_000);
  task.stop();
  let idle = false;
  const p = task.whenIdle().then(() => { idle = true; });
  await Promise.resolve();
  assert.equal(idle, false);
  finish();
  await p;
  assert.equal(idle, true);
  await task.whenIdle();
  mock.timers.reset();
});

test('start() after the signal aborted does nothing', () => {
  const ac = new AbortController();
  ac.abort();
  const task = schedule('* * * * *', () => {}, { signal: ac.signal });
  assert.equal(task.running, false);
  assert.equal(task.start().running, false);
});

test('validates maxWaitMs and signal', () => {
  assert.throws(() => schedule('* * * * *', () => {}, { maxWaitMs: 5 }), TypeError);
  assert.throws(() => schedule('* * * * *', () => {}, { maxWaitMs: 2 ** 31 }), TypeError);
  assert.throws(() => schedule('* * * * *', () => {}, { signal: {} }), TypeError);
  assert.throws(() => schedule('* * * * *', () => {}, null), TypeError);
});
