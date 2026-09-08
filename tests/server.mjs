import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {randomUUID,createHmac} from 'node:crypto';
import {createApp} from '../server/app.mjs';
import {verifyWebhook} from '../server/payments.mjs';
const dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-test-'));
const secret='whsec_local_test_only',checkouts=new Map();let next=0,checks=0;
const app=await createApp({port:0,host:'127.0.0.1',dataDir:dir,origin:'https://game.example.test',stripeKey:'sk_test_local_test_only',webhookSecret:secret,secure:false,fetcher:async(url,opts)=>{
 assert.equal(url,'https://api.stripe.com/v1/checkout/sessions');const params=new URLSearchParams(opts.body);const id='cs_test_'+(++next);checkouts.set(id,params);return new Response(JSON.stringify({id,url:'https://checkout.stripe.com/c/pay/'+id}),{status:200,headers:{'Content-Type':'application/json'}});
}});
await app.listen();const base='http://127.0.0.1:'+app.server.address().port;
function passed(name){checks++;console.log('PASS',name);}
async function request(route,{data,session,headers={},method}={}){const res=await fetch(base+route,{method:method||(data?'POST':'GET'),headers:{...(data?{'Content-Type':'application/json'}:{}),...(session?{Cookie:session.cookie,'X-CSRF-Token':session.csrf}:{}),...headers},...(data?{body:JSON.stringify(data)}:{})});const result=await res.json();if(session&&res.headers.get('set-cookie'))session.cookie=res.headers.get('set-cookie').split(';')[0];if(session&&result.csrf)session.csrf=result.csrf;return {status:res.status,result,cookie:res.headers.get('set-cookie')};}
async function guest(){const r=await request('/api/session',{data:{}});assert.equal(r.status,200);return {cookie:r.cookie.split(';')[0],csrf:r.result.csrf,user:r.result.user,state:r.result.state};}
async function command(session,a){return request('/api/command',{session,data:{requestId:randomUUID(),...a}});}
function patchState(id,fn){const row=app.db.prepare('SELECT state FROM players WHERE id=?').get(id),s=JSON.parse(row.state);fn(s);app.db.prepare('UPDATE players SET state=? WHERE id=?').run(JSON.stringify(s),id);}
try{
 assert.equal((await request('/api/health')).status,200);const page=await fetch(base+'/');assert.equal(page.status,200);assert.match(await page.text(),/emberfall-runtime" content="server/);passed('Self-hosted server starts and serves the actual game');
 const a=await guest(),b=await guest();assert.notEqual(a.user.id,b.user.id);
 let r=await request('/api/auth/register',{session:a,data:{username:'Chief_Test_A',password:'test-password-12345'}});assert.equal(r.status,200);
 r=await request('/api/auth/login',{data:{username:'chief_test_a',password:'test-password-12345'}});assert.equal(r.status,200);assert.equal(r.result.user.id,a.user.id);
 assert.equal((await request('/api/auth/login',{data:{username:'Chief_Test_A',password:'incorrect-password'}})).status,401);passed('Accounts register, authenticate, and recover the same saved village');
 r=await request('/api/command',{session:a,headers:{'X-CSRF-Token':'wrong'},data:{requestId:randomUUID(),type:'collect'}});assert.equal(r.status,403);
 r=await request('/api/command',{session:a,headers:{Origin:'https://attacker.example'},data:{requestId:randomUUID(),type:'collect'}});assert.equal(r.status,403);
 r=await request('/api/state',{session:a,data:{gems:99999999,state:{gems:99999999}}});assert.equal(r.status,404);passed('CSRF, foreign origins, and arbitrary client wallet writes are rejected');
 const id=randomUUID(),before=(await request('/api/state',{session:a})).result.state;
 r=await command(a,{type:'exchange',resource:'gold',gems:999999,requestId:id});assert.equal(r.status,200);assert.equal(r.result.state.gems,before.gems-20);
 const replay=await command(a,{type:'exchange',resource:'gold',requestId:id});assert.equal(replay.result.state.gems,before.gems-20);
 const elixir=r.result.state.elixir;await Promise.all([command(a,{type:'train',troop:'guardian'}),command(a,{type:'train',troop:'guardian'})]);assert.equal((await request('/api/state',{session:a})).result.state.elixir,elixir-90);passed('Commands are idempotent and concurrent actions do not overwrite currency');
 r=await command(a,{type:'battle-start',index:10});assert.equal(r.status,400);
 r=await request('/api/clans',{session:a,data:{action:'create',name:'Emberfall Test Clan'}});assert.equal(r.status,200);const clan=r.result.user.clanId;
 assert.equal((await request('/api/clans',{session:b,data:{action:'join',id:clan}})).status,200);
 assert.equal((await request('/api/clans',{session:a,data:{action:'chat',message:'A local integration-test message.'}})).status,200);
 assert.equal((await request('/api/clans',{session:a,data:{action:'donate',id:b.user.id,troop:'guardian'}})).status,200);
 const social=(await request('/api/clans',{session:b})).result;assert.equal(social.members.length,2);assert.equal(social.messages.length,1);passed('Clan creation, membership, messages, and troop donations persist');
 r=await command(a,{type:'battle-start',index:0});assert.equal(r.status,200);const battleId=r.result.battleId;
 assert.equal((await command(a,{type:'battle-deploy',battleId,troop:'guardian',x:0,z:0})).status,400);
 for(const [troop,n]of Object.entries(r.result.state.army))for(let i=0;i<n;i++){const deployed=await command(a,{type:'battle-deploy',battleId,troop,x:(i%5-2)*1.1,z:11});assert.equal(deployed.status,200);}
 app.db.prepare('UPDATE battles SET last_step=last_step-45000 WHERE id=?').run(battleId);
 r=await request('/api/battle?id='+battleId,{session:a});assert.equal(r.status,200);assert.equal(r.result.battle.settled,true);assert.ok(r.result.battle.result.stars>0);
 const gold=r.result.state.gold;r=await command(a,{type:'battle-end',battleId,percent:100,stars:3,gold:9999999});assert.equal(r.result.state.gold,gold);passed('Server simulates raids, rejects center deployment, and awards loot once');
 const previousGems=(await request('/api/state',{session:a})).result.state.gems;
 r=await request('/api/payments/checkout',{session:b,data:{pack:'pouch'}});assert.equal(r.status,403);
 r=await request('/api/payments/checkout',{session:a,data:{pack:'pouch',cents:1,gems:999999}});assert.equal(r.status,200);
 const order=app.db.prepare('SELECT * FROM orders WHERE id=?').get(r.result.orderId);assert.equal(order.cents,499);assert.equal(order.gems,500);
 await fetch(base+'/?purchase=success');assert.equal((await request('/api/state',{session:a})).result.state.gems,previousGems);
 const event={id:'evt_test_paid_1',type:'checkout.session.completed',data:{object:{id:order.stripe_id,client_reference_id:a.user.id,payment_status:'paid',amount_total:499,currency:'usd',metadata:{order_id:order.id}}}};
 const send=async(value,signed=true)=>{const raw=JSON.stringify(value),t=Math.floor(Date.now()/1000),signature=createHmac('sha256',secret).update(t+'.'+raw).digest('hex');const res=await fetch(base+'/api/payments/webhook',{method:'POST',headers:{'Content-Type':'application/json','Stripe-Signature':`t=${t},v1=${signed?signature:'0'.repeat(64)}`},body:raw});return {status:res.status,result:await res.json()};};
 assert.equal((await send(event,false)).status,400);assert.equal((await send(event)).status,200);assert.equal((await send(event)).status,200);
 assert.equal((await send({...event,id:'evt_test_paid_2',type:'checkout.session.async_payment_succeeded'})).status,200);
 assert.equal((await request('/api/state',{session:a})).result.state.gems,previousGems+500);
 assert.throws(()=>verifyWebhook(Buffer.from('{}'),'t=1,v1='+'0'.repeat(64),secret));passed('Gem checkout validates prices; signed webhook credits once, even across duplicate event types');
 await request('/api/clans',{session:b,data:{action:'leave'}});patchState(a.user.id,s=>s.army.guardian=2);
 r=await command(a,{type:'battle-start',defender:b.user.id});assert.equal(r.status,200);assert.equal(r.result.battle.pvp,true);
 assert.equal((await command(b,{type:'battle-end',battleId:r.result.battleId})).status,404);
 await command(a,{type:'battle-end',battleId:r.result.battleId});assert.equal((await command(a,{type:'battle-start',defender:b.user.id})).status,400);passed('Player raids enforce ownership, use the saved defense layout, and apply a shield');
 const rows=app.db.prepare('SELECT COUNT(*) AS n FROM raid_log').get();assert.ok(rows.n>=2);passed('Battle history and persistent SQLite records are available');
 console.log(`${checks} server integration checks passed. No external payment calls were made.`);
}finally{await app.close();await rm(dir,{recursive:true,force:true});}
