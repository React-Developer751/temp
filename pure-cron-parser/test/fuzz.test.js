// Differential fuzz: random expressions are generated from explicit value sets, so the oracle below
// never touches the library's parser. next() must equal a minute-by-minute brute-force scan.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parse } from '../src/index.js';

function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

const RANGES = { minute: [0, 59], hour: [0, 23], dom: [1, 31], month: [1, 12], dow: [0, 6] };

// Returns { text, set, star } for one field.
function genField(rand, name) {
  const [min, max] = RANGES[name];
  const pick = (a, b) => a + Math.floor(rand() * (b - a + 1));
  const kind = Math.floor(rand() * 5);
  const set = new Set();
  if (kind === 0) {
    for (let v = min; v <= max; v++) set.add(v);
    return { text: '*', set, star: true };
  }
  if (kind === 1) {
    const step = pick(2, name === 'minute' ? 20 : 6);
    for (let v = min; v <= max; v += step) set.add(v);
    return { text: `*/${step}`, set, star: true };
  }
  if (kind === 2) {
    const a = pick(min, max);
    const b = pick(a, max);
    for (let v = a; v <= b; v++) set.add(v);
    return { text: `${a}-${b}`, set, star: false };
  }
  if (kind === 3) {
    const a = pick(min, max);
    const b = pick(a, max);
    const step = pick(2, 5);
    for (let v = a; v <= b; v += step) set.add(v);
    return { text: `${a}-${b}/${step}`, set, star: false };
  }
  const n = pick(1, 4);
  for (let i = 0; i < n; i++) set.add(pick(min, max));
  return { text: [...set].join(','), set, star: false };
}

const dtf = (timeZone) => new Intl.DateTimeFormat('en-US', {
  timeZone, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric',
  hour: 'numeric', minute: 'numeric', weekday: 'short',
});
const WD = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };

function localParts(fmt, ms) {
  if (fmt === null) { // UTC fast path
    const d = new Date(ms);
    return { mi: d.getUTCMinutes(), h: d.getUTCHours(), d: d.getUTCDate(), mo: d.getUTCMonth() + 1, dow: d.getUTCDay() };
  }
  const o = {};
  for (const { type, value } of fmt.formatToParts(ms)) o[type] = value;
  return { mi: +o.minute, h: +o.hour % 24, d: +o.day, mo: +o.month, dow: WD[o.weekday] };
}

function oracleMatches(f, p) {
  if (!f.minute.set.has(p.mi) || !f.hour.set.has(p.h) || !f.month.set.has(p.mo)) return false;
  const domOk = f.dom.set.has(p.d);
  const dowOk = f.dow.set.has(p.dow);
  return f.dom.star || f.dow.star ? domOk && dowOk : domOk || dowOk;
}

function runFuzz({ timeZone, seed, cases, horizonDays, startFrom, startSpanDays }) {
  const rand = rng(seed);
  const fmt = timeZone === 'UTC' ? null : dtf(timeZone);
  for (let i = 0; i < cases; i++) {
    const f = {};
    for (const name of Object.keys(RANGES)) f[name] = genField(rand, name);
    // Avoid "never matches" shapes (e.g. only Feb 30) - the parser rightly rejects those.
    const text = `${f.minute.text} ${f.hour.text} ${f.dom.text} ${f.month.text} ${f.dow.text}`;
    let cron;
    try { cron = parse(text, { timeZone }); } catch (e) {
      if (e instanceof RangeError) continue;
      throw e;
    }
    const from = startFrom + Math.floor(rand() * startSpanDays * 86_400_000);
    const actual = cron.next(from).getTime();

    let t = Math.floor(from / 60_000) * 60_000 + 60_000;
    const end = from + horizonDays * 86_400_000;
    let expected = null;
    for (; t <= end; t += 60_000) {
      if (oracleMatches(f, localParts(fmt, t))) { expected = t; break; }
    }
    if (expected === null) {
      assert.ok(actual > end - 60_000, `"${text}" ${timeZone}: oracle found nothing within horizon but next() = ${new Date(actual).toISOString()}`);
    } else {
      assert.equal(new Date(actual).toISOString(), new Date(expected).toISOString(),
        `"${text}" in ${timeZone} from ${new Date(from).toISOString()}`);
    }
  }
}

test('fuzz UTC (1000 random expressions)', () => {
  runFuzz({ timeZone: 'UTC', seed: 1, cases: 1000, horizonDays: 800, startFrom: Date.UTC(2020, 0, 1), startSpanDays: 3000 });
});

test('fuzz fixed-offset zones (Kolkata +5:30, Kathmandu +5:45)', () => {
  runFuzz({ timeZone: 'Asia/Kolkata', seed: 2, cases: 10, horizonDays: 40, startFrom: Date.UTC(2024, 0, 1), startSpanDays: 700 });
  runFuzz({ timeZone: 'Asia/Kathmandu', seed: 3, cases: 10, horizonDays: 40, startFrom: Date.UTC(2024, 0, 1), startSpanDays: 700 });
});

test('fuzz DST zones away from transitions (Jan-Feb and Jun-Aug windows)', () => {
  // Windows are fully inside a single offset period in both hemispheres' DST schedules.
  for (const [timeZone, seed] of [['Europe/London', 4], ['America/New_York', 5], ['Australia/Sydney', 6]]) {
    runFuzz({ timeZone, seed, cases: 6, horizonDays: 10, startFrom: Date.UTC(2026, 5, 1), startSpanDays: 30 });
    runFuzz({ timeZone, seed: seed + 100, cases: 6, horizonDays: 10, startFrom: Date.UTC(2026, 0, 1), startSpanDays: 30 });
  }
});
