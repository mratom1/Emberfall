import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as M from '../dist/model.js';
import * as R from '../dist/raids.js';
import {modelPortrait,heroPortrait} from '../dist/portraits.js';
import {portraitModel,makeUnit,buildingModel} from '../dist/world.js';
const signature=model=>{const h=createHash('sha256');model.traverse(o=>{if(o.geometry){for(const a of Object.values(o.geometry.attributes))h.update(Buffer.from(a.array.buffer));o.geometry.dispose();}if(o.material)o.material.dispose();});return h.digest('hex');};
for(const [kind,defs]of [['building',M.TYPES],['troop',M.TROOPS],['hero',M.HEROES]])for(const type of Object.keys(defs))for(const level of [1,kind==='hero'?50:15]){
 const markup=kind==='hero'?heroPortrait(type,'',level):modelPortrait(kind,type,level);
 assert.ok(markup.includes(`data-model-kind="${kind}"`));assert.ok(markup.includes(`data-model-type="${type}"`));assert.ok(markup.includes(`data-model-level="${level}"`));
 const actual=kind==='building'?buildingModel({type,level,id:'inspect',x:0,z:0}):makeUnit(type,false,{level});
 assert.equal(signature(portraitModel({kind,type,level})),signature(actual),`${kind} ${type} level ${level}`);
}
console.log('PASS Every building, troop and hero picture uses identical model geometry/colors and level as the world');
for(const [type,d]of Object.entries(M.TYPES).filter(([,d])=>!d.decoration)){
 assert.equal(M.buildingHp({type,level:1}),d.hp);let previous=0;
 for(let level=1;level<=15;level++){const hp=M.buildingHp({type,level});assert.ok(Number.isInteger(hp)&&hp>=previous);previous=hp;}
 assert.ok(M.buildingHp({type,level:15})>d.hp*4.5*6);
}
const s=M.initialState();M.advance(s);for(const b of s.buildings)b.level=7;
const b=R.configureBattle(M.createBattle(s,0),{id:'defender',name:'Defender',state:s});
for(const x of b.buildings)assert.equal(x.maxHp,M.buildingHp(x));
console.log('PASS Defender HP remains unchanged at level 1, grows monotonically, and matches authoritative raid HP');
