import assert from 'node:assert/strict';
import * as THREE from '../dist/assets/three.module.js';
import {makeUnit} from '../dist/world.js';
import {TROOPS,HEROES} from '../dist/model.js';

for(const [label,roster] of [['army',TROOPS],['hero',HEROES]]){
  const signatures=new Set();
  for(const type of Object.keys(roster)){
    const model=makeUnit(type,false,{level:15});
    let meshes=0,vertices=0;const colors=new Set();
    model.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position?.count||0;const c=o.material?.color?.getHex?.();if(Number.isFinite(c))colors.add(c);}});
    model.updateMatrixWorld(true);
    const size=new THREE.Box3().setFromObject(model).getSize(new THREE.Vector3());
    assert.ok(meshes>0&&vertices>0,`${label} ${type} must render geometry`);
    assert.ok([size.x,size.y,size.z].every(Number.isFinite),`${label} ${type} must have finite bounds`);
    signatures.add([meshes,vertices,colors.size,size.x.toFixed(2),size.y.toFixed(2),size.z.toFixed(2)].join(':'));
  }
  assert.equal(signatures.size,Object.keys(roster).length,`every ${label} must have a distinct structural silhouette`);
  console.log(`PASS ${Object.keys(roster).length} ${label} models have distinct, renderable 3D silhouettes`);
}
