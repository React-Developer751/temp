export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type EngineName = 'security' | 'crash' | 'ai';

export interface Finding {
  /** e.g. "security/xss" */
  ruleId: string;
  engine: EngineName;
  severity: Severity;
  message: string;
  /** How to fix it (not every rule has one). */
  fix?: string;
  file: string;
  /** 1-based. */
  line: number;
  column: number;
  endLine: number;
  endColumn: number;
  /** The source line, with any secret on it redacted. */
  snippet: string;
  /** Stable id (rule + file + content, not line number) for baselines / dedupe. Never contains the secret. */
  fingerprint: string;
  /** The file is ignored by git, so severity was lowered (secrets to medium, everything else to low). */
  gitIgnored?: boolean;
  /** For a secret repeated in one file: how many times that exact value appears (reported once). */
  occurrences?: number;
}

export interface ScanOptions {
  /** Which engines to run. Default: all three. */
  engines?: EngineName[];
  /** Rule ids to disable. Throws RangeError for unknown ids. */
  rulesOff?: string[];
  /** Hide findings below this severity. Default "low". */
  minSeverity?: Severity;
}

export interface ScanSourceOptions extends ScanOptions {
  /** Used for reporting and to pick code vs text handling by extension. Default "<input>". */
  filename?: string;
  /** Force how the text is treated: "code" = JS/TS (all engines), "text" = config file (secrets + hidden characters). */
  kind?: 'code' | 'text';
}

export interface ScanPathsOptions extends ScanOptions {
  /** Directory that relative paths and reported file names are relative to. Default process.cwd(). */
  cwd?: string;
  /** Extra ignore globs (node_modules, .git, dist, build, coverage, lockfiles, *.min.js are always ignored). */
  ignore?: string[];
  /** Skip files bigger than this many bytes. Default 1_000_000. */
  maxFileSize?: number;
  /** Also scan minified / bundled files (skipped by default: findings there are library internals). */
  includeMinified?: boolean;
  /** Files git ignores: "downgrade" (default), "skip", or "include" at full severity. */
  gitIgnored?: 'downgrade' | 'skip' | 'include';
}

export interface ScanResult {
  findings: Finding[];
  filesScanned: number;
  skipped: { file: string; reason: string }[];
  errors: { file: string; message: string }[];
}

export interface Rule {
  id: string;
  engine: EngineName;
  severity: Severity;
  description: string;
}

/** Scan one file's text. */
export function scanSource(source: string, options?: ScanSourceOptions): Finding[];
/** Scan files and directories (symlinks are not followed). */
export function scanPaths(paths: string | string[], options?: ScanPathsOptions): Promise<ScanResult>;
/** 'code', 'text', or null when the file type is not scanned. */
export function classify(filename: string): 'code' | 'text' | null;
/** True for minified / bundled code (huge lines, no formatting). */
export function looksMinified(text: string): boolean;

export const RULES: readonly Rule[];
export const ENGINES: readonly EngineName[];

export function formatText(result: ScanResult, options?: { color?: boolean }): string;
export function formatJson(result: ScanResult): string;
export function formatSarif(result: ScanResult, version?: string): string;

export interface Tokens {
  /** Same text as the source with comments, string/template text and regex bodies replaced by spaces. */
  masked: string;
  comments: { start: number; end: number; text: string; block: boolean }[];
  strings: { start: number; end: number; quote: string; value: string; hasExpr: boolean; tagged: boolean; exprs: { start: number; end: number }[] }[];
  regexes: { start: number; end: number; body: string; flags: string }[];
  lineStarts: number[];
  position(offset: number): { line: number; column: number };
}
export function tokenize(source: string): Tokens;
