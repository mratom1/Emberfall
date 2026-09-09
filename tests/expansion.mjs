import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import * as M from '../dist/model.js';
import * as X from '../dist/expansion.js';
import {makeUnit} from '../dist/world.js';
import {createApp} from '../server/app.mjs';
let count=0;const pass=n=>{count++;console.log('PASS',n);};
const now=Date.now();
function state(){const s=M.initialState(now);M.advance(s,now);return s;}
{
 const s=state();s.dark=1e7;s.buildings.push({id:'altar',type:'altar',x:8,z:8,level:1});
 for(const type of X.HOME_HEROES){
  const def=M.HEROES[type],hall=s.buildings[0],barracks=s.buildings.find(b=>b.type==='barracks');
  hall.level=def.unlock-1;barracks.level=def.barracks||1;assert.ok(M.upgradeHero(s,type,now).error,type+' must remain locked');
  hall.level=def.unlock;if(def.barracks){barracks.level=def.barracks-1;assert.ok(M.upgradeHero(s,type,now).error,type+' needs Barracks');barracks.level=def.barracks;}
  const cap=def.barracks?Math.min(50,def.unlock*5,def.barracks*5):5;assert.equal(M.heroMaxLevel(s,type),cap);
  assert.ok(M.upgradeHero(s,type,now).ok);M.advance(s,now+40000);assert.equal(s.heroes[type].level,1);
  s.heroes[type].level=cap;assert.ok(M.upgradeHero(s,type,now+40000).error);hall.level++;barracks.level++;
  const next=Math.min(50,cap+5);assert.equal(M.heroMaxLevel(s,type),next);if(next>cap)assert.ok(M.upgradeHero(s,type,now+40000).ok);
 }
 pass('All 20 home heroes enforce Town Hall and Barracks unlocks, progression caps and maximum level 50');
}
{
 const s=state();s.heroes.king.level=1;s.expansion.ore=10000;
 const basic=X.heroStats(s,'king',1);assert.ok(M.applyAction(s,{type:'equipment-upgrade',item:'emberblade'},now).ok);M.advance(s,now+20000);assert.ok(X.heroStats(s,'king',1).damage>basic.damage);assert.ok(M.applyAction(s,{type:'equipment-equip',hero:'king',slot:0,item:'emberblade'},now+21000).error);
 s.expansion.pets.fox.level=2;assert.ok(M.applyAction(s,{type:'pet-assign',hero:'king',pet:'fox'},now+21000).ok);const b=M.createBattle(s,0);M.deployHero(s,b,'king',0,11);assert.ok(b.units.some(u=>u.pet&&u.type==='fox'));const u=b.units.find(u=>u.hero);u.hp=50;assert.ok(M.heroAbility(b,'king').ok);assert.ok(u.hp>50);assert.ok(M.heroAbility(b,'king').error);pass('Equipment changes real combat stats; pets deploy and hero abilities can only fire once');
}
{
 const s=state();const before=JSON.stringify(s),b=X.createModeBattle(s,'training',now).battle;
 for(const k of X.HOME_HEROES){assert.ok(M.deployHero(s,b,k,0,11).unit);assert.ok(M.heroAbility(b,k).ok);}assert.ok(X.deploySiege(s,b,'ram',3,11).unit);assert.ok(X.deploySiege(s,b,'airship',4,11).error);b.units.find(u=>u.siege).hp=0;M.stepBattle(b,.05);assert.ok(b.units.filter(u=>u.type==='guardian').length>=3);M.settleBattle(s,b);assert.equal(JSON.stringify(s),before);assert.equal(b.result.gold,0);pass('Hero practice lends heroes and siege machines without mutating real wallets or unlocks');
}
{
 const s=state(),before=s.gold,army=s.army.guardian,v=s.expansion.builder;
 assert.ok(M.applyAction(s,{type:'upgrade',id:'bh',realm:'builder'},now).ok);assert.equal(s.gold,before);M.advance(s,now+40000);assert.equal(v.buildings[0].level,2);assert.equal(s.buildings[0].level,1);
 const b=X.createModeBattle(s,'builder',now+40000).battle;assert.ok(M.deploy(s,b,'guardian',0,11).unit);assert.equal(s.army.guardian,army);assert.equal(v.army.guardian,11);assert.ok(M.deployHero(s,b,'machine',1,11).unit);M.settleBattle(s,b);
 const obstacle=v.obstacles.find(o=>o.type==='tree');obstacle.finishAt=now+50000;obstacle.gemReward=3;const gems=s.gems;M.advance(s,now+50001);assert.equal(s.gems,gems+3);M.advance(s,now+50002);assert.equal(s.gems,gems+3);pass('Builder Base isolates resources and troops, keeps its own hero and shares gem rewards once');
}
{
 const s=state();s.expansion.season.points=500;assert.ok(M.applyAction(s,{type:'season-claim',tier:5},now).ok);const gems=s.gems;assert.ok(M.applyAction(s,{type:'season-claim',tier:5},now).error);assert.equal(s.gems,gems);s.stats.wins+=3;assert.ok(M.applyAction(s,{type:'daily-claim',id:'victory'},now).ok);assert.ok(M.applyAction(s,{type:'daily-claim',id:'victory'},now).error);pass('Daily challenges and season rewards validate progress and pay once');
}
{
 for(const type of [...X.HOME_HEROES,'machine',...Object.keys(X.PETS).map(k=>'pet:'+k),...Object.keys(X.SIEGE).map(k=>'siege:'+k)]){const model=makeUnit(type);assert.ok(model.children.length,type);model.traverse(o=>{if(o.geometry)assert.ok(o.geometry.attributes.position.count>0,type);});}pass('All heroes, pets and siege machines have renderable 3D models');
}
const dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-expansion-'));
const app=await createApp({port:0,host:'127.0.0.1',dataDir:dir});await app.listen();const url='http://127.0.0.1:'+app.server.address().port;
async function req(session,p,a){const r=await fetch(url+'/api'+p,{method:a?'POST':'GET',headers:{...(session?{Cookie:session.cookie,'X-CSRF-Token':session.csrf}:{}),...(a?{'Content-Type':'application/json'}:{})},...(a?{body:JSON.stringify(a)}:{})});return {status:r.status,...await r.json(),cookie:r.headers.get('set-cookie')};}
async function guest(){const r=await req(null,'/session',{});return {cookie:r.cookie.split(';')[0],csrf:r.csrf,id:r.user.id};}
const cmd=(session,a)=>req(session,'/command',{requestId:randomUUID(),...a});
function patch(id,fn){const s=JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(id).state);fn(s);app.db.prepare('UPDATE players SET state=? WHERE id=?').run(JSON.stringify(s),id);}
function warPatch(id,fn){const w=JSON.parse(app.db.prepare('SELECT state FROM wars WHERE id=?').get(id).state);fn(w);app.db.prepare('UPDATE wars SET state=?,status=? WHERE id=?').run(JSON.stringify(w),w.status,id);}
async function win(session,mode){patch(session.id,s=>{s.army.guardian=30;s.army.giant=10;s.heroes.king={level:20,recoverAt:0};});const start=await cmd(session,{type:'battle-start',...mode});assert.equal(start.status,200,JSON.stringify(start));const id=start.battleId;for(let i=0;i<10;i++)assert.equal((await cmd(session,{type:'battle-deploy',battleId:id,troop:'giant',x:(i%5-2)*.6,z:start.battle.bounds+2})).status,200);assert.equal((await cmd(session,{type:'battle-hero',battleId:id,hero:'king',x:0,z:start.battle.bounds+2})).status,200);await cmd(session,{type:'battle-ability',battleId:id,hero:'king'});app.db.prepare('UPDATE battles SET last_step=last_step-151000 WHERE id=?').run(id);const end=await req(session,'/battle?id='+id);assert.equal(end.status,200);assert.ok(end.battle.settled);return end;}
try{
 const a=await guest(),b=await guest(),mate=await guest();
 assert.equal((await cmd(a,{type:'hero-upgrade',hero:'queen'})).status,400);let r=await cmd(a,{type:'battle-start',mode:'training'});assert.equal(r.status,200);const before=r.state.gold;assert.equal(Object.keys(r.battle.heroStock).length,20);await cmd(a,{type:'battle-hero',battleId:r.battleId,hero:'champion',x:0,z:11});r=await cmd(a,{type:'battle-end',battleId:r.battleId});assert.equal(r.state.gold,before);assert.equal(r.state.heroes.champion.level,0);pass('Server rejects locked heroes and keeps training heroes separate from real accounts');
 const ca=await req(a,'/clans',{action:'create',name:'North Test Clan'}),cb=await req(b,'/clans',{action:'create',name:'South Test Clan'});assert.equal(ca.status,200);assert.equal(cb.status,200);await req(mate,'/clans',{action:'join',id:ca.user.clanId});
 assert.equal((await cmd(mate,{type:'war-start',opponent:cb.user.clanId})).status,400);r=await cmd(a,{type:'war-start',opponent:cb.user.clanId});assert.equal(r.status,200);let front=await req(a,'/frontiers'),w=front.wars[0];assert.equal((await cmd(a,{type:'battle-start',mode:'war',warId:w.id,target:b.id})).status,400);warPatch(w.id,w=>w.readyAt=Date.now()-1);
 const wa=await win(a,{mode:'war',warId:w.id,target:b.id});assert.ok(wa.battle.result.stars);assert.equal((await cmd(a,{type:'battle-start',mode:'war',warId:w.id,target:b.id})).status,400);
 await win(b,{mode:'war',warId:w.id,target:a.id});front=await req(a,'/frontiers');assert.equal(front.wars[0].status,'ended');r=await cmd(a,{type:'war-claim',warId:w.id});assert.equal(r.status,200);assert.equal((await cmd(a,{type:'war-claim',warId:w.id})).status,400);pass('Real clan wars enforce leaders, preparation, rosters, attack limits and one-time rewards');
 const gold=(await req(a,'/state')).state.expansion.capitalGold;assert.equal((await cmd(a,{type:'capital-donate',amount:250})).status,200);assert.equal((await req(a,'/state')).state.expansion.capitalGold,gold-250);assert.equal((await cmd(mate,{type:'upgrade',realm:'capital',id:'bh'})).status,400);assert.equal((await cmd(a,{type:'upgrade',realm:'capital',id:'bh'})).status,200);
 r=await win(a,{mode:'capital'});assert.ok(r.battle.result.capitalGold>0);front=await req(a,'/frontiers');assert.equal(front.world.raid.active,null);assert.equal(front.world.raid.uses[a.id],1);assert.ok(front.world.raid.district>0||front.world.raid.buildings.some(b=>b.hp<=0));const snapshot=(await req(a,'/state')).state.expansion.capitalGold;await cmd(a,{type:'battle-end',battleId:r.battleId});assert.equal((await req(a,'/state')).state.expansion.capitalGold,snapshot);pass('Capital donations, leader construction, persistent raid damage and rewards are authoritative');
 assert.equal((await cmd(a,{type:'league-start'})).status,200);assert.equal((await cmd(mate,{type:'league-next'})).status,400);
 for(let round=0;round<7;round++){await win(a,{mode:'league'});assert.equal((await cmd(a,{type:'battle-start',mode:'league'})).status,400);const row=app.db.prepare('SELECT state FROM clan_worlds WHERE clan_id=?').get(ca.user.clanId),c=JSON.parse(row.state);c.league.roundAt=Date.now()-900001;app.db.prepare('UPDATE clan_worlds SET state=? WHERE clan_id=?').run(JSON.stringify(c),ca.user.clanId);assert.equal((await cmd(a,{type:'league-next'})).status,200);}
 front=await req(a,'/frontiers');assert.equal(front.world.league.ended,true);assert.equal(front.world.league.scores.length,7);assert.equal((await cmd(a,{type:'league-claim'})).status,200);assert.equal((await cmd(a,{type:'league-claim'})).status,400);pass('Seven-round clan league saves attacks, results and one-time completion medals');
 const builderGold=(await req(a,'/state')).state.expansion.builder.gold;assert.equal((await cmd(a,{type:'upgrade',realm:'builder',id:'bh'})).status,200);r=await req(a,'/state');assert.ok(r.state.expansion.builder.gold<builderGold);assert.equal(r.state.buildings[0].level,1);pass('Builder Base progression survives real server commands and database reloads');
 console.log(`${count} expansion checks passed.`);
}finally{await app.close();await rm(dir,{recursive:true,force:true});}
