# Changelog

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
