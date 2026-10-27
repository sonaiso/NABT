import {readFile,writeFile} from 'node:fs/promises';
const files=[['/','web/index.html','text/html; charset=utf-8'],['/style.css','web/style.css','text/css; charset=utf-8'],['/app.js','web/app.js','text/javascript; charset=utf-8'],...['evidence-audit.js','evidence-sample.js','evidence-ui.js','semantic-axes.js','epistemic-contract.js','epistemic-measurement.js'].map(name=>['/'+name,'web/'+name,'text/javascript; charset=utf-8'])];
const assets={};
for(const [path,file,type] of files)assets[path]={body:await readFile(file,'utf8'),type};
const contract=await readFile('web/epistemic-contract.js','utf8');
const server=(await readFile('worker/server.mjs','utf8')).replace(/^import '\.\.\/web\/epistemic-contract\.js';\n/,'').replace(/^export /gm,'');
await writeFile('worker/index.js',contract+'\n'+server+'\nconst assets='+JSON.stringify(assets)+';\nexport default {fetch(request,env){return route(request,env,assets);}};\n');
