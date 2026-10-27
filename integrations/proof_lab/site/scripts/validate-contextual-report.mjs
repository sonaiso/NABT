// Structural and digest consistency only; imported records are not authenticated.
import { readFileSync } from 'node:fs';
import { validateContextualReference, validateReport } from '../worker/server.mjs';
const [path] = process.argv.slice(2);
if (!path) throw new Error('Provide the contextual-reference JSON path');
const report = JSON.parse(readFileSync(path, 'utf8'));
const suite = report.contextual_reference ?? report;
if (report.contextual_reference) validateReport(report, report);
validateContextualReference(suite);
await globalThis.NabtContextualContract.verifyIntegrity(suite);
console.log(JSON.stringify({ schema: suite.schema, cases: suite.cases.length, shared_worker_ui_contract: 'PASS', integrity: 'PASS', all_cases_native_checked: suite.all_cases_native_checked, source_authentication: false, tawatur_evaluated: false, whole_arabic_complete: false }));
