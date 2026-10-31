import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parse, validate } from '../src/index.js';

const utc = { timeZone: 'UTC' };
const iso = (d) => d.toISOString();
const at = (...a) => Date.UTC(...a);

test('daily midnight', () => {
  assert.equal(iso(parse('0 0 * * *', utc).next(at(2026, 0, 1, 10))), '2026-01-02T00:00:00.000Z');
});

test('next is strictly after `from`, and ignores milliseconds', () => {
  const c = parse('0 0 * * *', utc);
  assert.equal(iso(c.next(at(2026, 0, 2))), '2026-01-03T00:00:00.000Z');
  assert.equal(iso(c.next(at(2026, 0, 1, 23, 59, 59, 999))), '2026-01-02T00:00:00.000Z');
});

test('steps, lists and ranges', () => {
  assert.deepEqual(
    parse('*/15 9-10 * * *', utc).nextRuns(5, at(2026, 0, 1, 9, 50)).map(iso),
    ['2026-01-01T10:00:00.000Z', '2026-01-01T10:15:00.000Z', '2026-01-01T10:30:00.000Z',
      '2026-01-01T10:45:00.000Z', '2026-01-02T09:00:00.000Z'],
  );
  assert.deepEqual(parse('5,10 0 1 1 *', utc).nextRuns(2, at(2026, 0, 1)).map(iso),
    ['2026-01-01T00:05:00.000Z', '2026-01-01T00:10:00.000Z']);
  assert.equal(iso(parse('10/20 * * * *', utc).next(at(2026, 0, 1, 0, 11))), '2026-01-01T00:30:00.000Z');
});

test('six fields add seconds', () => {
  assert.deepEqual(parse('*/20 * * * * *', utc).nextRuns(3, at(2026, 0, 1)).map(iso),
    ['2026-01-01T00:00:20.000Z', '2026-01-01T00:00:40.000Z', '2026-01-01T00:01:00.000Z']);
});

test('names, case-insensitive, and 7 = Sunday', () => {
  // 2026-01-05 is a Monday
  assert.equal(iso(parse('0 9 * * mon-fri', utc).next(at(2026, 0, 3))), '2026-01-05T09:00:00.000Z');
  assert.equal(iso(parse('0 0 1 FEB,mar *', utc).next(at(2026, 0, 1))), '2026-02-01T00:00:00.000Z');
  assert.equal(iso(parse('0 0 * * 7', utc).next(at(2026, 0, 5))), '2026-01-11T00:00:00.000Z');
  assert.equal(iso(parse('0 0 * * 0', utc).next(at(2026, 0, 5))), '2026-01-11T00:00:00.000Z');
});

test('macros', () => {
  assert.equal(iso(parse('@hourly', utc).next(at(2026, 0, 1, 5, 30))), '2026-01-01T06:00:00.000Z');
  assert.equal(iso(parse('@weekly', utc).next(at(2026, 0, 1))), '2026-01-04T00:00:00.000Z');
  assert.equal(iso(parse('@monthly', utc).next(at(2026, 0, 15))), '2026-02-01T00:00:00.000Z');
  assert.equal(iso(parse('@yearly', utc).next(at(2026, 0, 15))), '2027-01-01T00:00:00.000Z');
  assert.equal(iso(parse('@DAILY', utc).next(at(2026, 0, 15))), '2026-01-16T00:00:00.000Z');
});

test('day-of-month OR day-of-week when both are restricted', () => {
  // the 13th OR any Friday; 2026-01-02 is a Friday
  assert.deepEqual(parse('0 0 13 * 5', utc).nextRuns(3, at(2026, 0, 1)).map(iso),
    ['2026-01-02T00:00:00.000Z', '2026-01-09T00:00:00.000Z', '2026-01-13T00:00:00.000Z']);
});

test('starred day field means AND', () => {
  // every other day-of-month, but only Mondays
  const runs = parse('0 0 */2 * 1', utc).nextRuns(3, at(2026, 0, 1));
  for (const d of runs) {
    assert.equal(d.getUTCDay(), 1);
    assert.equal(d.getUTCDate() % 2, 1);
  }
});

test('leap day skips ahead years, including a skipped leap year', () => {
  assert.equal(iso(parse('0 0 29 2 *', utc).next(at(2026, 0, 1))), '2028-02-29T00:00:00.000Z');
  assert.equal(iso(parse('0 0 29 2 *', utc).next(at(2096, 2, 1))), '2104-02-29T00:00:00.000Z');
});

