import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {Readable} from 'node:stream';
import {generateKeyPairSync,sign,createHash,createHmac} from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import {createApp} from '../server/app.mjs';
import {renderScale} from '../dist/graphics.js';

// Exercise the real HTTP handler without opening a listening socket.
const dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-oauth-'));
const {privateKey,publicKey}=generateKeyPairSync('rsa',{modulusLength:2048});
const jwk={...publicKey.export({format:'jwk'}),kid:'fixture-key',use:'sig',alg:'RS256'};
let app,checks=0,codeCounter=0;const codes=new Map();
const response=d=>new Response(JSON.stringify(d),{headers:{'Content-Type':'application/json'}});
const appSecret='facebook-fixture-secret',googleId='google-fixture-client';
const fakeFetch=async(value,options={})=>{
 const u=new URL(value),params=new URLSearchParams(options.body);
 assert.equal(options.redirect,'error');
 if(u.href==='https://www.googleapis.com/oauth2/v3/certs')return response({keys:[jwk]});
 if(u.href==='https://oauth2.googleapis.com/token'){
  assert.equal(params.get('client_secret'),'google-fixture-secret');const fixture=codes.get(params.get('code'));assert.ok(fixture);
  assert.equal(createHash('sha256').update(params.get('code_verifier')).digest('base64url'),fixture.challenge);assert.equal(params.get('redirect_uri'),'https://kingdom.example/api/auth/oauth/google/callback');
  const now=Math.floor(Date.now()/1000),claims={iss:'https://accounts.google.com',aud:googleId,sub:fixture.sub,nonce:fixture.nonce,iat:now,exp:now+3600,name:'Fixture Chief',...fixture.claims};
  const header=Buffer.from(JSON.stringify({alg:'RS256',kid:'fixture-key'})).toString('base64url'),payload=Buffer.from(JSON.stringify(claims)).toString('base64url');
  let signature=sign('RSA-SHA256',Buffer.from(header+'.'+payload),privateKey).toString('base64url');if(fixture.corrupt)signature='A'+signature.slice(1);
  return response({id_token:header+'.'+payload+'.'+signature});
 }
 if(u.pathname==='/v25.0/oauth/access_token')return response({access_token:'fb-'+params.get('code')});
 if(u.pathname==='/v25.0/debug_token') {assert.equal(options.headers.Authorization,'Bearer facebook-fixture-app|'+appSecret);const f=codes.get(u.searchParams.get('input_token').slice(3));return response({data:{is_valid:true,app_id:'facebook-fixture-app',user_id:f.sub,expires_at:Math.floor(Date.now()/1000)+3600,...f.claims}});}
 if(u.pathname==='/v25.0/me') {const token=options.headers.Authorization.slice(7);assert.equal(u.searchParams.get('appsecret_proof'),createHmac('sha256',appSecret).update(token).digest('hex'));return response({id:codes.get(token.slice(3)).sub,name:'Facebook Chief'});}
 throw new Error('Unexpected provider URL: '+u.origin+u.pathname);
};
app=await createApp({dataDir:dir,secure:true,origin:'https://kingdom.example',fetcher:fakeFetch,oauth:{googleId,googleSecret:'google-fixture-secret',facebookId:'facebook-fixture-app',facebookSecret:appSecret}});
async function call(route,{data,session,headers={}}={}) {
 const req=Readable.from(data===undefined?[]:[Buffer.from(JSON.stringify(data))]);req.url=route;req.method=data===undefined?'GET':'POST';
 req.headers={host:'kingdom.example',origin:'https://kingdom.example',...(data!==undefined?{'content-type':'application/json'}:{}),...(session?{cookie:session.cookie,'x-csrf-token':session.csrf}:{}),...headers};
 req.socket={remoteAddress:'127.0.0.'+(++codeCounter)};
 return new Promise(resolve=>{
  const out={headers:{},status:200};
  const res={headersSent:false,setHeader(k,v){out.headers[k.toLowerCase()]=v},writeHead(status,headers){this.headersSent=true;out.status=status;for(const[k,v]of Object.entries(headers))out.headers[k.toLowerCase()]=v;},end(value){let body;try{body=JSON.parse(String(value))}catch{body=String(value)};out.data=body;if(session&&out.headers['set-cookie'])session.cookie=out.headers['set-cookie'].split(';')[0];if(session&&body.csrf)session.csrf=body.csrf;resolve(out)}};
  app.server.emit('request',req,res);
 });
}
async function guest(){const r=await call('/api/session',{data:{}});assert.equal(r.status,200);return{cookie:r.headers['set-cookie'].split(';')[0],csrf:r.data.csrf,user:r.data.user};}
const start=async(session,provider='google',mode='signin')=>{const r=await call('/api/auth/oauth/start',{session,data:{provider,mode}});assert.equal(r.status,200,JSON.stringify(r.data));return r.data;};
const poll=(session,a,extra={})=>call('/api/oauth/poll',{session,data:{id:a.id,pollToken:a.pollToken,...extra}});
async function callback(a,{sub='google-person-a',claims={},corrupt=false}={}){
 const u=new URL(a.authorizationUrl),provider=u.hostname==='accounts.google.com'?'google':'facebook',code='code-'+(++codeCounter);
 codes.set(code,{sub,claims,corrupt,nonce:u.searchParams.get('nonce'),challenge:u.searchParams.get('code_challenge')});
 return call('/api/auth/oauth/'+provider+'/callback?state='+u.searchParams.get('state')+'&code='+code);
}
const pass=name=>{checks++;console.log('PASS',name)};
try {
 const a=await guest(),b=await guest();
 assert.equal((await call('/api/config')).data.oauth.google.enabled,true);
 assert.equal((await call('/api/auth/oauth/start',{session:a,data:{provider:'google',mode:'signin'},headers:{'x-csrf-token':'fake'}})).status,403);
 assert.equal((await call('/api/auth/oauth/start',{session:a,data:{provider:'google',mode:'signin'},headers:{origin:'https://attacker.example'}})).status,403);
 assert.equal((await call('/api/auth/oauth/start',{session:a,data:{provider:'attacker',mode:'signin'}})).status,503);pass('Provider start requires authenticated CSRF, same origin and a configured fixed provider');
 let flow=await start(a),before={...a};
 assert.equal(new URL(flow.authorizationUrl).searchParams.get('code_challenge_method'),'S256');
 const stored=app.db.prepare('SELECT * FROM oauth_attempts WHERE id=?').get(flow.id);assert.notEqual(stored.state_hash,new URL(flow.authorizationUrl).searchParams.get('state'));assert.notEqual(stored.poll_hash,flow.pollToken);
 assert.equal((await poll(b,flow)).status,410);assert.equal((await poll(a,{...flow,pollToken:'x'.repeat(43)})).status,410);assert.equal((await poll(a,flow)).data.status,'pending');pass('State and polling secrets are hashed and the handoff is bound to the initiating session');
 let r=await callback(flow);assert.equal(r.status,200);assert.equal(r.headers['set-cookie'],undefined);assert.match(r.data,/Return to Emberfall/);assert.equal((await callback(flow)).status,400);
 r=await poll(a,flow);assert.equal(r.status,200,JSON.stringify(r.data));assert.equal(r.data.user.id,a.user.id);assert.equal(r.data.user.registered,true);assert.equal(r.data.user.hasPassword,false);assert.deepEqual(r.data.user.providers,['google']);assert.equal((await call('/api/state',{session:before})).status,401);assert.equal((await poll(a,flow)).status,410);pass('Verified Google login saves the guest village, rotates cookies and rejects callback/claim replay');
 const newDevice=await guest();flow=await start(newDevice);await callback(flow);r=await poll(newDevice,flow);assert.equal(r.data.user.id,a.user.id);assert.equal(r.data.state.gems,100);pass('Signing in on another device loads the original village without copying client wallets');
 for(const claims of [{aud:'wrong-client'},{nonce:'wrong-nonce'},{exp:1},{iss:'https://attacker.example'}]) {
  const g=await guest();flow=await start(g);assert.equal((await callback(flow,{claims})).status,400);assert.equal((await poll(g,flow)).status,401);
 }
 const bad=await guest();flow=await start(bad);assert.equal((await callback(flow,{corrupt:true})).status,400);pass('Google rejects forged signatures, wrong audience, wrong nonce, expiry and foreign issuer');
 flow=await start(a,'facebook','link');assert.equal((await callback(flow,{sub:'fb-person-a'})).status,200);r=await poll(a,flow);assert.deepEqual(r.data.user.providers,['facebook','google']);assert.equal(r.data.user.id,a.user.id);pass('Facebook tokens are checked for app identity and proof before explicitly linking the current village');
 const c=await guest();flow=await start(c,'facebook');await callback(flow,{sub:'fb-person-b'});await poll(c,flow);
 flow=await start(c,'google','link');await callback(flow);assert.equal((await poll(c,flow)).status,409);assert.equal(app.db.prepare("SELECT player_id FROM auth_identities WHERE provider='google' AND subject='google-person-a'").get().player_id,a.user.id);pass('Linking cannot take over another village or silently merge accounts');
 const fbBad=await guest();flow=await start(fbBad,'facebook');assert.equal((await callback(flow,{sub:'fb-person-bad',claims:{app_id:'another-app'}})).status,400);pass('Facebook rejects a token issued to another app');
 const expired=await guest();flow=await start(expired);app.db.prepare('UPDATE oauth_attempts SET expires_at=1 WHERE id=?').run(flow.id);assert.equal((await callback(flow)).status,400);assert.equal((await poll(expired,flow)).status,410);pass('Expired OAuth attempts cannot be resumed or claimed');
 const cancelled=await guest();flow=await start(cancelled);assert.equal((await poll(cancelled,flow,{cancel:true})).data.status,'cancelled');assert.equal((await callback(flow)).status,400);pass('Cancelled attempts invalidate their callback and cannot mutate an account');
 const loggedOut=await guest();flow=await start(loggedOut);await call('/api/auth/logout',{session:loggedOut,data:{}});assert.equal((await callback(flow)).status,400);pass('Provider callbacks cannot revive a revoked game session');
 assert.ok(renderScale('ultra',4000,3000,3,8192)**2*4000*3000<=10000001);assert.equal(renderScale('high',800,400,2,8192),2);assert.ok(renderScale('ultra',9000,5000,3,8192)*9000<=8192);pass('HD resolution obeys pixel and GPU texture limits without blurring normal Retina screens');
 console.log(checks+' OAuth and graphics safety checks passed.');
} finally {await app.close();await rm(dir,{recursive:true,force:true});}
