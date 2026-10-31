# pure-retry

Zero-dependency retry for Node.js (>=20.19) with **exponential backoff + jitter**.

```js
import { retry } from 'pure-retry';

const data = await retry(async () => {
  const res = await fetch('https://example.com');
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}, {
  retries: 3,       // 3 retries after the first try (max 4 calls)
  factor: 2,        // delay doubles each time
  minTimeout: 1000, // base of the first delay: 1s
  jitter: true,     // randomise so 1000 clients don't retry in lockstep
});
```

## Options

| Option | Default | Meaning |
|---|---|---|
| `retries` | `3` | Retries after the first attempt |
| `factor` | `2` | Delay multiplier per retry (>= 1) |
| `minTimeout` | `1000` | Base of the first delay (ms). With the default jitter the real first wait is 500–1000 ms |
| `maxTimeout` | `Infinity` | Cap for a single delay (ms) |
| `jitter` | `true` | `true`/`'equal'`: `base/2 + rand*base/2`; `'full'`: `rand*base`; `false`: off |
| `timeout` | – | Max ms for ONE attempt (up to 2147483647, `Infinity` = none). A hung attempt fails with `TimeoutError` and is retried |
| `maxRetryTime` | – | Total time budget (ms) for all attempts and waits. No wait starts that would end past it, and an attempt still running when it runs out fails with `TimeoutError`. The last error is then thrown |
| `signal` | – | `AbortSignal` (or `null`); cancels waits and further attempts |
| `shouldRetry(err, attempt)` | – | Return `false` to stop (e.g. HTTP 4xx) |
| `onRetry(err, attempt, delay)` | – | Hook before each wait (logging) |

Delays without jitter (`jitter: false`): 1s → 2s → 4s → … With the default jitter each one is randomised within
`[base/2, base]`, so the waits are 0.5–1s → 1–2s → 2–4s → …

## Timeouts and cancelling hung requests

`fn` receives `(attempt, { signal })`. The signal aborts when the attempt times out or your own `signal` aborts,
so pass it to `fetch` and the request is really cancelled (not just abandoned):

```js
await retry((attempt, { signal }) => fetch(url, { signal }), {
  retries: 4, timeout: 5_000, maxRetryTime: 30_000, // the whole call never takes much more than 30s
});
```

Sharing one `AbortSignal` across many concurrent `retry()` calls is fine, but each call listens on it while it runs,
so with more than 10 at once Node prints a `MaxListenersExceededWarning` (exactly like `fetch`). Raise the limit with
`events.setMaxListeners(100, signal)` if you do that on purpose.

## Stop early

```js
import { retry, AbortError } from 'pure-retry';

await retry(async (attempt) => {
  const res = await fetch(url);
  if (res.status === 404) throw new AbortError(new Error('not found')); // no retry
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}, { signal: AbortSignal.timeout(30_000) });
```

When retries run out, the **last error is thrown as-is**. If `signal` aborts, it rejects with `signal.reason`.
Errors thrown inside `shouldRetry` / `onRetry` propagate to the caller. A single delay is capped at ~24.8 days
(Node's timer limit), so `retries: Infinity` is safe.

ESM package; `require('pure-retry')` also works on Node >= 20.19 / 22.12.
TypeScript types are included (ESM projects: any recent TypeScript; CommonJS projects: TypeScript >= 5.8 with `"module": "nodenext"`).
Not included on purpose: `Retry-After` header handling (use `shouldRetry` / `onRetry`), circuit breaking, rate limiting.

## Dev

```bash
npm test   # node:test, no dependencies
```
