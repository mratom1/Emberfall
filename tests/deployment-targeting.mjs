import assert from 'node:assert/strict';
import * as M from '../dist/model.js';
const s=M.initialState();s.army.guardian=8;s.heroes.king.level=1;
const b=M.createBattle(s,0);b.buildings=[{id:'hall',type:'hall',level:1,x:0,z:0,hp:1000,maxHp:1000}];b.heroStock.king=1;
for(const [x,z] of [[4,0],[-4,0],[0,4],[0,-4]]){assert.ok(M.canDeploy(b,x,z));const r=M.deploy(s,b,'guardian',x,z);assert.equal(r.unit.x,x);assert.equal(r.unit.z,z);}
assert.ok(M.deployHero(s,b,'king',4,4).unit);assert.equal(M.canDeploy(b,0,0),false);b.buildings[0].hp=0;assert.ok(M.canDeploy(b,0,0));assert.equal(M.canDeploy(b,200,200),false);assert.equal(M.canDeploy(b,NaN,0),false);b.ended=true;assert.equal(M.canDeploy(b,4,4),false);
console.log('PASS Successive troop and hero drops use distinct open interior tiles; occupied, invalid and out-of-bounds drops remain blocked');
for(const type of ['giant','breaker','colossus','sentinel','valkyrie','champion']){
 const state=M.initialState(),battle=M.createBattle(state,0);battle.started=true;battle.remaining={guardian:1};battle.heroStock={};
 battle.buildings=[{id:'defense',type:'cannon',level:1,x:1,z:0,hp:1,maxHp:1,cooldown:99},{id:'store',type:'storage',level:1,x:5,z:0,hp:1000,maxHp:1000},{id:'wall',type:'wall',level:1,x:-1,z:0,hp:1000,maxHp:1000}];
 battle.units=[{id:'unit',type,hero:type==='champion',level:1,x:0,z:0,hp:10000,maxHp:10000,damage:100,cooldown:0}];
 M.stepBattle(battle,.05);assert.equal(battle.buildings[0].hp,0,type);M.stepBattle(battle,.05);assert.equal(battle.units[0].target,'store',type);
 for(let i=0;i<160;i++)M.stepBattle(battle,.05);assert.ok(battle.buildings[1].hp<1000,type+' attacks remaining resources');
}
console.log('PASS Defense hunters and champion retarget non-defense buildings after the final defense falls, instead of choosing unrelated nearby walls');
