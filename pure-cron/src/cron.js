import { parseFields } from './parse.js';
import { offsetAt, resolveTimeZone, wallFields, wallToInstants } from './timezone.js';

const YEARS_AHEAD = 12; // Feb 29 can be up to 8 years away across a skipped leap year
const MAX_DATE_MS = 8.64e15; // ECMAScript Date limit
const MAX_DST_SHIFT_MS = 3 * 3_600_000; // longest backward clock change, with room to spare

function toMs(from) {
  const ms = from instanceof Date ? from.getTime() : from;
  if (typeof ms !== 'number' || !Number.isFinite(ms)) {
    throw new TypeError('pure-cron: date must be a valid Date or timestamp');
  }
  if (Math.abs(ms) > MAX_DATE_MS - 366 * 86_400_000) {
    throw new RangeError('pure-cron: date is too close to the limits of the Date type');
  }
  return ms;
}

function firstAtLeast(list, v) {
  for (const x of list) if (x >= v) return x;
  return undefined;
}

function daysInMonth(y, mo) {
  return new Date(Date.UTC(y, mo, 0)).getUTCDate();
}

// Re-normalise overflowing fields (e.g. s=60, d=32) through the UTC calendar.
function normalise(w) {
  const dt = new Date(Date.UTC(w.y, w.mo - 1, w.d, w.h, w.mi, w.s));
  return {
    y: dt.getUTCFullYear(), mo: dt.getUTCMonth() + 1, d: dt.getUTCDate(),
    h: dt.getUTCHours(), mi: dt.getUTCMinutes(), s: dt.getUTCSeconds(),
  };
}

export class CronExpression {
  /**
   * @param {string} expression
   * @param {{ timeZone?: string }} [options]
   */
  constructor(expression, options = {}) {
    this.source = expression;
    if (options === null || typeof options !== 'object') {
      throw new TypeError('pure-cron: options must be an object');
    }
    const zone = resolveTimeZone(options.timeZone);
    this.timeZone = zone.name;
    this._tz = zone.canonical;
    this._f = parseFields(expression);
  }

  _dayMatches(y, mo, d) {
    const { dayOfMonth, dayOfWeek } = this._f;
    const domOk = dayOfMonth.set.has(d);
    const dowOk = dayOfWeek.set.has(new Date(Date.UTC(y, mo - 1, d)).getUTCDay());
    // Classic cron: both restricted => either may match; otherwise both must (the starred one always does).
    return dayOfMonth.star || dayOfWeek.star ? domOk && dowOk : domOk || dowOk;
  }

  /** True if `date` (to the second) is a scheduled time. */
  matches(date = new Date()) {
    const w = wallFields(Math.floor(toMs(date) / 1000) * 1000, this._tz);
    const f = this._f;
    return f.second.set.has(w.s) && f.minute.set.has(w.mi) && f.hour.set.has(w.h) &&
      f.month.set.has(w.mo) && this._dayMatches(w.y, w.mo, w.d);
  }

  /**
   * First scheduled time strictly after `from` (default: now).
   *
   * When clocks go back and an hour repeats, a job with a wildcard / stepped hour field (e.g. every 15
   * minutes) runs in both passes, like Vixie cron; a job at a fixed hour (e.g. 01:30 daily) runs once.
   */
  next(from = new Date()) {
    const fromMs = toMs(from);
    const repeat = this._f.hour.star;
    let found = this._search(wallFields(Math.floor(fromMs / 1000) * 1000 + 1000, this._tz), fromMs, repeat);

    // Walking forward through wall time from inside the first pass of a repeated hour jumps past the second
    // pass; if the clocks go back before the run we found, also look from the moment they do.
    if (repeat && this._tz !== 'UTC') {
      let hi = Math.min(found, fromMs + MAX_DST_SHIFT_MS);
      const startOffset = offsetAt(fromMs, this._tz);
      if (offsetAt(hi, this._tz) < startOffset) {
        let lo = fromMs;
        while (hi - lo > 1000) {
          const mid = lo + Math.floor((hi - lo) / 2);
          if (offsetAt(mid, this._tz) === startOffset) lo = mid;
          else hi = mid;
        }
        const back = Math.floor(hi / 1000) * 1000;
        const again = this._search(wallFields(back, this._tz), Math.max(fromMs, back - 1), true);
        if (again < found) found = again;
      }
    }
    return new Date(found);
  }

  /** Earliest scheduled instant (ms) > `afterMs`, walking wall-clock time forward from `start`. */
  _search(start, afterMs, allowRepeat) {
    const f = this._f;
    let w = start;
    const lastYear = w.y + YEARS_AHEAD;

    for (;;) {
      if (!(w.y <= lastYear)) { // also catches NaN from calendar overflow
        throw new RangeError(`pure-cron: no run of "${this.source}" within ${YEARS_AHEAD} years`);
      }

      if (!f.month.set.has(w.mo)) {
        const m = firstAtLeast(f.month.list, w.mo + 1);
        w = m === undefined ? { y: w.y + 1, mo: f.month.list[0], d: 1, h: 0, mi: 0, s: 0 }
          : { y: w.y, mo: m, d: 1, h: 0, mi: 0, s: 0 };
        continue;
      }
      if (!this._dayMatches(w.y, w.mo, w.d)) {
        w = normalise({ y: w.y, mo: w.mo, d: w.d + 1, h: 0, mi: 0, s: 0 });
        continue;
      }
      const h = firstAtLeast(f.hour.list, w.h);
      if (h === undefined) {
        w = normalise({ y: w.y, mo: w.mo, d: w.d + 1, h: 0, mi: 0, s: 0 });
        continue;
      }
      if (h !== w.h) w = { ...w, h, mi: 0, s: 0 };

      const mi = firstAtLeast(f.minute.list, w.mi);
      if (mi === undefined) {
        w = normalise({ ...w, h: w.h + 1, mi: 0, s: 0 });
        continue;
      }
      if (mi !== w.mi) w = { ...w, mi, s: 0 };

      const s = firstAtLeast(f.second.list, w.s);
      if (s === undefined) {
        w = normalise({ ...w, mi: w.mi + 1, s: 0 });
        continue;
      }
      w = { ...w, s };

      const instants = wallToInstants(w, this._tz);
      // A repeated wall time counts twice only for wildcard-hour jobs; otherwise its first occurrence only.
      const instant = allowRepeat ? instants.find((t) => t > afterMs) : instants[0] > afterMs ? instants[0] : undefined;
      if (instant !== undefined && instant <= MAX_DATE_MS) return instant;
      w = normalise({ ...w, s: w.s + 1 }); // already passed (e.g. repeated hour after fall-back)
    }
  }

  /** The next `count` run times after `from`. */
  nextRuns(count, from = new Date()) {
    if (!Number.isInteger(count) || count < 0) throw new TypeError('pure-cron: count must be a non-negative integer');
    const out = [];
    let cursor = toMs(from);
    for (let i = 0; i < count; i++) {
      const d = this.next(cursor);
      out.push(d);
      cursor = d.getTime();
    }
    return out;
  }

  /** Milliseconds from `from` (default now) until the next run. */
  msUntilNext(from = new Date()) {
    return this.next(from).getTime() - toMs(from);
  }
}

export function parse(expression, options) {
  return new CronExpression(expression, options);
}

export function validate(expression, options) {
  try {
    parse(expression, options);
    return true;
  } catch {
    return false;
  }
}
