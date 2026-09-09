import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {Readable} from 'node:stream';
import {randomUUID,createHash} from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import * as M from '../dist/model.js';
import * as R from '../dist/raids.js';
import {buildingModel,makeUnit,World} from '../dist/world.js';
import {heroPortrait} from '../dist/portraits.js';
import {createApp} from '../server/app.mjs';
const now=Date.now(),fresh=()=>{const s=M.initialState(now);M.advance(s,now);return s;};
let checks=0;const pass=name=>{checks++;console.log('PASS',name);};
assert.deepEqual(R.availableLoot({gold:1234567,elixir:987654,dark:12345,gems:9999}),{gold:123456,elixir:98765,dark:1234});
pass('Raid loot is exactly a 10% maximum of each stored resource, without fixed caps or stealable gems');
{
 const attacker=fresh(),defender=fresh();attacker.gold=M.capacity(attacker)-7;attacker.elixir=M.capacity(attacker)-11;defender.gold=123456;defender.elixir=234567;defender.dark=9001;
 const before={...defender},b=R.configureBattle(M.createBattle(attacker,0),{id:'d',name:'Defender',state:defender});b.id='loot-test';R.reserveLoot(defender,b);b.started=true;for(const building of b.buildings)building.hp=0;
 const r=M.settleBattle(attacker,b);assert.equal(r.gold,7);assert.equal(r.elixir,11);assert.equal(r.dark,900);R.settleDefender(defender,b,r,now);
 assert.equal(defender.gold,before.gold-7);assert.equal(defender.elixir,before.elixir-11);assert.equal(defender.dark,before.dark-900);
 assert.equal(defender.gems,before.gems);assert.equal(M.settleBattle(attacker,b),r);assert.equal(attacker.raids.history.length,1);
 pass('Attacker storage limits and defender refunds conserve actual transferred loot, including overflow and replay');
}
{
 const s=fresh();s.gems=1000;const balance=s.gems;
 assert.ok(M.applyAction(s,{type:'shield-buy',shield:'12h',gems:0,duration:R.WEEK},now).ok);assert.equal(s.gems,balance-100);assert.equal(s.shieldUntil,now+12*3600000);
 assert.ok(M.applyAction(s,{type:'shield-buy',shield:'free'},now).error);s.shieldUntil=now+R.WEEK;
 assert.ok(M.applyAction(s,{type:'shield-buy',shield:'1d'},now).error);assert.equal(s.gems,balance-100);
 const b=R.createBotBattle(s,()=>.5,now);R.startAttack(s,b,now);assert.equal(s.shieldUntil,now+R.WEEK);b.started=true;R.startAttack(s,b,now);assert.equal(s.shieldUntil,0);
 pass('Shield prices and duration are authoritative, stacking is capped, and only deployment breaks protection');
}
{
 const s=fresh(),box=s.obstacles.find(o=>o.type==='gem-box'),gems=s.gems;
 assert.ok(box);assert.ok(M.applyAction(s,{type:'clear',id:box.id},now).ok);assert.ok(M.applyAction(s,{type:'clear',id:box.id},now).error);
 M.advance(s,now+12001);assert.equal(s.gems,gems+25);const due=s.nextGemBoxAt;M.advance(s,due-1);assert.ok(!s.obstacles.some(o=>o.type==='gem-box'));M.advance(s,due);assert.equal(s.obstacles.filter(o=>o.type==='gem-box').length,1);M.advance(s,due+3*R.WEEK);assert.equal(s.obstacles.filter(o=>o.type==='gem-box').length,1);assert.equal(s.gems,gems+25);
 const rock=s.obstacles.find(o=>o.type==='rock');M.clearObstacle(s,rock.id,due+3*R.WEEK,()=>0);assert.equal(rock.gemReward,0);
 pass('Weekly Gem Boxes pay 25 once, enforce a full 7-day cooldown, and never stack missed weeks');
}
{
 const s=fresh();s.buildings=s.buildings.filter(b=>b.type==='hall');s.obstacles=[];const gold=s.gold;let point={x:-10,z:8};
 for(let j=0;j<8;j++){const r=M.build(s,'wall',point.x,point.z,now+j);assert.ok(r.building);const next=M.nextWallSpot(s,point.x,point.z);assert.ok(next);assert.ok(M.canPlace(s,'wall',next.x,next.z));point=next;}
 assert.equal(s.gold,gold-8*M.TYPES.wall.gold);assert.equal(s.buildings.filter(b=>b.type==='wall').length,8);
 pass('Repeated wall placement advances to a free neighboring tile and charges once per wall');
}
{
 for(const hall of [1,4,8,15]){const s=fresh();s.buildings.find(b=>b.type==='hall').level=hall;const b=R.createBotBattle(s,()=>.6,now);assert.ok(Math.abs(b.enemy.hall-hall)<=1);assert.equal(b.enemy.kind,'bot');assert.equal(b.enemy.gold,Math.floor(b.defenderBalance.gold/10));assert.ok(b.buildings.every(x=>x.hp>0&&Number.isFinite(x.maxHp)));}
 const weak=fresh();weak.buildings=weak.buildings.filter(b=>b.type==='hall');weak.obstacles=[];weak.raids.nextDefenseAt=now;const before={gold:weak.gold,elixir:weak.elixir,dark:weak.dark};
 const entry=R.simulateDefense(weak,()=>.5,now);assert.ok(entry);assert.equal(entry.result.percent,100);for(const k of ['gold','elixir','dark'])assert.equal(weak[k],before[k]-Math.floor(before[k]/10));assert.equal(weak.raids.history[0].direction,'defense');assert.equal(R.simulateDefense(weak,()=>.5,now+1),null);
 weak.raids.nextDefenseAt=now;weak.shieldUntil=now+3600000;assert.equal(R.simulateDefense(weak,()=>.5,now),null);
 pass('Level-matched AI uses real combat against saved defenses, obeys the 10% rule, cooldown and Shields');
}
{
 const signature=model=>{const hash=createHash('sha256');model.traverse(o=>{if(o.isMesh){for(const name of ['position','color']){const a=o.geometry.getAttribute(name);if(a)hash.update(Buffer.from(a.array.buffer));}o.geometry.dispose();o.material.dispose();}});return hash.digest('hex');};
 for(const type of Object.keys(M.TYPES)){let prior;for(let level=1;level<=15;level++){const hash=signature(buildingModel({id:'v',type,level,x:0,z:0}));if(prior)assert.notEqual(hash,prior,type+' '+level);prior=hash;}}
 for(const type of Object.keys(M.HEROES)){let prior;for(let level=1;level<=50;level++){const hash=signature(makeUnit(type,false,{hero:true,level}));if(prior)assert.notEqual(hash,prior,type+' '+level);prior=hash;}assert.match(heroPortrait(type,'',12),/<image[^>]+hero-(?:atlas|recruits-v8)\.webp/);}
 pass('Every building level 1–15 and hero level 1–50 changes actual model geometry/colors; portraits reference a real image');
}
{
 const s=fresh();s.heroes.king.level=3;s.heroes.queen.level=2;const scene={add(g){g.parent=this;}};
 const world={scene};World.prototype.setVillageHeroes.call(world,s.heroes,false,s.buildings);assert.equal(world.heroVisitors.children.length,2);assert.equal(world.heroVisitors.children[0].userData.level,3);
 World.prototype.setCampArmy.call(world,s,false);const before=world.campArmy.children.length;assert.ok(before>0);s.army.ranger=0;World.prototype.setCampArmy.call(world,s,false);assert.ok(world.campArmy.children.length<before);
 pass('Camp models follow owned hero levels and the actual trained troop roster');
}

const dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-raids-')),app=await createApp({dataDir:dir,origin:'https://raid.example',secure:true});let sequence=0;
async function call(route,{data,session}={}){
 const req=Readable.from(data===undefined?[]:[Buffer.from(JSON.stringify(data))]);req.url=route;req.method=data===undefined?'GET':'POST';req.socket={remoteAddress:'127.1.0.'+(++sequence)};req.headers={host:'raid.example',origin:'https://raid.example',...(data===undefined?{}:{'content-type':'application/json'}),...(session?{cookie:session.cookie,'x-csrf-token':session.csrf}:{})};
 return new Promise(resolve=>{const out={headers:{}};app.server.emit('request',req,{headersSent:false,setHeader(k,v){out.headers[k.toLowerCase()]=v;},writeHead(status,headers){this.headersSent=true;out.status=status;Object.assign(out.headers,headers);},end(body){out.data=JSON.parse(String(body));resolve(out);}});});
}
const guest=async()=>{const r=await call('/api/session',{data:{}});assert.equal(r.status,200);return {id:r.data.user.id,cookie:r.headers['set-cookie'].split(';')[0],csrf:r.data.csrf};};
const command=(session,data)=>call('/api/command',{session,data:{requestId:randomUUID(),...data}});
const state=id=>JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(id).state);
const patch=(id,fn)=>{const s=state(id);fn(s);app.db.prepare('UPDATE players SET state=? WHERE id=?').run(JSON.stringify(s),id);};
try{
 const a=await guest();let r=await command(a,{type:'battle-start',mode:'match'});assert.equal(r.status,200);assert.equal(r.data.battle.enemy.kind,'bot');await command(a,{type:'battle-end',battleId:r.data.battleId});
 const b=await guest(),c=await guest();patch(c.id,s=>s.shieldUntil=Date.now()+86400000);patch(b.id,s=>{s.gold=150000;s.elixir=100000;s.dark=3000;});
 r=await command(a,{type:'battle-start',mode:'match',gold:999999,lootPercent:100});assert.equal(r.status,200,JSON.stringify(r.data));assert.equal(r.data.battle.defenderId,b.id);assert.deepEqual(r.data.battle.lootEscrow,{gold:15000,elixir:10000,dark:300});
 assert.equal((await command(c,{type:'battle-start',defender:b.id})).status,400);assert.equal((await command(b,{type:'shield-buy',shield:'12h'})).status,400);
 const battleId=r.data.battleId;assert.equal((await command(b,{type:'battle-end',battleId})).status,404);
 await command(a,{type:'battle-end',battleId,percent:100,gold:999999});assert.equal(state(b.id).gold,150000);assert.equal(state(b.id).shieldUntil,0);
 pass('Server matchmaking selects an eligible human, reserves 10%, rejects concurrent attacks and returns all unearned loot on scouting exit');

 patch(a.id,s=>{s.gold=0;s.elixir=0;s.dark=0;s.shieldUntil=Date.now()+100000;});
 r=await command(a,{type:'battle-start',mode:'match'});const bid=r.data.battleId;assert.ok(state(a.id).shieldUntil>Date.now());
 await command(a,{type:'battle-deploy',battleId:bid,troop:'guardian',x:16.5,z:0});assert.equal(state(a.id).shieldUntil,0);
 // Deterministic completed battlefield fixture; submitted client percentages remain ignored.
 const row=app.db.prepare('SELECT state FROM battles WHERE id=?').get(bid),battle=JSON.parse(row.state);for(const d of battle.buildings)d.hp=0;app.db.prepare('UPDATE battles SET state=? WHERE id=?').run(JSON.stringify(battle),bid);
 const requestId=randomUUID();r=await command(a,{type:'battle-end',battleId:bid,requestId,gold:999999,percent:1});assert.equal(r.status,200);const transferred=r.data.battle.result;const after=state(b.id);
 assert.equal(after.gold,150000-transferred.gold);assert.equal(after.elixir,100000-transferred.elixir);assert.equal(after.dark,3000-transferred.dark);assert.equal(state(a.id).gold,transferred.gold);assert.ok(after.shieldUntil>Date.now());
 await command(a,{type:'battle-end',battleId:bid,requestId});assert.deepEqual(state(b.id),after);
 const attacks=(await call('/api/raids',{session:a})).data.raids,defenses=(await call('/api/raids',{session:b})).data.raids;assert.equal(attacks[0].direction,'attack');assert.equal(defenses[0].direction,'defense');assert.equal(attacks[0].id,defenses[0].id);assert.deepEqual(attacks[0].result,defenses[0].result);
 pass('Server settlement credits and debits equal actual loot once, records both sides and grants defense protection');

 const solo=await guest();for(const id of [a.id,b.id,c.id])patch(id,s=>{s.raids.lastSeenAt=Date.now()-86400000;});patch(solo.id,s=>{s.buildings=s.buildings.filter(b=>b.type==='hall');s.raids.lastSeenAt=Date.now()-R.DEFENSE_INTERVAL;s.raids.nextDefenseAt=Date.now()-1;});
 const first=(await call('/api/state',{session:solo})).data.state;const log=(await call('/api/raids',{session:solo})).data.raids;assert.ok(log.some(r=>r.direction==='defense'&&r.opponentType==='bot'));const second=(await call('/api/state',{session:solo})).data.state;assert.equal(second.gold,first.gold);assert.equal(second.raids.history.length,first.raids.history.length);
 pass('A returning village receives one persisted AI defense when no active human attacker is available');
 console.log(`${checks} raid, economy and appearance checks passed.`);
}finally{await app.close();await rm(dir,{recursive:true,force:true});}
