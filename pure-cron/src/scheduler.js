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
  if (typeof fn !== 'function') throw new TypeError('pure-cron: callback must be a function');
  if (options === null || typeof options !== 'object') throw new TypeError('pure-cron: options must be an object');
  const {
    timeZone, overlap = false, runOnInit = false, unref = false, signal,
    maxWaitMs = DEFAULT_MAX_WAIT_MS, onError, onSkip,
  } = options;
  for (const [name, v] of [['onError', onError], ['onSkip', onSkip]]) {
    if (v !== undefined && typeof v !== 'function') throw new TypeError(`pure-cron: "${name}" must be a function`);
  }
  if (typeof maxWaitMs !== 'number' || !(maxWaitMs >= 1000 && maxWaitMs <= MAX_TIMER_MS)) {
    throw new TypeError(`pure-cron: "maxWaitMs" must be a number between 1000 and ${MAX_TIMER_MS}`);
  }
  if (signal !== undefined && typeof signal?.aborted !== 'boolean') {
    throw new TypeError('pure-cron: "signal" must be an AbortSignal');
  }
  if (expression instanceof CronExpression && timeZone !== undefined && timeZone !== expression.timeZone) {
    throw new TypeError(
      `pure-cron: "timeZone" (${timeZone}) differs from the parsed expression's (${expression.timeZone}); ` +
      'pass the zone to parse() instead',
    );
  }
  const cron = expression instanceof CronExpression ? expression : new CronExpression(expression, { timeZone });

  let timer = null;
  let target = 0;
  let running = false;
  // Bumped by every start()/stop(), so a run whose callback restarted the task doesn't schedule again.
  let generation = 0;
  let inFlight = 0;
  let idleWaiters = [];

  function reportError(error) {
    try {
      if (onError) onError(error);
      else console.error('pure-cron: task failed:', error);
    } catch (inner) {
      console.error('pure-cron: onError threw:', inner);
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
    if (timer) clearTimeout(timer);
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
    const gen = generation;
    dispatch(new Date(target));
    if (!running || gen !== generation) return; // the callback called stop() (and maybe start() again)
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

  const onAbort = () => task.stop();

  const task = {
    start() {
      if (running || signal?.aborted) return task;
      target = cron.next().getTime();
      running = true;
      generation++;
      signal?.addEventListener('abort', onAbort, { once: true });
      arm();
      return task;
    },
    stop() {
      if (running) generation++;
      running = false;
      if (timer) clearTimeout(timer);
      timer = null;
      // A long-lived shared signal must not keep stopped tasks alive.
      signal?.removeEventListener('abort', onAbort);
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

  task.start();
  if (runOnInit && running) dispatch(new Date());
  return task;
}
