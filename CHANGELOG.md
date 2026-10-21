# Changelog

## 0.2.0
- Added `timeout` (per-attempt) and `TimeoutError`; `fn` now receives `(attempt, { signal })` so hung work can be cancelled.
- Added `maxRetryTime` (total time budget).
- Abort now also interrupts an attempt that ignores its signal.
- Fixed: delays could overflow `setTimeout`'s 32-bit limit (fired after ~1ms), `NaN` delays with `minTimeout: 0`,
  options set to `undefined` rejecting, hooks running after abort.
- Input validation for all options. `engines.node` is now `>=20.19.0` (also makes `require()` of this ESM package work).

## 0.1.0
- Initial release.
