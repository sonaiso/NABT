// Shared Worker/browser contract and hash consistency, never authentication.
import { readFileSync } from 'node:fs';
import { validateEpistemicMeasurement, validateReport } from '../worker/server.mjs';
const [path] = process.argv.slice(2);
if (!path) throw new Error('Provide the measured epistemic JSON path');
const report = JSON.parse(readFileSync(path, 'utf8'));
const suite = report.epistemic_measurement ?? report;
if (report.epistemic_measurement) validateReport(report, report);
validateEpistemicMeasurement(suite);
await globalThis.NabtEpistemicContract.verifyIntegrity(suite);
console.log(JSON.stringify({ schema: suite.schema, cases: suite.cases.length, shared_worker_ui_contract: 'PASS', integrity: 'PASS', all_cases_native_checked: suite.all_cases_native_checked, source_authentication: false, whole_arabic_complete: false }));
