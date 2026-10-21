import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { ENGINES, RULES, scanSource } from './engine.js';
import { formatJson, formatSarif, formatText } from './report.js';
import { SEVERITIES, severityRank } from './util.js';
import { scanPaths } from './walk.js';

const HELP = `pure-guard - security, crash and AI-text-handling scanner for JavaScript/TypeScript (zero dependencies)

Usage: pure-guard [options] [paths...]      (default path: .   use "-" to read stdin)

Options:
  --format <text|json|sarif>   output format (default: text)
  --engine <list>              comma list of: ${ENGINES.join(', ')} (default: all)
  --min-severity <level>       hide findings below: ${SEVERITIES.join(' | ')} (default: medium; use low for advisories)
  --fail-on <level|never>      exit 1 when a finding is at least this severe (default: high)
  --ignore <glob>              extra ignore pattern, repeatable (node_modules, .git, dist... are always ignored)
  --rule-off <id[,id]>         disable rules, repeatable
  --max-file-size <bytes>      skip bigger files (default: 1000000)
  --stdin-filename <name>      file name to report/classify stdin as (default: stdin.js)
  --config <file>              JSON config (default: ./pure-guard.config.json if present)
  --include-minified           also scan minified / bundled files (skipped by default)
  --gitignored <mode>          files git ignores: downgrade (default: secrets -> medium, rest -> low) | skip | include
  --no-color                   plain output
  --list-rules                 print every rule and exit
  -h, --help                   show this help
  -v, --version                print version

Suppress one finding in code:   // pure-guard-ignore security/xss
Suppress a rule for a whole file: /* pure-guard-ignore-file crash/empty-catch */

Exit codes: 0 clean, 1 findings at/above --fail-on, 2 usage or I/O error`;

const CONFIG_KEYS = new Set(['ignore', 'ruleOff', 'engines', 'minSeverity', 'failOn', 'maxFileSize', 'format', 'includeMinified', 'gitIgnored']);

class UsageError extends Error {}

async function readText(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  return Buffer.concat(chunks).toString('utf8');
}

