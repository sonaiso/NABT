// Schema/conservation check, not authentication or a linguistic proof.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {validateSemanticAxes} from '../worker/server.mjs';
const [path]=process.argv.slice(2);
if(!path)throw new Error('Provide the measured semantic-axes JSON path');
const report=JSON.parse(readFileSync(path,'utf8'));
const suite=report.semantic_axes??report;
validateSemanticAxes(suite);
const sandbox={};vm.createContext(sandbox);
vm.runInContext(readFileSync(new URL('../web/semantic-axes.js',import.meta.url),'utf8'),sandbox);
sandbox.NabtSemanticAxes.validate(suite);
console.log(JSON.stringify({schema:suite.schema,cases:suite.case_count,worker_and_ui_contract:'PASS',linguistic_proof:false}));