test('31st skips short months', () => {
  assert.deepEqual(parse('0 0 31 * *', utc).nextRuns(3, at(2026, 0, 1)).map(iso),
    ['2026-01-31T00:00:00.000Z', '2026-03-31T00:00:00.000Z', '2026-05-31T00:00:00.000Z']);
});

test('year rollover', () => {
  assert.equal(iso(parse('59 23 31 12 *', utc).next(at(2026, 11, 31, 23, 59))), '2027-12-31T23:59:00.000Z');
});

test('matches()', () => {
  const c = parse('30 8 * * 1-5', utc);
  assert.ok(c.matches(at(2026, 0, 5, 8, 30, 0, 750)));
  assert.ok(!c.matches(at(2026, 0, 5, 8, 31)));
  assert.ok(!c.matches(at(2026, 0, 3, 8, 30))); // Saturday
});

test('msUntilNext', () => {
  assert.equal(parse('0 0 * * *', utc).msUntilNext(at(2026, 0, 1, 23)), 3_600_000);
});

test('time zones with a fixed offset', () => {
  // Asia/Kolkata is UTC+05:30
  assert.equal(iso(parse('0 9 * * *', { timeZone: 'Asia/Kolkata' }).next(at(2026, 0, 1))), '2026-01-01T03:30:00.000Z');
  assert.equal(parse('0 0 * * *', { timeZone: 'Asia/Kolkata' }).timeZone, 'Asia/Kolkata');
});

test('DST: midnight stays local across spring-forward', () => {
  const c = parse('0 0 * * *', { timeZone: 'America/New_York' });
  assert.deepEqual(c.nextRuns(2, at(2026, 2, 7, 12)).map(iso),
    ['2026-03-08T05:00:00.000Z', '2026-03-09T04:00:00.000Z']);
});

test('DST: a time inside the spring-forward gap runs when the clocks jump', () => {
  const c = parse('30 2 * * *', { timeZone: 'America/New_York' });
  assert.deepEqual(c.nextRuns(2, at(2026, 2, 7, 12)).map(iso),
    ['2026-03-08T07:00:00.000Z', '2026-03-09T06:30:00.000Z']);
});

test('DST: gap does not duplicate every-minute jobs', () => {
  const c = parse('* * * * *', { timeZone: 'America/New_York' });
  const runs = c.nextRuns(4, at(2026, 2, 8, 6, 58)).map(iso); // 01:58 EST
  assert.deepEqual(runs, ['2026-03-08T06:59:00.000Z', '2026-03-08T07:00:00.000Z',
    '2026-03-08T07:01:00.000Z', '2026-03-08T07:02:00.000Z']);
});

test('DST: a repeated hour fires once (first occurrence)', () => {
  const c = parse('30 1 * * *', { timeZone: 'America/New_York' });
  assert.deepEqual(c.nextRuns(2, at(2026, 9, 31, 12)).map(iso),
    ['2026-11-01T05:30:00.000Z', '2026-11-02T06:30:00.000Z']);
});

test('southern hemisphere and half-hour DST (Lord Howe)', () => {
  const c = parse('0 12 * * *', { timeZone: 'Australia/Lord_Howe' });
  // January: UTC+11, July: UTC+10:30
  assert.equal(iso(c.next(at(2026, 0, 1))), '2026-01-01T01:00:00.000Z');
  assert.equal(iso(c.next(at(2026, 6, 1))), '2026-07-01T01:30:00.000Z');
});

test('rejects invalid expressions with SyntaxError', () => {
  for (const bad of ['', '* * * *', '* * * * * * *', '60 * * * *', '* 24 * * *', '* * 0 * *', '* * 32 * *',
    '* * * 13 *', '* * * * 8', '5-1 * * * *', '*/0 * * * *', '*/x * * * *', '1,,2 * * * *', '? * * * *',
    '* * * foo *', '@sometimes', '1/2/3 * * * *', '1-2-3 * * * *']) {
    assert.throws(() => parse(bad, utc), SyntaxError, `should reject "${bad}"`);
  }
  assert.throws(() => parse(42), TypeError);
});

test('rejects expressions that can never match', () => {
  assert.throws(() => parse('0 0 30 2 *', utc), RangeError);
  assert.throws(() => parse('0 0 31 4,6,9,11 *', utc), RangeError);
});

test('rejects unknown time zones', () => {
  assert.throws(() => parse('* * * * *', { timeZone: 'Mars/Olympus' }), RangeError);
  assert.throws(() => parse('* * * * *', { timeZone: '' }), TypeError);
});

