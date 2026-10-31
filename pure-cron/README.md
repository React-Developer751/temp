# pure-cron

Zero-dependency cron parser + scheduler for Node.js (>=20.19). No per-second `setInterval` polling:
it **calculates the next run time, then arms one `setTimeout` for exactly that long**. When the task
runs it calculates the next one. While waiting there is no loop: the only wake-up is one cheap clock check per hour (see `maxWaitMs`).

```js
import { schedule, parse } from 'pure-cron';

// 1. Run a job. Starts immediately.
const task = schedule('0 0 * * *', (scheduledFor) => {
  console.log('midnight job for', scheduledFor);
}, { timeZone: 'Asia/Kolkata' });

task.nextRun();  // Date of the next run
task.stop();     // cancel;  task.start() resumes

// 2. Or just calculate
const cron = parse('*/15 9-17 * * mon-fri', { timeZone: 'Europe/London' });
cron.next();              // next Date after now
cron.nextRuns(5);         // next 5 Dates
cron.msUntilNext();       // e.g. 45_000_000
cron.matches(new Date()); // is "now" a run time?
```

## Syntax

`[second] minute hour day-of-month month day-of-week` (5 fields, or 6 with a leading seconds field)

| Feature | Examples |
|---|---|
| Wildcard, list, range, step | `*`, `1,15`, `9-17`, `*/5`, `10-50/10`, `5/15` |
| Month / weekday names | `JAN-MAR`, `mon-fri` (case-insensitive) |
| Sunday | `0` or `7` |
| Macros | `@yearly` `@annually` `@monthly` `@weekly` `@daily` `@midnight` `@hourly` |
| `?` | accepted in day-of-month / day-of-week as "any" |

If **both** day-of-month and day-of-week are restricted, a day matches when **either** does (standard cron:
`0 0 13 * 5` = the 13th *or* any Friday). If one of them starts with `*`, both must match.
Invalid input throws `SyntaxError`; expressions that can never fire (`0 0 30 2 *`) throw `RangeError`.

## Time zones and DST

Any IANA zone via built-in `Intl` (default: the system zone). Rules:

- **Skipped time** (spring forward): a job scheduled inside the gap runs at the moment the clocks jump
  (`30 2 * * *` on the US switch day runs at 03:00). It does not run twice.
- **Repeated time** (fall back), same rule as Vixie cron:
  - a job at a **fixed hour** (`30 1 * * *`, `*/15 1 * * *`) runs **once**, in the first pass;
  - a job whose hour field is a **wildcard or step** (`*/5 * * * *`, `0 */2 * * *`) keeps its rhythm and runs
    in **both** passes, so heartbeats and pollers don't go quiet for an hour.

## `schedule(expression, fn, options)`

`fn(scheduledFor: Date)` may be sync or async.

| Option | Default | Meaning |
|---|---|---|
| `timeZone` | system | IANA zone. With an already parsed expression, use `parse(expr, { timeZone })`; a different zone here throws |
| `overlap` | `false` | `false`: skip a tick if the previous async run is still going |
| `runOnInit` | `false` | also call `fn` once right away |
| `unref` | `false` | don't keep the process alive just for this timer |
| `signal` | – | `AbortSignal` that stops the task |
| `maxWaitMs` | `3600000` | Longest single timer (1s..2^31-1). Keeps jobs on time after sleep / clock changes |
| `onError(err)` | `console.error` | `fn` threw / rejected. The schedule keeps going |
| `onSkip(date)` | – | a tick was skipped because of `overlap: false` |

The returned task has `start()`, `stop()`, `running`, `nextRun()`, `cron` and `whenIdle()` (a promise that
resolves when no async run is in flight, for graceful shutdown: `task.stop(); await task.whenIdle();`).
`stop()` and `start()` may be called from inside `fn` (e.g. to reload settings); the schedule stays on time.

**On "no polling":** there is no per-second loop. While waiting, the process wakes up once per `maxWaitMs`
(default 1 hour) only to compare the clock with the target, so a laptop sleep or an NTP / VM clock jump delays a
job by at most that much. Set `maxWaitMs: 2**31 - 1` for a single timer per run (max ~24.8 days per chunk).

## Behaviour to know

- If the machine sleeps through a run time, the job runs **once, late**, after wake-up, then resumes from
  "now". Missed runs are not replayed.
- `next()` looks at most 12 years ahead (enough for Feb 29 across a skipped leap year).
- `matches(date)` is purely wall-clock based, so both passes of a repeated DST hour match (even for fixed-hour
  jobs, which `next()` runs only once).
- Day of week: `0` and `7` are Sunday; `7/n` means Sundays only; `1/2` means Mon, Wed, Fri.
- Not supported (throws `SyntaxError`): Quartz extras `L`, `W`, `#`, a year field, and `@reboot`.
- ESM package; `require('pure-cron')` also works on Node >= 20.19 / 22.12.
- TypeScript types are included (ESM projects: any recent TypeScript; CommonJS projects: TypeScript >= 5.8 with `"module": "nodenext"`).

## Dev

```bash
npm test   # node:test, no dependencies
```
