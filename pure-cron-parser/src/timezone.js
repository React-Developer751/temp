// Time zone helpers built on Intl only. All "wall" values are { y, mo (1-12), d, h, mi, s }.

const DAY_MS = 24 * 60 * 60 * 1000;
const formatters = new Map();

function formatter(timeZone) {
  let f = formatters.get(timeZone);
  if (!f) {
    f = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hourCycle: 'h23',
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
    });
    formatters.set(timeZone, f);
  }
  return f;
}

export function systemTimeZone() {
  return new Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

/**
 * Validates a zone. `name` is what the caller asked for (shown back to them);
 * `canonical` is ICU's name, used internally so "Etc/UTC" and "utc" hit the UTC fast path.
 * Throws RangeError for an unknown zone.
 */
export function resolveTimeZone(timeZone) {
  if (timeZone === undefined) {
    const name = systemTimeZone();
    return { name, canonical: formatter(name).resolvedOptions().timeZone };
  }
  if (typeof timeZone !== 'string' || timeZone === '') {
    throw new TypeError('pure-cron-parser: "timeZone" must be a non-empty string');
  }
  try {
    return { name: timeZone, canonical: formatter(timeZone).resolvedOptions().timeZone };
  } catch {
    throw new RangeError(`pure-cron-parser: unknown time zone "${timeZone}"`);
  }
}

/** Wall-clock fields of the instant `ms` in `timeZone` (millis are dropped). */
export function wallFields(ms, timeZone) {
  if (timeZone === 'UTC') {
    const dt = new Date(ms);
    return {
      y: dt.getUTCFullYear(), mo: dt.getUTCMonth() + 1, d: dt.getUTCDate(),
      h: dt.getUTCHours(), mi: dt.getUTCMinutes(), s: dt.getUTCSeconds(),
    };
  }
  const out = {};
  for (const { type, value } of formatter(timeZone).formatToParts(ms)) {
    if (type !== 'literal') out[type] = Number(value);
  }
  return {
    y: out.year, mo: out.month, d: out.day,
    h: out.hour === 24 ? 0 : out.hour, mi: out.minute, s: out.second,
  };
}

function wallAsUtcMs(w) {
  return Date.UTC(w.y, w.mo - 1, w.d, w.h, w.mi, w.s);
}

/** UTC offset (ms, local - utc) in effect at instant `ms`. */
function offsetAt(ms, timeZone) {
  const whole = Math.floor(ms / 1000) * 1000;
  return wallAsUtcMs(wallFields(whole, timeZone)) - whole;
}

function sameWall(a, b) {
  return a.y === b.y && a.mo === b.mo && a.d === b.d && a.h === b.h && a.mi === b.mi && a.s === b.s;
}

/**
 * Instant (ms) at which the wall clock reads `wall` in `timeZone`.
 * - repeated time (clocks go back): the first occurrence wins
 * - skipped time (clocks go forward): the instant the clocks jump, i.e. the job runs right after the gap
 */
export function wallToInstant(wall, timeZone) {
  const guess = wallAsUtcMs(wall);
  if (timeZone === 'UTC') return guess;

  // Offsets a day either side cover both sides of any single transition.
  const before = offsetAt(guess - DAY_MS, timeZone);
  const after = offsetAt(guess + DAY_MS, timeZone);
  const candidates = [guess - before, guess - after].filter((c) => sameWall(wallFields(c, timeZone), wall));
  if (candidates.length > 0) return Math.min(...candidates);

  // Wall time falls in a gap: binary-search the transition instant between the two candidates.
  let lo = Math.min(guess - before, guess - after);
  let hi = Math.max(guess - before, guess - after);
  const loOffset = offsetAt(lo, timeZone);
  while (hi - lo > 1) {
    const mid = lo + Math.floor((hi - lo) / 2);
    if (offsetAt(mid, timeZone) === loOffset) lo = mid;
    else hi = mid;
  }
  return hi;
}
