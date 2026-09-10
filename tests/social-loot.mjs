import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {randomUUID} from 'node:crypto';
import {createApp} from '../server/app.mjs';
import {playerCode} from '../server/social.mjs';
import * as M from '../dist/model.js';
import * as R from '../dist/raids.js';
assert.equal(playerCode(1),'EFAA00001');assert.equal(playerCode(99999),'EFAA99999');assert.equal(playerCode(100000),'EFAB00001');assert.equal(playerCode(26*99999+1),'EFBA00001');
const attacker=M.initialState(),defender=M.initialState();defender.gold=10000;defender.elixir=8000;const b=R.configureBattle(M.createBattle(attacker,0),{id:'test',name:'Test',state:defender});
for(const x of b.buildings)if(!['hall','storage','mine','well','drill'].includes(x.type))x.hp=0;
assert.equal(R.earnedLoot(b).gold,0);const hall=b.buildings.find(x=>x.type==='hall');hall.hp=hall.maxHp/2;assert.equal(R.earnedLoot(b).gold,Math.floor(hall.loot.gold/2));const storage=b.buildings.find(x=>x.type==='storage');storage.hp=0;assert.equal(R.earnedLoot(b).gold,Math.floor(hall.loot.gold/2+storage.loot.gold));for(const x of b.buildings)x.hp=0;assert.deepEqual(R.earnedLoot(b),R.availableLoot(defender));assert.ok(Math.abs(M.producerRate({type:'mine',level:1})*60-10.2)<1e-9);
const low=M.initialState(),high=M.initialState();high.buildings[0].level=10;assert.equal(R.matchAllowed(low,high),false);low.glory=1100;high.glory=1150;assert.equal(R.matchAllowed(low,high),true);high.glory=999;assert.equal(R.matchAllowed(low,high),false);for(let i=0;i<30;i++){const bot=R.botVillage(M.initialState());assert.ok(bot.hall<=3);}
console.log('PASS Stable Player ID rollover, targeted resource loot, slower production and trophy matchmaking');
const dir=await mkdtemp(tmpdir()+'/ember-social-'),app=await createApp({port:0,dataDir:dir,backupIntervalMs:0});await app.listen();const base='http://127.0.0.1:'+app.server.address().port;
async function call(route,u,data){const r=await fetch(base+'/api'+route,{method:data?'POST':'GET',headers:{...(data?{'Content-Type':'application/json'}:{}),...(u?{Cookie:u.cookie,'X-CSRF-Token':u.csrf}:{})},...(data?{body:JSON.stringify(data)}:{})});const body=await r.json();return {status:r.status,body,cookie:r.headers.get('set-cookie')};}
async function guest(){const r=await call('/session',null,{});assert.equal(r.status,200);return {...r.body.user,cookie:r.cookie.split(';')[0],csrf:r.body.csrf};}
try{
 const a=await guest(),c=await guest(),d=await guest();assert.equal(a.code,'EFAA00001');assert.equal(c.code,'EFAA00002');assert.equal(a.name,a.code);assert.equal((await call('/social',null)).status,401);
 let r=await call('/social?q='+c.code,a);assert.equal(r.body.players[0].id,c.id);
 assert.equal((await call('/social',a,{action:'request',target:c.code})).status,200);assert.equal((await call('/social',a,{action:'request',target:c.code})).status,400);assert.equal((await call('/social',d,{action:'accept',target:a.code})).status,400);assert.equal((await call('/social',c,{action:'accept',target:a.code})).status,200);
 assert.equal((await call('/social',a)).body.friends[0].status,'accepted');
 r=await call('/clans',a,{action:'create',name:'Valley Keep'});assert.equal(r.status,200);const clanId=r.body.user.clanId;r=await call('/social?q=Valley',a);const clan=r.body.clans[0];assert.match(clan.code,/^\d{10}$/);assert.equal((await call('/social?q='+clan.code,a)).body.clans[0].id,clanId);
 assert.equal((await call('/social',d,{action:'invite',target:c.code})).status,400);assert.equal((await call('/social',a,{action:'invite',target:c.code})).status,200);assert.equal((await call('/social',d,{action:'join-invite',clanId})).status,400);assert.equal((await call('/social',c,{action:'join-invite',clanId})).status,200);assert.equal((await call('/social',c)).body.profile.clanId,clanId);
 r=await call('/command',a,{type:'war-start',requestId:randomUUID()});assert.equal(r.status,200,JSON.stringify(r.body));let war=(await call('/frontiers',a)).body.wars[0];assert.equal(war.botClan,true);assert.equal(war.rosters.a.length,war.rosters.b.length);assert.ok(war.rosters.b.every((p,i)=>Math.abs(p.hall-war.rosters.a[i].hall)<=1));war.readyAt=Date.now()-1;app.db.prepare('UPDATE wars SET state=? WHERE id=?').run(JSON.stringify(war),war.id);war=(await call('/frontiers',a)).body.wars[0];assert.ok(war.botPlayed);const attacks=war.attacks.length;assert.ok(attacks>0);assert.equal((await call('/frontiers',a)).body.wars[0].attacks.length,attacks);
 const saved=await call('/auth/register',a,{username:'ValleyChief',password:'a-long-test-password'});assert.equal(saved.status,200);const signed=await call('/auth/login',null,{username:a.code,password:'a-long-test-password'});assert.equal(signed.status,200);assert.equal(signed.body.user.code,a.code);assert.equal(signed.body.user.registered,true);
 console.log('PASS Authenticated profiles, player/clan searches, friend consent, leader invitations and level-matched bot clan wars');
}finally{await app.close();await rm(dir,{recursive:true,force:true});}
