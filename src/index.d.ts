export interface RetryOptions {
  /** Retries after the first attempt (integer or Infinity). `3` => at most 4 calls. Default 3. */
  retries?: number;
  /** Multiplier applied to the delay on every retry. Default 2. */
  factor?: number;
  /** Delay before the first retry, in ms. Default 1000. */
  minTimeout?: number;
  /** Upper bound for a single delay, in ms. Default Infinity. */
  maxTimeout?: number;
  /**
   * `true`/`'equal'`: delay = base/2 + random*base/2. `'full'`: random*base. `false`: none.
   * Default true.
   */
  jitter?: boolean | 'equal' | 'full';
  /** Max time for ONE attempt, in ms. On expiry the attempt fails with `TimeoutError` (and is retried). */
  timeout?: number;
  /** Total time budget in ms across all attempts and waits. Retrying stops (last error thrown) if the next wait would exceed it. */
  maxRetryTime?: number;
  /** Cancels pending waits and further attempts. Rejects with `signal.reason`. */
  signal?: AbortSignal;
  /** Return false to stop retrying and reject with the current error. */
  shouldRetry?: (error: unknown, attempt: number) => boolean | Promise<boolean>;
  /** Called before each wait. `attempt` is the attempt that just failed. */
  onRetry?: (error: unknown, attempt: number, delay: number) => void | Promise<void>;
}

export class TimeoutError extends Error {
  constructor(ms: number);
}

export interface AttemptContext {
  /** Aborted when this attempt times out or the caller's `signal` aborts. Pass it to fetch() etc. */
  signal?: AbortSignal;
}

export class AbortError extends Error {
  constructor(messageOrError: string | Error);
  readonly originalError?: Error;
}

export function retry<T>(
  fn: (attempt: number, context: AttemptContext) => T | Promise<T>,
  options?: RetryOptions,
): Promise<T>;

export function computeDelay(
  retryIndex: number,
  options?: Pick<RetryOptions, 'factor' | 'minTimeout' | 'maxTimeout' | 'jitter'>,
  random?: () => number,
): number;

export default retry;
