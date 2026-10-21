// setTimeout stores the delay as a signed 32-bit int; anything larger fires after ~1ms.
const MAX_TIMER_MS = 2 ** 31 - 1;

const DEFAULTS = {
  retries: 3,
  factor: 2,
  minTimeout: 1000,
  maxTimeout: Infinity,
  jitter: true,
};

/**
 * Throw inside the retried function to stop retrying immediately.
 * If constructed from an Error, `retry()` rejects with that original error.
 */
export class AbortError extends Error {
  /** @param {string | Error} messageOrError */
  constructor(messageOrError) {
    super(messageOrError instanceof Error ? messageOrError.message : messageOrError);
    this.name = 'AbortError';
    this.originalError = messageOrError instanceof Error ? messageOrError : undefined;
  }
}

/** Rejected by `retry()` attempts that exceed the `timeout` option. Retryable like any other error. */
export class TimeoutError extends Error {
  /** @param {number} ms */
  constructor(ms) {
    super(`Attempt timed out after ${ms}ms`);
    this.name = 'TimeoutError';
  }
}

function assertNumber(name, value, { min = 0, allowInfinity = false } = {}) {
  const ok = typeof value === 'number' && !Number.isNaN(value) && value >= min &&
    (allowInfinity || Number.isFinite(value));
  if (!ok) throw new TypeError(`pure-retry: "${name}" must be a number >= ${min}, got ${String(value)}`);
}

function assertFunction(name, value) {
  if (value !== undefined && typeof value !== 'function') {
    throw new TypeError(`pure-retry: "${name}" must be a function`);
  }
}

function resolveOptions(options) {
  if (options === null || typeof options !== 'object') {
    throw new TypeError('pure-retry: options must be an object');
  }
  // Options explicitly set to undefined fall back to defaults.
  const opts = { ...DEFAULTS };
  for (const [key, value] of Object.entries(options)) {
    if (value !== undefined) opts[key] = value;
  }

  assertNumber('retries', opts.retries, { allowInfinity: true });
  if (opts.retries !== Infinity && !Number.isInteger(opts.retries)) {
    throw new TypeError(`pure-retry: "retries" must be an integer or Infinity, got ${opts.retries}`);
  }
  assertNumber('factor', opts.factor, { min: 1 });
  assertNumber('minTimeout', opts.minTimeout);
  assertNumber('maxTimeout', opts.maxTimeout, { allowInfinity: true });
  if (![true, false, 'equal', 'full'].includes(opts.jitter)) {
    throw new TypeError('pure-retry: "jitter" must be true, false, "equal" or "full"');
  }
  if (opts.timeout !== undefined) assertNumber('timeout', opts.timeout, { min: 1 });
  if (opts.maxRetryTime !== undefined) assertNumber('maxRetryTime', opts.maxRetryTime, { allowInfinity: true });
  assertFunction('shouldRetry', opts.shouldRetry);
  assertFunction('onRetry', opts.onRetry);
  if (opts.signal !== undefined && typeof opts.signal?.aborted !== 'boolean') {
    throw new TypeError('pure-retry: "signal" must be an AbortSignal');
  }
  return opts;
}

/**
 * Delay (ms) before retry number `retryIndex` (0 = first retry).
 * base = min(minTimeout * factor^retryIndex, maxTimeout, 2^31-1)
 *   jitter "equal" (default for `true`): base/2 + random * base/2  -> keeps growth, spreads callers
 *   jitter "full": random * base                                    -> maximum spread
 */
export function computeDelay(retryIndex, options = {}, random = Math.random) {
  const { factor, minTimeout, maxTimeout, jitter } = resolveOptions(options);
  // Clamp the multiplier first so 0 * Infinity can never produce NaN.
  const growth = Math.min(factor ** retryIndex, MAX_TIMER_MS);
  const base = Math.min(minTimeout * growth, maxTimeout, MAX_TIMER_MS);
  let delay = base;
  if (jitter === true || jitter === 'equal') delay = base / 2 + random() * (base / 2);
  else if (jitter === 'full') delay = random() * base;
  return Math.round(delay);
}

function abortReason(signal) {
  return signal.reason ?? new DOMException('The operation was aborted', 'AbortError');
}

function sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(abortReason(signal));
    const onAbort = () => {
      clearTimeout(timer);
      reject(abortReason(signal));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

/**
 * One attempt. With a `timeout` and/or a `signal`, the attempt is raced against them and `fn` receives an
 * AbortSignal (aborted on timeout or when the caller's signal aborts) so it can cancel real work.
 */
async function runAttempt(fn, attempt, { timeout, signal }) {
  if (timeout === undefined && !signal) return fn(attempt, { signal: undefined });

  const controller = new AbortController();
  let timer;
  let onAbort;
  const guards = [];
  if (timeout !== undefined) {
    guards.push(new Promise((_, reject) => {
      timer = setTimeout(() => {
        const error = new TimeoutError(timeout);
        controller.abort(error);
        reject(error);
      }, timeout);
    }));
  }
  if (signal) {
    guards.push(new Promise((_, reject) => {
      onAbort = () => {
        controller.abort(abortReason(signal));
        reject(abortReason(signal));
      };
      signal.addEventListener('abort', onAbort, { once: true });
    }));
  }
  try {
    // Promise.race keeps listening to the losers, so a late rejection from `fn` is never "unhandled".
    return await Promise.race([Promise.resolve().then(() => fn(attempt, { signal: controller.signal })), ...guards]);
  } finally {
    clearTimeout(timer);
    if (onAbort) signal.removeEventListener('abort', onAbort);
  }
}

/**
 * Run `fn` until it resolves, retrying on failure with exponential backoff.
 * `retries` is the number of retries AFTER the first attempt (retries: 3 => up to 4 calls).
 * When retries run out the last error is thrown unchanged. If `signal` aborts, rejects with
 * `signal.reason`. Errors thrown by `shouldRetry` / `onRetry` propagate to the caller.
 *
 * @template T
 * @param {(attempt: number, context: { signal?: AbortSignal }) => T | Promise<T>} fn
 * @param {import('./index.d.ts').RetryOptions} [options]
 * @returns {Promise<T>}
 */
export async function retry(fn, options = {}) {
  if (typeof fn !== 'function') throw new TypeError('pure-retry: first argument must be a function');
  const opts = resolveOptions(options);
  const { retries, signal, shouldRetry, onRetry, maxRetryTime } = opts;
  const startedAt = performance.now();

  for (let attempt = 1; ; attempt++) {
    if (signal?.aborted) throw abortReason(signal);

    try {
      return await runAttempt(fn, attempt, opts);
    } catch (error) {
      if (error instanceof AbortError) throw error.originalError ?? error;
      if (attempt > retries) throw error;
      if (signal?.aborted) throw abortReason(signal);
      if (shouldRetry && !(await shouldRetry(error, attempt))) throw error;

      const delay = computeDelay(attempt - 1, opts);
      if (maxRetryTime !== undefined && performance.now() - startedAt + delay > maxRetryTime) throw error;
      if (onRetry) await onRetry(error, attempt, delay);
      await sleep(delay, signal);
    }
  }
}

export default retry;
