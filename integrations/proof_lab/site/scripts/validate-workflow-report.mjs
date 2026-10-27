import {readFile} from 'node:fs/promises';
import {validateReport} from '../worker/server.mjs';
const report=JSON.parse(await readFile(process.argv[2],'utf8'));
validateReport(report,{request_id:report.request_id,code_sha:report.code_sha,payload_sha256:report.payload_sha256,mode:report.mode,workflow_request_sha256:report.workflow_request_sha256});
await globalThis.NabtWorkflowContract.verifyEnvelope(report);
console.log(JSON.stringify({passed:true,mode:report.mode,status:report.gateway_result.status,claims:report.gateway_result.claims.length,strict_language_accepted:false}));
