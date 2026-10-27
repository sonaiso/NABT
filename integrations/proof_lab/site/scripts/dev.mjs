import http from 'node:http';
import {stat} from 'node:fs/promises';
const args=process.argv.slice(2),port=Number(args[args.indexOf('--port')+1]||4173),host=args.includes('--host')?args[args.indexOf('--host')+1]:'0.0.0.0';
http.createServer(async(req,res)=>{
 try{
  const parts=[];let bytes=0;for await(const part of req){bytes+=part.length;if(bytes>32768){res.writeHead(413);res.end();return;}parts.push(part);}
  const source=await stat('worker/index.js');const worker=await import('../worker/index.js?v='+source.mtimeMs);
  const method=req.method;const request=new Request('http://'+req.headers.host+req.url,{method,headers:req.headers,...(['GET','HEAD'].includes(method)?{}:{body:Buffer.concat(parts)})});
  const response=await worker.default.fetch(request,{});res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
 }catch{res.writeHead(500);res.end('Preview unavailable');}
}).listen(port,host,()=>console.log('NABT preview listening on '+port));
