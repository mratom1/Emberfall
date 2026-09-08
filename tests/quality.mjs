import assert from 'node:assert/strict';
import {mkdtemp, rm, readdir, stat, writeFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {DatabaseSync} from 'node:sqlite';
import * as M from '../dist/model.js';
import * as Q from '../dist/quality.js';
import {buildingModel} from '../dist/world.js';
import {createHash} from 'node:crypto';
import {Connection} from '../dist/connection.js';
import {createApp} from '../server/app.mjs';
import {backupDatabase} from '../scripts/backup.mjs';
import {startBackups} from '../server/backups.mjs';
let count = 0;
const pass = text => { count++; console.log('PASS', text); };
const now = Date.now();
const fresh = () => { const s = M.initialState(now); M.advance(s, now); return s; };
{
  const s = fresh(), gold = s.gold, gems = s.gems;
  assert.ok(M.applyAction(s, {type:'army-preset-save', slot:0, name:'First army', army:{guardian:10, ranger:5}}, now).ok);
  assert.equal(s.armyPresets[0].name, 'First army');
  assert.equal(s.gold, gold); assert.equal(s.gems, gems); assert.equal(s.heroes.king.level, 0);
  const loaded = M.loadState({getItem:()=>JSON.stringify(s)}, now);
  assert.deepEqual(loaded.armyPresets, s.armyPresets);
  for (const army of [{guardian:-1}, {guardian:1.5}, {guardian:501}, {wyvern:1}, {guardian:500}, JSON.parse('{"__proto__":1}'), [], null]) {
    assert.ok(M.applyAction(s, {type:'army-preset-save', slot:1, name:'Bad', army}, now).error);
  }
  assert.ok(M.applyAction(s, {type:'army-preset-save', slot:-1, name:'Bad', army:{guardian:1}}, now).error);
  assert.equal(s.armyPresets[1], null);
  pass('Preset migration preserves progress and rejects forged, locked, fractional and oversized armies');
}
{
  const s = fresh(); s.army = {}; s.elixir = M.TROOPS.guardian.cost * 3;
  const queue = JSON.stringify(s.queue), elixir = s.elixir;
  assert.ok(Q.trainBatch(s, {guardian:5}, now).error);
  assert.equal(s.elixir, elixir); assert.equal(JSON.stringify(s.queue), queue);
  s.elixir = 10000; s.army.guardian = M.armyCapacity(s) - 2;
  assert.ok(Q.trainBatch(s, {guardian:5}, now).error);
  assert.equal(s.elixir, 10000); assert.equal(s.queue.length, 0);
  assert.ok(M.applyAction(s,{type:'train-batch',troop:'guardian',count:Infinity},now).error);
  pass('Batch training is atomic when funds or camp space run out partway through');
}
{
  const s = fresh(); s.army = {guardian:2}; s.queue = [{type:'guardian',finishAt:now+100000}];
  assert.ok(M.applyAction(s,{type:'army-preset-save',slot:0,name:'Guard',army:{guardian:8}},now).ok);
  const cost = s.elixir, r = M.applyAction(s,{type:'army-preset-train',slot:0},now);
  assert.equal(r.queued,5); assert.equal(s.elixir,cost-5*M.TROOPS.guardian.cost);
  assert.equal(M.applyAction(s,{type:'army-preset-train',slot:0},now).queued,0);
  const home = s.elixir;
  assert.ok(M.applyAction(s,{type:'army-preset-save',realm:'builder',slot:0,name:'Night',army:{guardian:14}},now).ok);
  assert.equal(s.armyPresets[0].name,'Guard'); assert.equal(s.expansion.builder.armyPresets[0].name,'Night');
  assert.equal(M.applyAction(s,{type:'army-preset-train',realm:'builder',slot:0},now).queued,2);
  assert.equal(s.elixir,home);
  pass('Quick train fills missing troops once and isolates home and Builder Base presets and wallets');
}
{
  const s = fresh(); s.heroes.king.recoverAt=now+8000; s.buildings[0].finishAt=now+20000;
  s.expansion.builder.queue=[{type:'guardian',finishAt:now+10000},{type:'ranger',finishAt:now+15000}];
  const jobs=Q.workOrders(s,now);
  assert.ok(jobs.some(j=>j.kind==='building'&&j.id===s.buildings[0].id));
  assert.ok(jobs.some(j=>j.kind==='recovery'&&!j.canSkip));
  assert.equal(jobs.filter(j=>j.realm==='builder'&&j.canSkip).length,1);
  assert.ok(jobs.every((j,i)=>i===0||jobs[i-1].finishAt<=j.finishAt));
  pass('Work queue orders both villages correctly and only offers valid timer skips');
}
{
  const ids=[]; let down=true;
  const api=new Connection({pause:async()=>{},fetcher:async(p,o)=>{ids.push(JSON.parse(o.body).requestId);if(down)throw new Error('offline');return new Response(JSON.stringify({ok:true}));}});
  await assert.rejects(api.command({type:'exchange',resource:'gold'}),/confirmation/);
  assert.equal(ids.length,3);assert.equal(new Set(ids).size,1);
  await assert.rejects(api.command({type:'builder'}),/previous action/);assert.equal(ids.length,3);
  down=false;await api.retryPending();assert.equal(new Set(ids).size,1);assert.equal(api.pending,null);
  pass('Connection recovery preserves one request ID and blocks new spending until confirmation');
}
{
  let calls=0;
  const api=new Connection({pause:async()=>{},fetcher:async()=>{calls++;return new Response(JSON.stringify({error:'Insufficient funds'}),{status:400});}});
  await assert.rejects(api.command({type:'builder'}),/Insufficient funds/);assert.equal(calls,1);assert.equal(api.pending,null);
  api.fetcher=async()=>{calls++;throw new Error('offline');};
  calls=0;await assert.rejects(api.request('/payments/checkout',{method:'POST',data:{pack:'large'}}));assert.equal(calls,1);
  api.user={id:'first'};await assert.rejects(api.command({type:'collect'}));api.user={id:'second'};
  calls=0;await assert.rejects(api.retryPending(),/another account/);assert.equal(calls,0);
  api.user={id:'first'};calls=0;api.pause=async()=>{api.user={id:'second'};};
  await assert.rejects(api.command({type:'collect'}),/account changed/);assert.equal(calls,1);
  pass('Validation errors and checkout are not retried; pending commands never cross accounts');
}
{
  const s=fresh();s.gold=10000;s.elixir=10000;
  s.buildings.push({id:'w1',type:'wall',level:1,x:10,z:0},{id:'w2',type:'wall',level:1,x:10,z:1});
  const cost=Q.wallQuote(s,['w1','w2']).cost,gold=s.gold,elixir=s.elixir;
  assert.ok(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w1']},now).error);
  assert.ok(M.applyAction(s,{type:'wall-upgrade',ids:['w1',s.buildings[0].id]},now).error);
  assert.ok(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w2'],currency:'elixir'},now).error);
  assert.equal(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w2'],levels:[1,1]},now).upgraded,2);
  assert.equal(s.gold,gold-cost);assert.equal(s.elixir,elixir);
  assert.ok(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w2'],levels:[1,1]},now).error);
  assert.ok(M.applyAction(s,{type:'upgrade',id:'w1'},now).error);
  s.buildings[0].level=4;
  const next=Q.wallQuote(s,['w1','w2'],'elixir').cost;
  assert.equal(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w2'],currency:'elixir'},now).upgraded,2);
  assert.equal(s.elixir,elixir-next);assert.equal(s.gold,gold-cost);
  const before=JSON.stringify(s.buildings);s.gold=0;
  assert.ok(M.applyAction(s,{type:'wall-upgrade',ids:['w1','w2']},now).error);assert.equal(JSON.stringify(s.buildings),before);
  const b=s.expansion.builder;b.buildings.push({id:'bw',type:'wall',level:10,x:10,z:0});b.buildings[0].level=10;
  assert.ok(M.applyAction(s,{type:'wall-upgrade',realm:'builder',ids:['bw']},now).error);
  pass('Bulk walls validate ownership, unique IDs, preview levels, currencies, funds and Town Hall limits');
  const signatures=[];
  for(let level=1;level<=15;level++){
    const model=buildingModel({type:'wall',level,id:'test',x:0,z:0}),hash=createHash('sha256');
    model.traverse(o=>{if(o.geometry)for(const key of ['position','color']){const attribute=o.geometry.getAttribute(key);if(attribute)hash.update(Buffer.from(attribute.array.buffer));}});
    signatures.push(hash.digest('hex'));
  }
  assert.equal(new Set(signatures).size,15);
  pass('All 15 wall levels have distinct renderable 3D geometry or colors');
}
const dir=await mkdtemp(path.join(os.tmpdir(),'emberfall-quality-'));
let app=await createApp({port:0,host:'127.0.0.1',dataDir:dir});await app.listen();
const base='http://127.0.0.1:'+app.server.address().port;
let cookie='', csrf='', playerId='';
try {
  const session=await fetch(base+'/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}), initial=await session.json();
  cookie=session.headers.get('set-cookie').split(';')[0];csrf=initial.csrf;playerId=initial.user.id;
  const actual=async(p,o)=>fetch(base+p,{...o,headers:{...o?.headers,Cookie:cookie,'X-CSRF-Token':csrf}});
  let lost=false;
  const api=new Connection({pause:async()=>{},fetcher:async(p,o)=>{const r=await actual(p,o);if(p==='/api/command'&&!lost){lost=true;await r.text();throw new Error('response dropped after commit');}return r;}});
  api.user=initial.user;api.csrf=csrf;
  const response=await api.command({type:'train-batch',troop:'guardian',count:5});
  assert.equal(response.result.queued,5);
  const stored=JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(playerId).state);
  assert.equal(stored.elixir,initial.state.elixir-5*M.TROOPS.guardian.cost);
  assert.equal(stored.queue.length,5);
  assert.equal(app.db.prepare('SELECT COUNT(*) AS n FROM commands WHERE player_id=?').get(playerId).n,1);
  pass('Real HTTP response loss after SQLite commit charges elixir once on automatic retry');
  const wallState=JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(playerId).state);
  wallState.buildings.push({id:'persist-wall',type:'wall',level:1,x:10,z:0});
  app.db.prepare('UPDATE players SET state=? WHERE id=?').run(JSON.stringify(wallState),playerId);
  let wallDrop=false;api.fetcher=async(p,o)=>{const r=await actual(p,o);if(p==='/api/command'&&!wallDrop){wallDrop=true;await r.text();throw new Error('wall response lost');}return r;};
  await api.command({type:'wall-upgrade',ids:['persist-wall'],levels:[1],currency:'gold'});
  const wallSaved=JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(playerId).state);
  assert.equal(wallSaved.buildings.find(b=>b.id==='persist-wall').level,2);
  assert.equal(wallSaved.gold,wallState.gold-M.upgradeCost({type:'wall',level:1}).gold);
  pass('Server wall upgrades survive lost responses with one debit and one level increase');

  await api.command({type:'army-preset-save',slot:2,name:'Persistent army',army:{guardian:12}});
  const file=backupDatabase({dataDir:dir});const snapshot=new DatabaseSync(file,{readOnly:true});
  assert.equal(JSON.parse(snapshot.prepare('SELECT state FROM players WHERE id=?').get(playerId).state).armyPresets[2].name,'Persistent army');snapshot.close();
  assert.equal((await stat(file)).mode & 0o777,0o600);
  const out=path.join(dir,'backups');await writeFile(path.join(out,'unrelated.sqlite'),'keep');
  for(let i=0;i<4;i++)backupDatabase({dataDir:dir,automatic:true,keep:2,now:new Date(now+i*1000)});
  const names=await readdir(out);assert.equal(names.filter(n=>n.startsWith('emberfall-auto-')).length,2);assert.ok(names.includes(path.basename(file)));assert.ok(names.includes('unrelated.sqlite'));
  const manager=startBackups(dir,{intervalMs:60000,keep:2,report:message=>{throw new Error(message);}});
  const first=manager.run(),second=manager.run();assert.equal(first,second);assert.ok((await first).endsWith('.sqlite'));await manager.close();
  assert.equal((await readdir(out)).filter(n=>n.endsWith('.partial')).length,0);
  pass('Consistent WAL snapshots restore real account data; automatic retention preserves manual and unrelated files');
  await app.close();app=null;
  app=await createApp({port:0,host:'127.0.0.1',dataDir:dir});await app.listen();
  const persisted=JSON.parse(app.db.prepare('SELECT state FROM players WHERE id=?').get(playerId).state);
  assert.equal(persisted.armyPresets[2].name,'Persistent army');
  assert.equal(persisted.heroes.champion.level,0);
  pass('Server restart preserves army presets, troop orders and Town Hall hero restrictions');
  console.log(`${count} quality and recovery checks passed.`);
} finally {if(app)await app.close();await rm(dir,{recursive:true,force:true});}
