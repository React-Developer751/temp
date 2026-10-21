export interface ParseOptions {
  /** IANA zone, e.g. "Asia/Kolkata". Default: the system time zone. */
  timeZone?: string;
}

export class CronExpression {
  constructor(expression: string, options?: ParseOptions);
  readonly source: string;
  /** The IANA time zone in use (as given, or the system zone). */
  readonly timeZone: string;
  /** True if `date` (to the second) is a scheduled time. */
  matches(date?: Date | number): boolean;
  /** First scheduled time strictly after `from` (default now). */
  next(from?: Date | number): Date;
  nextRuns(count: number, from?: Date | number): Date[];
  /** Milliseconds from `from` (default now) until the next run. */
  msUntilNext(from?: Date | number): number;
}

export function parse(expression: string, options?: ParseOptions): CronExpression;
export function validate(expression: string, options?: ParseOptions): boolean;

export interface ScheduleOptions extends ParseOptions {
  /** Allow a new run while the previous async run is unfinished. Default false (skip it). */
  overlap?: boolean;
  /** Also call the callback once right now. Default false. */
  runOnInit?: boolean;
  /** Don't let the pending timer keep the process alive. Default false. */
  unref?: boolean;
  /** Stops the task when aborted. */
  signal?: AbortSignal;
  /**
   * Longest single timer, in ms (1000 .. 2^31-1). Waits are split into chunks of this size so the job
   * stays on time after system sleep or clock changes. Default 3_600_000 (1 hour).
   */
  maxWaitMs?: number;
  /** Called when the callback throws or rejects. Default: console.error. */
  onError?: (error: unknown) => void;
  /** Called when a run is skipped because the previous one is still running. */
  onSkip?: (scheduledFor: Date) => void;
}

export interface ScheduledTask {
  start(): this;
  stop(): this;
  readonly running: boolean;
  /** Resolves when no async run is in flight (call after stop() for graceful shutdown). */
  whenIdle(): Promise<void>;
  /** Next scheduled time, or null when stopped. */
  nextRun(): Date | null;
  readonly cron: CronExpression;
}

export function schedule(
  expression: string | CronExpression,
  fn: (scheduledFor: Date) => unknown,
  options?: ScheduleOptions,
): ScheduledTask;
