import {readFile,writeFile} from 'node:fs/promises';
const files=[['/','web/index.html','text/html; charset=utf-8'],['/style.css','web/style.css','text/css; charset=utf-8'],['/app.js','web/app.js','text/javascript; charset=utf-8'],...['transport-contract.js','workflow-contract.js','workflow-ui.js','legacy-authority.js','evidence-audit.js','evidence-sample.js','evidence-ui.js','semantic-axes.js','epistemic-contract.js','epistemic-measurement.js','contextual-contract.js','contextual-reference.js'].map(name=>['/'+name,'web/'+name,'text/javascript; charset=utf-8'])];
const assets={};
for(const [path,file,type] of files)assets[path]={body:await readFile(file,'utf8'),type};
const contract=await readFile('web/transport-contract.js','utf8')+'\n'+await readFile('web/workflow-contract.js','utf8')+'\n'+await readFile('web/legacy-authority.js','utf8')+'\n'+await readFile('web/epistemic-contract.js','utf8')+'\n'+await readFile('web/contextual-contract.js','utf8');
const server=(await readFile('worker/server.mjs','utf8')).replace(/^import '\.\.\/web\/(?:(?:epistemic|contextual)-contract|legacy-authority|workflow-contract|transport-contract)\.js';\n/gm,'').replace(/^export /gm,'');
await writeFile('worker/index.js',contract+'\n'+server+'\nconst assets='+JSON.stringify(assets)+';\nexport default {fetch(request,env){return route(request,env,assets);}};\n');
