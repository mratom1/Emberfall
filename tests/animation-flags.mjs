import assert from 'node:assert/strict';
import {makeUnit,animateUnit,World} from '../dist/world.js';
import {TROOPS,HEROES} from '../dist/model.js';
import {flagCanvas} from '../dist/flags.js';
for(const [type,def] of Object.entries({...TROOPS,...HEROES})){
 const m=makeUnit(type),j=m.userData.joints;
 animateUnit(m,.18,true);if(!def.flying){assert.ok(j.leftLeg&&j.rightLeg,type);assert.notEqual(j.leftLeg.rotation.x,0);assert.equal(j.leftLeg.rotation.x,-j.rightLeg.rotation.x);animateUnit(m,.18,false);assert.equal(Math.abs(j.leftLeg.rotation.x),0);assert.equal(Math.abs(j.rightLeg.rotation.x),0);}else{assert.ok(animateUnit(m,.18,true)>1);assert.ok(!j.leftLeg&&!j.rightLeg);}
}
console.log('PASS Every ground troop and hero has opposing walking legs; idle stops walking and flying units stay airborne');
const originals={fetch:globalThis.fetch,Image:globalThis.Image,document:globalThis.document};let draws=0;
globalThis.fetch=async()=>({ok:true,json:async()=>({mm:'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480"><path fill="red" d="M0 0h640v480H0z"/></svg>'})});globalThis.Image=class{set src(value){assert.ok(decodeURIComponent(value).includes('width="256" height="192"'));queueMicrotask(()=>this.onload());}};globalThis.document={createElement:()=>({getContext:()=>({drawImage(){draws++;}})})};
try{const c=await flagCanvas('mm');assert.equal(c.width,256);assert.equal(c.height,192);assert.equal(await flagCanvas('mm'),c);assert.equal(draws,1);await assert.rejects(flagCanvas('invalid'));const material={color:{setHex(v){this.hex=v;}},map:null};const cloth={userData:{},material};await World.prototype.applyFlagTexture.call({callbacks:{}},cloth,'mm');assert.equal(material.map.isCanvasTexture,true);assert.equal(material.map.generateMipmaps,false);assert.equal(material.color.hex,0xffffff);material.map.dispose();}finally{Object.assign(globalThis,originals);}
console.log('PASS Flag SVGs get explicit dimensions, rasterize once per country and upload as non-mipmapped canvas textures');