test('validate()', () => {
  assert.equal(validate('0 0 * * *'), true);
  assert.equal(validate('nope'), false);
});

test('next() rejects bad dates', () => {
  assert.throws(() => parse('* * * * *', utc).next(NaN), TypeError);
  assert.throws(() => parse('* * * * *', utc).next(new Date('x')), TypeError);
});

test('dates near the Date limit throw instead of hanging', () => {
  const c = parse('0 0 1 1 *', utc);
  assert.throws(() => c.next(8.64e15 - 1000), RangeError);
  assert.throws(() => c.next(-8.64e15), RangeError);
  assert.throws(() => c.matches(8.64e15 + 1), RangeError);
});

test('dates before 1970 work', () => {
  assert.equal(iso(parse('0 0 1 1 *', utc).next(at(1900, 5, 1))), '1901-01-01T00:00:00.000Z');
});

test('UTC aliases are accepted and keep the given name', () => {
  for (const tz of ['utc', 'Etc/UTC', 'UTC']) {
    const c = parse('0 12 * * *', { timeZone: tz });
    assert.equal(c.timeZone, tz);
    assert.equal(iso(c.next(at(2026, 0, 1))), '2026-01-01T12:00:00.000Z');
  }
});

test('a skipped calendar day (Samoa 2011-12-30) still runs, at the jump', () => {
  const c = parse('0 12 30 12 *', { timeZone: 'Pacific/Apia' });
  assert.equal(iso(c.next(at(2011, 11, 1))), '2011-12-30T10:00:00.000Z');
});

test('whitespace variants, ? wildcards and stepped weekday ranges', () => {
  assert.equal(parse('  0\t0  *\n* *  ', utc).source.trim().length > 0, true);
  assert.equal(iso(parse('0 0 ? * ?', utc).next(0)), '1970-01-02T00:00:00.000Z');
  assert.deepEqual(parse('0 0 * * mon-fri/2', utc).nextRuns(3, at(2026, 0, 1)).map((d) => d.getUTCDay()), [5, 1, 3]);
});

test('constructor validates options', () => {
  assert.throws(() => parse('* * * * *', null), TypeError);
});

test('matches() is wall-clock based: both passes of a repeated hour match', () => {
  const c = parse('30 1 * * *', { timeZone: 'America/New_York' });
  assert.ok(c.matches(at(2026, 10, 1, 5, 30)) && c.matches(at(2026, 10, 1, 6, 30)));
});

test('performance: 20k runs per zone in reasonable time', () => {
  for (const tz of ['UTC', 'America/New_York']) {
    const t0 = performance.now();
    const runs = parse('* * * * *', { timeZone: tz }).nextRuns(20_000, at(2026, 0, 1));
    assert.equal(runs.length, 20_000);
    assert.ok(performance.now() - t0 < 5000, `${tz} too slow: ${performance.now() - t0}ms`);
  }
});

test('DST fall-back: wildcard-hour jobs run in both passes of the repeated hour (Vixie)', () => {
  const ny = (e, from, n) => parse(e, { timeZone: 'America/New_York' }).nextRuns(n, from).map((d) => d.toISOString().slice(11, 16));
  // 2026-11-01: 01:00-01:59 EDT (05:xxZ) then again as EST (06:xxZ)
  assert.deepEqual(ny('*/30 * * * *', Date.UTC(2026, 10, 1, 4), 6), ['04:30', '05:00', '05:30', '06:00', '06:30', '07:00']);
  // starting inside the first pass
  assert.deepEqual(ny('0,30 * * * *', Date.UTC(2026, 10, 1, 5, 40), 3), ['06:00', '06:30', '07:00']);
  // fixed hour: once
  assert.deepEqual(ny('*/15 1 * * *', Date.UTC(2026, 10, 1, 4), 5), ['05:00', '05:15', '05:30', '05:45', '06:00']);
  assert.equal(ny('*/15 1 * * *', Date.UTC(2026, 10, 1, 4), 5)[4], '06:00'); // next day's 01:00 EST
});

test('day-of-week 7 with a step means Sunday; empty sets are rejected', () => {
  const days = (e) => parse(e, { timeZone: 'UTC' }).nextRuns(3, Date.UTC(2026, 0, 4)).map((d) => d.getUTCDay());
  assert.deepEqual(days('0 0 * * 7/1'), [0, 0, 0]);
  assert.deepEqual(days('0 0 * * 1/2'), [1, 3, 5]);
});
