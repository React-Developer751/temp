import { RULES } from './engine.js';
import { SEVERITIES } from './util.js';

const COLORS = { critical: '\x1b[1;41;97m', high: '\x1b[31m', medium: '\x1b[33m', low: '\x1b[36m', dim: '\x1b[2m', bold: '\x1b[1m', reset: '\x1b[0m' };

export function countBySeverity(findings) {
  const counts = Object.fromEntries(SEVERITIES.map((s) => [s, 0]));
  for (const f of findings) counts[f.severity]++;
  return counts;
}

export function formatText(result, { color = false } = {}) {
  const paint = (name, text) => (color ? `${COLORS[name]}${text}${COLORS.reset}` : text);
  const lines = [];
  let current = null;
  for (const f of result.findings) {
    if (f.file !== current) {
      if (current !== null) lines.push('');
      lines.push(paint('bold', f.file));
      current = f.file;
    }
    lines.push(`  ${String(f.line).padStart(4)}:${String(f.column).padEnd(3)} ${paint(f.severity, f.severity.padEnd(8))} ${f.message}  ${paint('dim', f.ruleId)}`);
    if (f.snippet) lines.push(`        ${paint('dim', f.snippet)}`);
    if (f.fix) lines.push(`        ${paint('dim', `fix: ${f.fix}`)}`);
  }
  for (const e of result.errors) lines.push(`${paint('high', 'error')} ${e.file}: ${e.message}`);
  const counts = countBySeverity(result.findings);
  const parts = SEVERITIES.slice().reverse().filter((s) => counts[s] > 0).map((s) => `${counts[s]} ${s}`);
  if (lines.length > 0) lines.push('');
  lines.push(result.findings.length === 0
    ? `No issues found in ${result.filesScanned} file(s).`
    : `${result.findings.length} issue(s) (${parts.join(', ')}) in ${result.filesScanned} file(s).`);
  if (result.skipped.length > 0) lines.push(paint('dim', `Skipped ${result.skipped.length} file(s): ${result.skipped.map((s) => `${s.file} (${s.reason})`).join('; ')}`));
  return lines.join('\n');
}

export function formatJson(result) {
  return JSON.stringify({
    filesScanned: result.filesScanned,
    summary: countBySeverity(result.findings),
    findings: result.findings,
    skipped: result.skipped,
    errors: result.errors,
  }, null, 2);
}

const SARIF_LEVEL = { critical: 'error', high: 'error', medium: 'warning', low: 'note' };

/** SARIF 2.1.0, accepted by GitHub code scanning and most CI dashboards. */
export function formatSarif(result, version = '0.0.0') {
  return JSON.stringify({
    $schema: 'https://json.schemastore.org/sarif-2.1.0.json',
    version: '2.1.0',
    runs: [{
      tool: {
        driver: {
          name: 'pure-code-guard',
          version,
          rules: RULES.map((r) => ({
            id: r.id,
            shortDescription: { text: r.description },
            defaultConfiguration: { level: SARIF_LEVEL[r.severity] },
            properties: { engine: r.engine },
          })),
        },
      },
      results: result.findings.map((f) => ({
        ruleId: f.ruleId,
        level: SARIF_LEVEL[f.severity],
        message: { text: f.fix ? `${f.message} Fix: ${f.fix}` : f.message },
        locations: [{
          physicalLocation: {
            artifactLocation: { uri: f.file },
            region: { startLine: f.line, startColumn: f.column, endLine: f.endLine, endColumn: f.endColumn },
          },
        }],
        partialFingerprints: { primaryLocationLineHash: f.fingerprint },
      })),
    }],
  }, null, 2);
}
