import { CronExpression } from './cron.js';

// setTimeout takes a signed 32-bit delay (~24.8 days).
const MAX_TIMER_MS = 2 ** 31 - 1;
const DEFAULT_MAX_WAIT_MS = 60 * 60 * 1000;

/**
 * Run `fn` on a cron schedule using one setTimeout at a time (no polling loop).
 * The task starts immediately; call `task.stop()` to cancel.
 *
 * Long waits are split into chunks of at most `maxWaitMs` (default 1 hour). Each chunk end is just a
 * clock check - it keeps the job on time after system sleep or a wall-clock change at a cost of one
 * wake-up per hour.
 *
 * @param {string | CronExpression} expression
 * @param {(scheduledFor: Date) => unknown} fn
 * @param {object} [options] timeZone, overlap, runOnInit, unref, signal, maxWaitMs, onError, onSkip
 */
export function schedule(expression, fn, options = {}) {
  if (typeof fn !== 'function') throw new TypeError('pure-cron-parser: callback must be a function');
  if (options === null || typeof options !== 'object') throw new TypeError('pure-cron-parser: options must be an object');
  const {
    timeZone, overlap = false, runOnInit = false, unref = false, signal,
    maxWaitMs = DEFAULT_MAX_WAIT_MS, onError, onSkip,
  } = options;
  for (const [name, v] of [['onError', onError], ['onSkip', onSkip]]) {
    if (v !== undefined && typeof v !== 'function') throw new TypeError(`pure-cron-parser: "${name}" must be a function`);
  }
  if (typeof maxWaitMs !== 'number' || !(maxWaitMs >= 1000 && maxWaitMs <= MAX_TIMER_MS)) {
    throw new TypeError(`pure-cron-parser: "maxWaitMs" must be a number between 1000 and ${MAX_TIMER_MS}`);
  }
  if (signal !== undefined && typeof signal?.aborted !== 'boolean') {
    throw new TypeError('pure-cron-parser: "signal" must be an AbortSignal');
  }
  const cron = expression instanceof CronExpression ? expression : new CronExpression(expression, { timeZone });

  let timer = null;
  let target = 0;
  let running = false;
  let inFlight = 0;
  let idleWaiters = [];

  function reportError(error) {
    try {
      if (onError) onError(error);
      else console.error('pure-cron-parser: task failed:', error);
    } catch (inner) {
      console.error('pure-cron-parser: onError threw:', inner);
    }
  }

  function settle() {
    inFlight--;
    if (inFlight === 0) {
      const waiters = idleWaiters;
      idleWaiters = [];
      for (const resolve of waiters) resolve();
    }
  }

  function dispatch(scheduledFor) {
    if (inFlight > 0 && !overlap) {
      if (onSkip) {
        try { onSkip(scheduledFor); } catch (e) { reportError(e); }
      }
      return;
    }
    let result;
    try {
      result = fn(scheduledFor);
    } catch (error) {
      reportError(error);
      return;
    }
    if (result && typeof result.then === 'function') {
      inFlight++;
      result.then(settle, (error) => { settle(); reportError(error); });
    }
  }

  function arm() {
    const delay = Math.min(Math.max(target - Date.now(), 0), maxWaitMs);
    timer = setTimeout(onTimer, delay);
    if (unref) timer.unref();
  }

  function onTimer() {
    timer = null;
    if (!running) return;
    if (Date.now() < target) { // end of a wait chunk, or the timer fired a hair early
      arm();
      return;
    }
    dispatch(new Date(target));
    if (!running) return; // callback called stop()
    try {
      // After a long sleep we run once, late, and resume from "now" rather than replaying missed runs.
      target = cron.next(Math.max(Date.now(), target)).getTime();
    } catch (error) {
      running = false; // nothing left to schedule (e.g. date range exhausted)
      reportError(error);
      return;
    }
    arm();
  }

  const task = {
    start() {
      if (running || signal?.aborted) return task;
      target = cron.next().getTime();
      running = true;
      arm();
      return task;
    },
    stop() {
      running = false;
      if (timer) clearTimeout(timer);
      timer = null;
      return task;
    },
    /** Resolves when no async run is in flight. Use after stop() for a graceful shutdown. */
    whenIdle() {
      return inFlight === 0 ? Promise.resolve() : new Promise((resolve) => idleWaiters.push(resolve));
    },
    get running() { return running; },
    nextRun() { return running ? new Date(target) : null; },
    cron,
  };

  if (signal) signal.addEventListener('abort', () => task.stop(), { once: true });
  task.start();
  if (runOnInit) dispatch(new Date());
  return task;
}
