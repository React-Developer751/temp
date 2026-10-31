# Changelog

## 0.3.0
- DST fall-back now follows Vixie cron: wildcard/stepped-hour jobs (`*/5 * * * *`) run in both passes of the
  repeated hour instead of pausing for an hour; fixed-hour jobs still run once.
- Fixed: calling `stop()` + `start()` inside the callback skipped the next run and leaked a timer.
- Fixed: `runOnInit` ran even when the `signal` had already aborted.
- Fixed: `7/n` in the day-of-week field was accepted but never ran; any field that matches nothing now throws.
- `schedule(parsedExpression, fn, { timeZone })` with a different zone now throws instead of ignoring it.
- `stop()` removes the listener from the abort signal, so a shared long-lived signal doesn't keep tasks alive.

## 0.2.0
- Fixed: `next()` hung forever for dates near the `Date` limits; it now throws `RangeError`.
- `cron.timeZone` now returns the name you passed (was ICU's canonical alias, e.g. `Asia/Calcutta`).
- Scheduler: waits are chunked (`maxWaitMs`, default 1h) so jobs stay on time after system sleep or clock changes.
- Scheduler: `whenIdle()` for graceful shutdown; a failing `cron.next()` no longer crashes the process;
  `start()` is a no-op after the abort signal fired.
- Added a differential fuzz test against a brute-force oracle (UTC, fixed-offset and DST zones).
- `engines.node` is now `>=20.19.0`.

## 0.1.0
- Initial release.