async function loadConfig(cwd, explicit) {
  const file = resolve(cwd, explicit ?? 'pure-guard.config.json');
  let text;
  try {
    text = await readFile(file, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT' && !explicit) return {};
    throw new UsageError(`cannot read config ${file}: ${error.message}`);
  }
  let config;
  try {
    config = JSON.parse(text);
  } catch (error) {
    throw new UsageError(`invalid JSON in ${file}: ${error.message}`);
  }
  if (config === null || typeof config !== 'object' || Array.isArray(config)) throw new UsageError(`${file} must contain a JSON object`);
  for (const key of Object.keys(config)) if (!CONFIG_KEYS.has(key)) throw new UsageError(`unknown key "${key}" in ${file} (allowed: ${[...CONFIG_KEYS].join(', ')})`);
  return config;
}

const list = (value) => (value === undefined ? [] : [value].flat().flatMap((v) => String(v).split(',')).map((v) => v.trim()).filter(Boolean));

/**
 * Run the CLI. Returns the exit code instead of exiting, so it can be tested.
 * @param {string[]} argv
 * @param {{ stdout?: { write(s: string): unknown, isTTY?: boolean }, stderr?: { write(s: string): unknown }, stdin?: AsyncIterable<Buffer | string>, cwd?: string, env?: Record<string, string | undefined> }} [io]
 */
export async function run(argv, io = {}) {
  const { stdout = process.stdout, stderr = process.stderr, stdin = process.stdin, cwd = process.cwd(), env = process.env } = io;
  try {
    let parsed;
    try {
      parsed = parseArgs({
        args: argv,
        allowPositionals: true,
        options: {
          format: { type: 'string' },
          engine: { type: 'string', multiple: true },
          'min-severity': { type: 'string' },
          'fail-on': { type: 'string' },
          ignore: { type: 'string', multiple: true },
          'rule-off': { type: 'string', multiple: true },
          'max-file-size': { type: 'string' },
          'stdin-filename': { type: 'string' },
          config: { type: 'string' },
          'include-minified': { type: 'boolean' },
          gitignored: { type: 'string' },
          'no-color': { type: 'boolean' },
          'list-rules': { type: 'boolean' },
          help: { type: 'boolean', short: 'h' },
          version: { type: 'boolean', short: 'v' },
        },
      });
    } catch (error) {
      throw new UsageError(error.message);
    }
    const { values, positionals } = parsed;

    const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
    if (values.help) { stdout.write(`${HELP}\n`); return 0; }
    if (values.version) { stdout.write(`${pkg.version}\n`); return 0; }
    if (values['list-rules']) {
      stdout.write(`${RULES.map((r) => `${r.id.padEnd(34)} ${r.severity.padEnd(9)} ${r.description}`).join('\n')}\n`);
      return 0;
    }

    const config = await loadConfig(cwd, values.config);
    const format = values.format ?? config.format ?? 'text';
    if (!['text', 'json', 'sarif'].includes(format)) throw new UsageError(`--format must be text, json or sarif (got "${format}")`);
    const failOn = values['fail-on'] ?? config.failOn ?? 'high';
    if (failOn !== 'never' && !SEVERITIES.includes(failOn)) throw new UsageError(`--fail-on must be one of ${SEVERITIES.join(', ')}, never (got "${failOn}")`);
    const maxRaw = values['max-file-size'] ?? config.maxFileSize;
    const maxFileSize = maxRaw === undefined ? undefined : Number(maxRaw);
    if (maxFileSize !== undefined && !(Number.isInteger(maxFileSize) && maxFileSize > 0)) throw new UsageError('--max-file-size must be a positive integer');

    const options = {
      cwd,
      engines: values.engine ? list(values.engine) : list(config.engines).length > 0 ? list(config.engines) : undefined,
      minSeverity: values['min-severity'] ?? config.minSeverity ?? 'medium',
      ignore: [...list(config.ignore), ...list(values.ignore)],
      rulesOff: [...list(config.ruleOff), ...list(values['rule-off'])],
      maxFileSize,
      includeMinified: values['include-minified'] ?? config.includeMinified,
      gitIgnored: values.gitignored ?? config.gitIgnored,
    };
    for (const key of Object.keys(options)) if (options[key] === undefined) delete options[key];

    const paths = positionals.length > 0 ? positionals : ['.'];
    let result;
    if (paths.includes('-')) {
      const filename = values['stdin-filename'] ?? 'stdin.js';
      const findings = scanSource(await readText(stdin), { ...options, filename });
      result = { findings, filesScanned: 1, skipped: [], errors: [] };
      const rest = paths.filter((p) => p !== '-');
      if (rest.length > 0) {
        const more = await scanPaths(rest, options);
        result = { findings: [...findings, ...more.findings], filesScanned: 1 + more.filesScanned, skipped: more.skipped, errors: more.errors };
      }
    } else {
      result = await scanPaths(paths, options);
    }

    const color = !values['no-color'] && !env.NO_COLOR && Boolean(stdout.isTTY);
    const output = format === 'json' ? formatJson(result) : format === 'sarif' ? formatSarif(result, pkg.version) : formatText(result, { color });
    stdout.write(`${output}\n`);

    if (result.errors.length > 0) {
      if (format !== 'text') for (const e of result.errors) stderr.write(`pure-guard: ${e.file}: ${e.message}\n`);
      return 2;
    }
    if (failOn === 'never') return 0;
    return result.findings.some((f) => severityRank(f.severity) >= severityRank(failOn)) ? 1 : 0;
  } catch (error) {
    if (error instanceof UsageError || error instanceof RangeError) {
      stderr.write(`pure-guard: ${error.message}\nRun "pure-guard --help" for usage.\n`);
      return 2;
    }
    throw error;
  }
}
