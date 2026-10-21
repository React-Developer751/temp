const MACROS = {
  '@yearly': '0 0 1 1 *',
  '@annually': '0 0 1 1 *',
  '@monthly': '0 0 1 * *',
  '@weekly': '0 0 * * 0',
  '@daily': '0 0 * * *',
  '@midnight': '0 0 * * *',
  '@hourly': '0 * * * *',
};

const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const WEEKDAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

const SPECS = {
  second: { min: 0, max: 59 },
  minute: { min: 0, max: 59 },
  hour: { min: 0, max: 23 },
  dayOfMonth: { min: 1, max: 31, question: true },
  month: { min: 1, max: 12, names: MONTHS, nameBase: 1 },
  dayOfWeek: { min: 0, max: 7, starMax: 6, names: WEEKDAYS, nameBase: 0, question: true },
};

// Longest possible month (Feb counted as 29) - used to reject "Feb 30"-style expressions.
const MAX_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function fail(field, text, why) {
  throw new SyntaxError(`pure-cron-parser: invalid ${field} field "${text}": ${why}`);
}

function parseValue(field, text, token, spec) {
  let n;
  if (/^\d+$/.test(token)) n = Number(token);
  else if (spec.names) {
    const idx = spec.names.indexOf(token.toUpperCase());
    if (idx === -1) fail(field, text, `unknown value "${token}"`);
    n = idx + spec.nameBase;
  } else fail(field, text, `unknown value "${token}"`);
  if (n < spec.min || n > spec.max) fail(field, text, `${n} is outside ${spec.min}-${spec.max}`);
  return n;
}

function parseField(field, text, spec) {
  const values = new Set();
  const star = text.startsWith('*') || (spec.question && text === '?');

  for (const part of text.split(',')) {
    if (part === '') fail(field, text, 'empty list item');
    const [rangeText, stepText, extra] = part.split('/');
    if (extra !== undefined) fail(field, text, 'more than one "/"');

    let step = 1;
    if (stepText !== undefined) {
      if (!/^\d+$/.test(stepText) || Number(stepText) < 1) fail(field, text, `bad step "${stepText}"`);
      step = Number(stepText);
    }

    let from;
    let to;
    if (rangeText === '*' || (spec.question && rangeText === '?')) {
      if (rangeText === '?' && stepText !== undefined) fail(field, text, '"?" cannot have a step');
      from = spec.min;
      to = spec.starMax ?? spec.max;
    } else if (rangeText.includes('-')) {
      const bounds = rangeText.split('-');
      if (bounds.length !== 2) fail(field, text, `bad range "${rangeText}"`);
      from = parseValue(field, text, bounds[0], spec);
      to = parseValue(field, text, bounds[1], spec);
      if (from > to) fail(field, text, `range "${rangeText}" is reversed`);
    } else {
      from = parseValue(field, text, rangeText, spec);
      to = stepText !== undefined ? (spec.starMax ?? spec.max) : from; // "5/15" == "5-max/15"
    }

    for (let v = from; v <= to; v += step) values.add(field === 'dayOfWeek' && v === 7 ? 0 : v);
  }

  const list = [...values].sort((a, b) => a - b);
  return { list, set: new Set(list), star };
}

/**
 * Parse a cron expression (5 fields, or 6 with a leading seconds field, or an @macro).
 * @returns {{ second, minute, hour, dayOfMonth, month, dayOfWeek }} each `{ list, set, star }`
 */
export function parseFields(expression) {
  if (typeof expression !== 'string') throw new TypeError('pure-cron-parser: expression must be a string');
  let source = expression.trim();
  if (source.startsWith('@')) {
    const macro = MACROS[source.toLowerCase()];
    if (!macro) throw new SyntaxError(`pure-cron-parser: unknown macro "${source}"`);
    source = macro;
  }

  const parts = source.split(/\s+/);
  if (parts.length !== 5 && parts.length !== 6) {
    throw new SyntaxError(
      `pure-cron-parser: expected 5 or 6 fields, got ${source === '' ? 0 : parts.length} in "${expression}"`,
    );
  }
  if (parts.length === 5) parts.unshift('0');

  const [sec, min, hour, dom, month, dow] = parts;
  const fields = {
    second: parseField('second', sec, SPECS.second),
    minute: parseField('minute', min, SPECS.minute),
    hour: parseField('hour', hour, SPECS.hour),
    dayOfMonth: parseField('dayOfMonth', dom, SPECS.dayOfMonth),
    month: parseField('month', month, SPECS.month),
    dayOfWeek: parseField('dayOfWeek', dow, SPECS.dayOfWeek),
  };

  // Only dom restricted (AND semantics): make sure some chosen month can actually have a chosen day.
  if (!fields.dayOfMonth.star && fields.dayOfWeek.star) {
    const possible = fields.month.list.some((m) => fields.dayOfMonth.list.some((d) => d <= MAX_DAYS[m - 1]));
    if (!possible) {
      throw new RangeError(`pure-cron-parser: "${expression}" can never match (day does not exist in those months)`);
    }
  }
  return fields;
}
