import {appearance} from './raids.js?v=6.0.0';
import {gamePoint,gameDelta,isRotated} from './viewport.js?v=6.0.0';
import {GRAPHICS, graphicsProfile, renderScale} from './graphics.js?v=6.0.0';
import * as THREE from './assets/three.module.js';
import {TYPES,TROOPS,HEROES,canPlace,unitDefinition} from './model.js?v=6.0.0';

const C={grass:0x75a44e,grassLight:0x87b05a,grassDark:0x5c8c3f,dirt:0xc8b489,stone:0xc5c0a2,stoneDark:0x827f69,wall:0xd6c5a0,wood:0x72503c,timber:0x503e30,roof:0x984e3f,roofLight:0xbb6847,gold:0xe5bd57,iron:0x485452,leaf:0x407643,pine:0x335d3e,water:0x68a9a3};
const materials=new Map();
function mat(c){if(!materials.has(c))materials.set(c,new THREE.MeshStandardMaterial({color:c,roughness:.78,metalness:.03}));return materials.get(c);}
function mesh(parent,geo,color,x=0,y=0,z=0){const m=new THREE.Mesh(geo,mat(color));m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
function box(p,w,h,d,c,x=0,y=0,z=0){return mesh(p,new THREE.BoxGeometry(w,h,d),c,x,y,z);}
function cone(p,r,h,c,x=0,y=0,z=0,n=4){return mesh(p,new THREE.ConeGeometry(r,h,n),c,x,y,z);}
function cyl(p,rt,rb,h,c,x=0,y=0,z=0,n=8){return mesh(p,new THREE.CylinderGeometry(rt,rb,h,n),c,x,y,z);}
function rock(p,r,c,x,y,z){const m=mesh(p,new THREE.DodecahedronGeometry(r,0),c,x,y,z);m.rotation.set(x*.4,z*.7,x*.1);return m;}
function sphere(p,r,c,x,y,z){return mesh(p,new THREE.IcosahedronGeometry(r,1),c,x,y,z);}
function seeded(seed){return()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};}
function merged(group){
  group.updateMatrixWorld(true);const positions=[],normals=[],colors=[];
  group.traverse(o=>{if(!o.isMesh)return;const g=o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone();g.applyMatrix4(o.matrixWorld);const p=g.getAttribute('position'),n=g.getAttribute('normal'),c=o.material.color;
    for(let i=0;i<p.count;i++){positions.push(p.getX(i),p.getY(i),p.getZ(i));normals.push(n.getX(i),n.getY(i),n.getZ(i));colors.push(c.r,c.g,c.b);}g.dispose();
  });
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeBoundingSphere();
  const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.82,metalness:.03}));m.castShadow=true;m.receiveShadow=true;
  group.traverse(o=>{if(o.isMesh)o.geometry.dispose();});return m;
}
function roof(parent,w,d,h,x,y,z,color=C.roof){
  const points=[-w/2,0,-d/2,w/2,0,-d/2,0,h,-d/2,-w/2,0,d/2,0,h,d/2,w/2,0,d/2,-w/2,0,-d/2,0,h,-d/2,0,h,d/2,-w/2,0,-d/2,0,h,d/2,-w/2,0,d/2,w/2,0,-d/2,w/2,0,d/2,0,h,d/2,w/2,0,-d/2,0,h,d/2,0,h,-d/2];
  for(let i=0;i<points.length;i+=9)for(let j=0;j<3;j++){const v=points[i+3+j];points[i+3+j]=points[i+6+j];points[i+6+j]=v;}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(points,3));geo.computeVertexNormals();mesh(parent,geo,color,x,y,z);
  box(parent,.13,.14,d+.14,C.roofLight,x,y+h,z);
  for(const side of [-1,1]){const m=box(parent,Math.hypot(w/2,h),.075,d+.08,side<0?C.roofLight:C.roof,x+side*w/4,y+h/2,z);m.rotation.z=-side*Math.atan2(h,w/2);}
}
function windowBlock(p,x,y,z,w=.3,h=.5){box(p,w+.15,h+.12,.07,C.wood,x,y,z);box(p,w,h,.085,0x394538,x,y,z+.02);box(p,.055,h,.10,0xbeaa72,x,y,z+.035);}
function banner(p,x,y,z,red=true){cyl(p,.033,.033,1.3,0xc5b08a,x,y+.3,z,5);box(p,.48,.58,.045,red?0xb75d42:0x315c60,x+.23,y+.65,z);box(p,.06,.18,.055,C.gold,x+.23,y+.65,z+.03);cone(p,.075,.18,C.gold,x,y+1.03,z,4);}
function barrel(p,x,y,z){cyl(p,.25,.25,.53,C.wood,x,y+.265,z,8);cyl(p,.26,.26,.065,C.iron,x,y+.12,z,8);cyl(p,.26,.26,.065,C.iron,x,y+.4,z,8);cyl(p,.22,.22,.018,0xa78358,x,y+.54,z,8);}
function stairs(p,x,z,width=1){for(let i=0;i<3;i++)box(p,width,.12*(i+1),.3,C.stone,x,.06*(i+1),z-i*.22);}
function smallTower(p,x,z,h=2.2){
  cyl(p,.49,.57,h,C.wall,x,h/2+.22,z,8);cyl(p,.6,.57,.2,C.stoneDark,x,h+.18,z,8);cyl(p,.62,.62,.25,C.stone,x,h+.4,z,8);
  for(let i=0;i<6;i++){const a=i*Math.PI/3;box(p,.2,.28,.21,C.wall,x+Math.sin(a)*.5,h+.63,z+Math.cos(a)*.5);}
  const r=cone(p,.87,1.16,C.roof,x,h+1.17,z,8);cone(p,.09,.2,C.gold,x,h+1.84,z,4);
  box(p,.14,.39,.05,0x414b3e,x,h-.35,z+.505);return r;
}
function buildingLevelDetails(g,b,size){
 const level=Math.max(1,Math.min(15,b.level||1));if(level===1||b.type==='wall')return;
 const colors=[0x9a7150,0xa58965,0xbaa477,0x869ca2,0x7798ab,0x627e9c,0x6873a6,0x9d8eac,0xb1a0c3,0xcfb275,0xe3bc6e,0x4fabad,0x69c6ce,0x9eacd4,0xc7a9e7];
 const trim=colors[level-1],tier=Math.floor((level-1)/3),edge=size*.42;
 for(const z of [-edge,edge])box(g,size*.93,.07+level*.006,.11,trim,0,.45,z);
 for(const x of [-edge,edge])box(g,.11,.07+level*.006,size*.93,trim,x,.45,0);
 for(let j=0;j<level;j++)box(g,.08,.12,.045,trim,-Math.min(size*.36,.8)+(j%8)*.2,.63+Math.floor(j/8)*.19,size*.48);
 if(tier>0)for(const x of [-edge,edge])for(const z of [-edge,edge]){box(g,.16+tier*.025,.4+tier*.2,.16+tier*.025,trim,x,.5+tier*.1,z);if(tier>1)cone(g,.15,.24,trim,x,1+tier*.2,z,5);}
 if(level>=7){const badge=new THREE.Mesh(new THREE.OctahedronGeometry(.10+(level-7)*.008),mat(level>=12?0x99eeee:0xf1ce80));badge.position.set(0,.9,size*.48);g.add(badge);}
 if(level>=10&&b.type!=='bomb')banner(g,edge,1.1+tier*.25,-edge,true);
 g.scale.y=1+(level-1)*.015;
}
function heroLevelDetails(body,level){
 const look=appearance(level),c=look.color;
 for(const x of [-.36,.36]){box(body,.19+level*.003,.10+level*.001,.30,c,x,1.10,.01);box(body,.09,.24,.10,c,x*.48,.36,.12);}
 for(let j=0;j<look.marks;j++){const angle=(j/10)*Math.PI*2;const gem=mesh(body,new THREE.OctahedronGeometry(.023+look.tier*.005),c,Math.sin(angle)*.13,.95+Math.cos(angle)*.13,.205);gem.rotation.z=j;}
 if(level>=5)box(body,.25,.045,.09,c,.47,1.1+level*.004,.17);
 if(level>=10)for(const side of [-1,1])cone(body,.06,.17+level*.003,c,side*.28,1.65,0,5).rotation.z=side*.35;
 if(level>=20){const aura=mesh(body,new THREE.TorusGeometry(.47+look.tier*.025,.022,6,30),c,0,.07,0);aura.rotation.x=Math.PI/2;}
 body.scale.set(1+(level-1)*.0015,1+(level-1)*.002,1+(level-1)*.0015);
}
export function buildingModel(b,enemy=false){
  const g=new THREE.Group(),type=b.type,sz=TYPES[type].size,red=enemy?0x8e423d:b.level>=8?0x425c77:b.level>=4?0xb27842:C.roof;
  box(g,sz+.25,.17,sz+.25,C.stoneDark,0,.085,0);box(g,sz+.11,.14,sz+.11,C.stone,0,.21,0);
  if(type==='hall'){
    box(g,2.45,1.9,2.7,C.wall,0,1.17,0);box(g,2.55,.21,2.78,C.wood,0,1.9,0);roof(g,2.9,3.1,1.3,0,2.03,0,red);
    box(g,.72,1.04,.12,C.wood,0,.85,1.41);box(g,.78,.1,.16,C.timber,0,1.4,1.43);box(g,.065,.9,.13,C.gold,0,.8,1.47);
    stairs(g,0,1.9,1.1);for(const x of [-.87,.87])windowBlock(g,x,1.26,1.385,.26,.44);
    for(const x of [-1.32,1.32])smallTower(g,x,-1.23,2.35);
    box(g,.27,.85,.28,C.stoneDark,.75,2.75,.5);banner(g,0,3.35,-.22,!enemy);
    for(const x of [-1.2,1.2]){cyl(g,.08,.1,.85,C.wood,x,.65,1.66);sphere(g,.14,0xf6bb55,x,1.2,1.66);}
  }else if(type==='barracks'){
    box(g,2.38,1.23,2.05,C.wall,0,.89,0);roof(g,2.8,2.45,1,0,1.57,0,red);box(g,.95,1.1,.1,C.wood,0,.79,1.065);box(g,2.4,.12,.15,C.wood,0,1.47,1.08);
    for(const x of [-.97,.97])box(g,.13,1.26,.14,C.timber,x,.9,1.08);
    windowBlock(g,-.76,1.03,1.10,.25,.4);windowBlock(g,.76,1.03,1.1,.25,.4);
    const sword1=box(g,.08,.9,.06,0xc4d0c4,-.13,2.05,1.22);sword1.rotation.z=.55;const sword2=box(g,.08,.9,.06,0xc4d0c4,.13,2.05,1.22);sword2.rotation.z=-.55;
    banner(g,-1.23,1.4,-.9,!enemy);barrel(g,1.35,.29,.7);box(g,.8,.15,.8,C.wood,-1,.39,-1.4);
  }else if(type==='mine'){
    rock(g,1.02,0x90937c,0,.91,-.22);rock(g,.6,0xb7b094,-.8,.64,-.55);box(g,1.22,.92,.12,0x3c4036,0,.77,1.0);
    for(const x of [-.65,.65])box(g,.2,1.3,.3,C.wood,x,.91,.92);box(g,1.61,.22,.35,C.wood,0,1.54,.92);
    roof(g,1.7,1.55,.64,0,1.64,.28,red);box(g,.8,.39,.69,C.wood,.1,.5,1.12);
    for(const x of [-.42,.42]){cyl(g,.11,.11,.1,C.iron,x,.33,1.23,8).rotation.z=Math.PI/2;box(g,.055,.04,1.25,C.iron,x,.3,1.02);}
    for(let i=0;i<5;i++)rock(g,.17,C.gold,(i%3)*.19-.15,.76+Math.floor(i/3)*.11,1.15-(i%2)*.18);
    rock(g,.22,C.gold,-.63,.85,.36);rock(g,.15,C.gold,.51,1.12,-.16);barrel(g,-.85,.3,1.03);
  }else if(type==='well'){
    cyl(g,.9,1,.25,C.stoneDark,0,.4,0,10);cyl(g,.82,.85,.95,C.stone,0,.98,0,10);cyl(g,.85,.85,.14,C.wood,0,1.41,0,10);cyl(g,.71,.71,.06,0xbe73cd,0,1.5,0,14);
    for(const x of [-.8,.8])box(g,.15,1.66,.17,C.wood,x,1.66,0);roof(g,2.15,1.5,.7,0,2.52,0,0x586a81);
    cyl(g,.06,.06,1.85,C.wood,0,2.17,0,6).rotation.z=Math.PI/2;box(g,.04,.7,.04,0xc9ba94,0,1.88,0);cyl(g,.19,.14,.3,C.wood,0,1.53,0,8);
    for(const [x,z] of [[.9,.8],[-.8,-.9]]){rock(g,.21,0xa16dc0,x,.56,z);cone(g,.15,.55,0xd9a3e0,x,.82,z,5);}
  }else if(type==='tower'){
    for(const x of [-.51,.51])for(const z of [-.51,.51]){const post=box(g,.18,2.2,.19,C.wood,x,1.36,z);post.rotation.z=x*.05;}
    box(g,1.45,.22,1.42,C.timber,0,2.37,0);box(g,1.5,.63,.12,C.wall,0,2.72,.66);box(g,1.5,.63,.12,C.wall,0,2.72,-.66);
    for(const x of [-.67,.67])box(g,.13,.63,1.3,C.wall,x,2.72,0);
    for(const x of [-.69,.69])for(const z of [-.64,.64])box(g,.17,1.25,.17,C.wood,x,3.0,z);
    const roofM=cone(g,1.2,.84,red,0,3.75,0,4);roofM.rotation.y=Math.PI/4;cone(g,.09,.23,C.gold,0,4.25,0,4);
    for(let i=0;i<6;i++)box(g,.51,.07,.12,0xac9262,0,.48+i*.3,.7);for(const x of [-.27,.27])box(g,.065,1.9,.08,C.wood,x,1.35,.72);
    const beam=box(g,.11,2.05,.1,C.timber,0,1.37,.53);beam.rotation.z=.48;
  }else if(type==='cannon'){
    cyl(g,.85,.96,.3,C.stone,0,.42,0,10);box(g,1.32,.46,1.23,C.wood,0,.82,0);
    for(const x of [-.68,.68]){const wheel=cyl(g,.43,.43,.15,C.timber,x,.73,.05,10);wheel.rotation.z=Math.PI/2;cyl(g,.12,.12,.18,C.gold,x,.73,.05,8).rotation.z=Math.PI/2;}
    cyl(g,.58,.63,.28,C.iron,0,1.05,0,10);
  }else if(type==='storage'){
    box(g,1.93,1.29,1.82,C.wood,0,.94,0);roof(g,2.4,2.2,.88,0,1.64,0,red);
    for(const z of [-.92,.92])for(const x of [-.92,.92])box(g,.14,1.44,.14,C.timber,x,1.02,z);
    for(const y of [.62,1.23])box(g,1.95,.08,.07,0xae8c5b,0,y,.946);
    box(g,.64,.86,.11,C.timber,0,.81,.99);box(g,.15,.21,.06,C.gold,.19,1.08,1.06);
    barrel(g,-1.05,.28,.69);barrel(g,1.02,.28,.65);box(g,.63,.54,.57,0xbc965c,1.08,.55,-.7);box(g,.1,.58,.60,C.wood,1.08,.57,-.7);
  }else if(type==='camp'){
    roof(g,1.45,1.86,1.28,-.43,.30,-.24,0xc0b18a);box(g,1.49,.08,2,C.wood,-.43,.33,-.24);box(g,.04,1.55,.06,C.wood,-.43,1.02,.76);
    cone(g,.43,.28,0xe8bd61,.71,.53,.72,6);cyl(g,.5,.54,.12,0x77786a,.71,.32,.72,9);
    for(let i=0;i<6;i++){const a=i*Math.PI/3;rock(g,.15,C.stone,.71+Math.cos(a)*.43,.44,.72+Math.sin(a)*.43);}
    box(g,.72,.18,.25,C.wood,.76,.38,-.46);banner(g,.8,.88,-.7,!enemy);
  }else if(type==='wall'){
    const level=Math.max(1,Math.min(15,b.level)),palette=[0xa68860,0xb8b5a0,0x879995,0x637a88,0x526777,0x596b98,0x7165a2,0x8660a7,0x955b86,0xa6515e,0xa55e42,0x98753e,0x6f935c,0x4c9d91,0x446b92],height=.64+level*.025;
    box(g,.86,height,.86,palette[level-1],0,.29+height/2,0);
    const trim=level>=10?0xefbc64:level>=5?0xb1bfc7:C.stone;
    for(const x of [-.29,.29])for(const z of [-.29,.29])box(g,.23,.24,.23,trim,x,.40+height,z);
    for(let tier=0;tier<Math.floor(level/3);tier++)box(g,.9,.045,.9,trim,0,.41+tier*.13,0);
    if(level>=4)for(const z of [-.442,.442])box(g,.12,height*.7,.05,trim,0,.35+height/2,z);
    if(level>=8)for(const x of [-.29,.29])cone(g,.12,.26,trim,x,height+.62,0,4);
    if(level>=12)sphere(g,.12,level>=14?0x7deade:0xf6bb73,0,height+.55,0);
  }else if(type==='bomb'){
    cyl(g,.34,.40,.15,C.wood,0,.39,0,8);sphere(g,.24,0x4b5147,0,.62,0);cyl(g,.024,.024,.25,0xd5b385,0,.88,0,4);
  }else if(['mortar','air','tesla','wizard','inferno'].includes(type)){
    cyl(g,.67,.85,.5,C.stone,0,.54,0,8);
    if(type==='mortar'){cyl(g,.49,.58,.68,C.iron,0,1.11,0,10);cyl(g,.34,.34,.03,0x202c29,0,1.46,0,10);}
    else if(type==='air'){for(const x of [-.35,.35])for(const z of [-.3,.3]){cyl(g,.09,.15,1.25,C.iron,x,1.33,z,6);cone(g,.2,.37,C.gold,x,2.1,z,4);}}
    else{cyl(g,.40,.62,type==='inferno'?2.3:1.85,type==='wizard'?0x837494:C.stoneDark,0,1.6,0,8);for(let i=0;i<3;i++)cyl(g,.53,.53,.10,C.gold,0,1.0+i*.62,0,8);sphere(g,.43,type==='inferno'?0xed9b4d:type==='tesla'?0x94cae0:0xc194dd,0,type==='inferno'?3.0:2.7,0);if(type==='wizard')cone(g,.81,.74,0x69577f,0,3.14,0,6);}
  }else if(['laboratory','forge','altar','drill'].includes(type)){
    if(type==='drill'){box(g,1.25,.7,1.25,C.wood,0,.67,0);for(const x of [-.55,.55])box(g,.13,2.3,.15,C.iron,x,1.55,0);cone(g,.22,1.4,0x7e7389,0,1.5,0,7);box(g,1.65,.2,.5,C.iron,0,2.68,0);barrel(g,.7,.29,.8);}
    else if(type==='altar'){cyl(g,1.1,1.2,.25,C.stone,0,.43,0,8);for(const x of [-.85,.85]){cyl(g,.2,.25,1.9,C.wall,x,1.51,0,6);cone(g,.38,.52,C.gold,x,2.7,0,4);}box(g,.8,.9,.6,C.wood,0,.99,-.25);box(g,.78,1.1,.19,0xa16749,0,1.6,-.53);banner(g,0,2.1,-.65,true);}
    else{box(g,1.86,1.1,1.7,C.wall,0,.85,0);roof(g,2.25,2.1,.88,0,1.44,0,type==='laboratory'?0x536c7f:0x876451);windowBlock(g,-.4,1.03,.9);box(g,.51,.85,.1,C.wood,.42,.75,.91);cyl(g,.36,.36,1.0,C.stoneDark,-.62,1.97,-.45,8);sphere(g,.29,type==='laboratory'?0x9bcbcd:0xd6a1dc,-.62,2.52,-.45);barrel(g,1,.28,.58);}
  }else{
    box(g,1.43,1.07,1.36,C.wall,0,.8,0);roof(g,1.92,1.75,.94,0,1.36,0,red);box(g,.46,.81,.08,C.wood,.24,.70,.71);windowBlock(g,-.41,.97,.73,.24,.29);
    box(g,.28,.71,.29,C.stoneDark,.54,1.99,-.38);barrel(g,.79,.28,.67);
  }
  if(b.level>1){for(let i=0;i<Math.min(b.level-1,5);i++)box(g,.15,.10,.13,C.gold,-.34+i*.19,.39,sz/2+.1);}
  buildingLevelDetails(g,b,sz);const root=new THREE.Group();root.add(merged(g));
  if(type==='cannon'){
    const turret=new THREE.Group();cyl(turret,.26,.35,1.4,C.iron,0,0,.35,10).rotation.x=Math.PI/2;const muzzle=cyl(turret,.18,.18,.05,0x172522,0,0,1.08,10);muzzle.rotation.x=Math.PI/2;
    const band=cyl(turret,.31,.31,.12,0x839185,0,0,.77,10);band.rotation.x=Math.PI/2;turret.position.y=1.33;root.add(turret);root.userData.turret=turret;
  }
  if(b.finishAt){const scaffold=new THREE.Group();for(const x of [-sz/2,sz/2])for(const z of [-sz/2,sz/2])box(scaffold,.09,2.4,.09,0xc5a66e,x,1.2,z);for(const y of [.85,1.75])for(const z of [-sz/2,sz/2])box(scaffold,sz+.2,.09,.12,0xd2ba7e,0,y,z);root.add(merged(scaffold));}
  root.position.set(b.x,0,b.z);root.rotation.y=(b.rotation||0)*Math.PI/2;root.userData.building=b;root.traverse(o=>{o.userData.buildingId=b.id;});return root;
}
function tree(parent,x,z,scale,kind,rand){
  const g=new THREE.Group();cyl(g,.13,.24,1.22,C.wood,0,.6,0,6);
  if(kind<.75){const colors=[0x3b6840,0x467949,0x527e42,0x3a6241];for(let i=0;i<3;i++)cone(g,1.1-i*.2,1.7-i*.19,colors[Math.floor(rand()*colors.length)],0,1.4+i*.65,0,6);}
  else{sphere(g,1.11,kind>.94?0xa1a454:0x668c47,0,2,0);sphere(g,.77,0x6d954d,.6,1.8,.2);sphere(g,.8,0x749951,-.54,1.7,.19);}
  g.position.set(x,0,z);g.scale.setScalar(scale);g.rotation.y=rand()*6.28;parent.add(g);
}
function heroBody(body,type,level=1){
  const armor=new THREE.Color(HEROES[type].color).lerp(new THREE.Color(appearance(level).color),Math.min(.65,(level-1)*.012)).getHex(),gold=appearance(level).color,skin=type==='champion'?0x976844:type==='prince'?0x929dbc:0xd8aa7b;
  const round=(r,c,x,y,z)=>mesh(body,new THREE.SphereGeometry(r,12,8),c,x,y,z);
  if(type==='machine'){
    box(body,.87,.79,.63,0x43786f,0,.94,0);box(body,.66,.43,.57,0x4e837b,0,1.54,.03);
    for(const x of [-.25,.25]){box(body,.28,.39,.38,0x384f4a,x,.25,0);round(.19,gold,x,.52,0);round(.23,gold,x*2.1,1.17,0);box(body,.25,.59,.26,0x50837a,x*2.35,.9,.03);round(.05,0x91ead9,x*.65,1.57,.335);}
    for(const y of [.72,1.18])box(body,.92,.08,.68,gold,0,y,0);
    cyl(body,.15,.15,.1,0x8de9d1,0,1,.35,12).rotation.x=Math.PI/2;
    cyl(body,.055,.065,1.42,0x72503c,.68,1.02,.11,8);box(body,.67,.43,.42,0x466763,.68,1.79,.11);box(body,.72,.08,.47,gold,.68,1.68,.11);return;
  }
  const width=type==='king'?.73:type==='queen'?.47:.58;
  cone(body,width*.68,.65,armor,0,.64,0,12);box(body,width,.42,.35,armor,0,.94,0);box(body,width+.03,.065,.38,gold,0,.75,0);
  for(const x of [-.19,.19]){box(body,.19,.40,.26,0x343b38,x,.26,0);box(body,.2,.14,.34,armor,x,.10,.035);round(type==='king'?.20:.14,gold,x*(width/.35),1.04,0);cyl(body,.09,.085,.4,armor,x*1.85,.85,.02,10);round(.085,skin,x*1.85,.65,.09);}
  const cape=cone(body,width*.82,.83,type==='king'?0x842f24:type==='queen'?0x513769:type==='warden'?0x376582:0x343750,0,.72,-.25,5);cape.rotation.x=-.12;
  round(.255,type==='queen'?0x453353:type==='warden'?0xb6c3c5:0x563c2b,0,1.39,-.04);round(.216,skin,0,1.40,.05);
  for(const x of [-.074,.074]){round(.025,0xf4efe0,x,1.445,.247);round(.012,0x213b39,x,1.445,.268);}
  round(.038,skin,0,1.382,.259);
  if(type==='king'||type==='warden'){cone(body,.18,.3,type==='king'?0x8a4025:0xcad1cf,0,1.21,.125,9).rotation.z=Math.PI;for(const side of [-1,1])round(.071,type==='king'?0x9a4927:0xd4d8d5,side*.07,1.29,.23);}
  if(type==='queen')for(const side of [-1,1]){cyl(body,.105,.08,.52,0x46334f,side*.21,1.19,-.085,10);cone(body,.06,.17,skin,side*.25,1.42,.02,3).rotation.z=side*1.0;}
  if(type==='king'){box(body,.095,1.03,.08,0xdbdfe0,.48,1.1,.12);box(body,.34,.075,.11,gold,.48,.76,.12);cyl(body,.29,.29,.08,gold,-.48,.86,.17,10).rotation.x=Math.PI/2;}
  else if(type==='queen'){const bow=mesh(body,new THREE.TorusGeometry(.43,.035,7,20,Math.PI),0xc5c5d3,.43,.98,.13);bow.rotation.z=-Math.PI/2;box(body,.015,.84,.015,0xe6d8c2,.43,.98,.13);}
  else {cyl(body,.035,.045,1.6,gold,.45,1.03,.10,10);if(type==='warden')rock(body,.19,0x94dffa,.45,1.94,.1);else if(type==='prince'){const crescent=mesh(body,new THREE.TorusGeometry(.19,.04,7,18,Math.PI*1.6),0xc5cbd8,.45,1.96,.1);crescent.rotation.z=.6;round(.075,0xb7bdff,.45,1.96,.1);}else {cone(body,.105,.44,gold,.45,1.99,.10,5);const shield=cyl(body,.34,.34,.10,gold,-.42,.91,.17,14);shield.rotation.x=Math.PI/2;round(.095,0xffdf97,-.42,.91,.26);}}
  if(type==='warden'){const halo=mesh(body,new THREE.TorusGeometry(.43,.018,5,32),0x81cce5,0,.05,0);halo.rotation.x=Math.PI/2;}
}
export function makeUnit(type,enemy=false,record={}){
  if(type.includes(':')){const [kind,id]=type.split(':');record={...record,[kind]:true};type=id;}
  const def=unitDefinition({...record,type,hero:!!HEROES[type]}),scale=record.pet?.72:record.siege?1:type==='machine'?1.5:type==='giant'||type==='colossus'?1.45:HEROES[type]?1.1:type==='wyvern'?1.25:.72,g=new THREE.Group(),body=new THREE.Group();
  if(record.siege){
    box(body,1.2,.7,1.9,0x86613e,0,.65,0);for(const x of [-.7,.7])for(const z of [-.65,.65])cyl(body,.3,.3,.18,0x504333,x,.3,z,8).rotation.z=Math.PI/2;
    if(type==='airship'){sphere(body,1.1,0xa85744,0,2,0);box(body,.9,.12,.8,C.gold,0,1.2,0);}else if(type==='catapult'){box(body,.13,1.8,.15,C.wood,0,1.3,0).rotation.x=.8;sphere(body,.25,C.stone,0,1.95,.55);}else{cyl(body,.24,.24,2.6,0xb39b70,0,.9,.1,8).rotation.x=Math.PI/2;cone(body,.4,.6,C.iron,0,.9,1.6,4).rotation.x=Math.PI/2;}
  }else if(record.pet){
    sphere(body,.5,def.color,0,.55,0);sphere(body,.34,def.color,0,.85,.42);cone(body,.16,.5,def.color,-.24,1.1,.4,3);cone(body,.16,.5,def.color,.24,1.1,.4,3);for(const x of [-.28,.28])for(const z of [-.3,.3])box(body,.17,.4,.17,def.color,x,.2,z);for(const x of [-.13,.13])sphere(body,.045,0x162822,x,.9,.73);if(def.flying)for(const side of [-1,1])cone(body,.65,.1,def.color,side*.62,.65,0,3);
  }else if(HEROES[type]){heroBody(body,type,record.level||1);heroLevelDetails(body,record.level||1);
  }else if(type==='giant'||type==='colossus'){
    box(body,.72,.85,.48,0x9b9d8a,0,.87,0);rock(body,.32,0xbcbaa4,0,1.45,0);for(const x of [-.51,.51])rock(body,.26,0x8a927f,x,1.02,0);
    box(body,.29,.39,.37,0x72695a,-.24,.25,0);box(body,.29,.39,.37,0x72695a,.24,.25,0);box(body,.38,.17,.15,0x41696a,0,1.48,.29);
  }else{
    cone(body,.34,.60,def.color,0,.61,0,6);sphere(body,.22,0xdabb90,0,1.05,.02);sphere(body,.25,type==='guardian'?0x727b6d:0x3f6550,0,1.17,-.02);
    box(body,.17,.35,.23,0x544735,-.15,.22,0);box(body,.17,.35,.23,0x544735,.15,.22,0);box(body,.14,.41,.16,0xd1af81,.32,.64,.02);
    if(type==='guardian'||type==='king'){box(body,.10,.70,.09,0xd4dace,.39,.95,.13);box(body,.30,.08,.1,C.gold,.39,.65,.13);box(body,.39,.49,.12,0xa36548,-.33,.68,.19);box(body,.07,.36,.13,C.gold,-.33,.68,.26);}
    else if(['warden','champion','prince'].includes(type)){cyl(body,.04,.04,1.6,C.gold,.4,.95,.1,6);if(type==='warden')sphere(body,.19,0x85c5e7,.4,1.8,.1);else cone(body,.14,.45,0xe5d7af,.4,1.82,.1,4);if(type==='champion')cyl(body,.32,.32,.1,C.gold,-.35,.8,.22,8).rotation.x=Math.PI/2;}
    else{const bow=mesh(body,new THREE.TorusGeometry(.31,.027,4,8,Math.PI),C.wood,.39,.72,.1);bow.rotation.z=-Math.PI/2;box(body,.018,.58,.018,0xd1c39a,.39,.72,.1);}
  }
  if(type==='wyvern'||type==='prince'){for(const side of [-1,1]){const wing=cone(body,.7,.13,def.color,side*.67,.9,-.1,3);wing.rotation.z=side*.25;}}if(HEROES[type]&&type!=='machine'){cyl(body,.25,.24,.085,C.gold,0,1.60,0,12);if(type==='king')for(let i=0;i<5;i++)cone(body,.058,.20,C.gold,Math.sin(i*Math.PI*2/5)*.21,1.73,Math.cos(i*Math.PI*2/5)*.21,5);}
  if(!HEROES[type]&&!record.pet&&!record.siege&&(record.level||1)>1){const l=record.level;for(let j=0;j<Math.min(8,l);j++)box(body,.04,.07,.05,appearance(l*2).color,-.15+j*.04,.7,.24);body.scale.y=1+(l-1)*.012;}g.add(merged(body));g.scale.setScalar(scale);g.userData.level=record.level||1;return g;
}
function healthSprite(){const canvas=document.createElement('canvas');canvas.width=64;canvas.height=8;const texture=new THREE.CanvasTexture(canvas);texture.minFilter=THREE.LinearFilter;const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:false,transparent:true}));sprite.scale.set(1.12,.14,1);sprite.renderOrder=6;sprite.userData={canvas,texture,last:-1};return sprite;}
function drawHealth(sprite,ratio,enemy){const value=Math.round(ratio*60);if(value===sprite.userData.last)return;sprite.userData.last=value;const {canvas,texture}=sprite.userData;const ctx=canvas.getContext('2d');ctx.clearRect(0,0,64,8);ctx.fillStyle='#17201b';ctx.fillRect(0,0,64,8);ctx.fillStyle=enemy?'#e87d5b':'#bde773';ctx.fillRect(2,2,Math.max(0,value),4);texture.needsUpdate=true;}
function disposeGroup(group){group.traverse(o=>{if(o.isMesh){o.geometry.dispose();if(![...materials.values()].includes(o.material))o.material.dispose();}if(o.isSprite){o.material.map?.dispose();o.material.dispose();}});}

export class World{
  constructor(container,callbacks){
    this.container=container;this.callbacks=callbacks;this.scene=new THREE.Scene();this.scene.background=new THREE.Color(0x92b8a7);this.scene.fog=new THREE.Fog(0x92b8a7,100,175);
    this.mobile=innerWidth<650;this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});this.renderer.setPixelRatio(Math.min(devicePixelRatio,this.mobile?1.5:2));this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.08;container.appendChild(this.renderer.domElement);
    this.camera=new THREE.OrthographicCamera(-25,25,20,-20,.1,200);this.target=new THREE.Vector3(0,0,0);this.zoom=1;this.camera.position.set(31,38,31);
    this.scene.add(new THREE.HemisphereLight(0xeaf5ff,0x52643e,1.8));const sun=new THREE.DirectionalLight(0xffedcd,3.0);sun.position.set(-17,34,13);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-30;sun.shadow.camera.right=30;sun.shadow.camera.top=30;sun.shadow.camera.bottom=-30;sun.shadow.camera.near=1;sun.shadow.camera.far=90;sun.shadow.bias=-.00015;sun.shadow.normalBias=.025;sun.shadow.radius=2;this.scene.add(sun);this.sun=sun;
    this.scenery=new THREE.Group();this.scene.add(this.scenery);this.structures=new THREE.Group();this.scene.add(this.structures);this.obstacleGroup=new THREE.Group();this.scene.add(this.obstacleGroup);this.obstacleMap=new Map();this.actors=new THREE.Group();this.scene.add(this.actors);this.particles=new THREE.Group();this.scene.add(this.particles);this.buildingMap=new Map();this.unitMap=new Map();this.effects=[];this.coins=[];this.villagers=[];this.smoke=[];
    this.raycaster=new THREE.Raycaster();this.pointer=new THREE.Vector2();this.groundPlane=new THREE.Plane(new THREE.Vector3(0,1,0),0);this.pointers=new Map();this.clock=new THREE.Clock();
    this.quality='high';this.buildTerrain();this.makeSelection();this.bindInput();this.resize();this.lastT=0;
    this.frame=(time)=>{if(this.stopped)return;const t=time/1000,dt=Math.min(.05,Math.max(0,t-this.lastT||.016));this.lastT=t;this.callbacks.frame?.(dt,t);this.animate(dt,t);this.renderer.render(this.scene,this.camera);this.raf=requestAnimationFrame(this.frame);};this.raf=requestAnimationFrame(this.frame);
    this.resizeHandler=()=>this.resize();window.addEventListener('resize',this.resizeHandler);this.resizeObserver=new ResizeObserver(this.resizeHandler);this.resizeObserver.observe(container);window.addEventListener('gameviewportchange',()=>{this.pointers.clear();this.down=null;this.pinch=null;});this.renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();this.callbacks.error?.('Graphics paused. Reload the game to continue.');});
  }
  buildTerrain(){
    const g=new THREE.Group(),r=seeded(87324);
    box(g,130,1,130,0x6e9650,0,-.64,0);
    for(let x=-24;x<=24;x+=2)for(let z=-24;z<=24;z+=2){const edge=Math.max(Math.abs(x),Math.abs(z));const c=edge<16?[0x83ac57,0x84ad58,0x80a954,0x82ab56][Math.floor(r()*4)]:[0x6e984c,0x70994c,0x759e50,0x6c9549][Math.floor(r()*4)];box(g,2.005,.06,2.005,c,x,-.12+r()*.025,z);}
    // Soft irregular clearing boundary and tiny stones make the village feel settled.
    for(let i=0;i<135;i++){const a=r()*Math.PI*2,rad=11.7+r()*6,x=Math.cos(a)*rad,z=Math.sin(a)*rad;if(z>9&&Math.abs(x)<2.1)continue;rock(g,.08+r()*.16,r()>.5?0xc2c19a:0x829660,x,.015,z).scale.y=.5;}
    // A winding dirt road leads between the buildings and into the woodland.
    for(let z=-11;z<=24;z+=.48){const x=z>8?Math.sin((z-8)*.25)*1.2:Math.sin(z*.45)*.26;const m=box(g,1.47+r()*.2,.035,.59,0xbab087,x,-.055,z);m.rotation.y=Math.sin(z*.25)*.09;}
    for(let x=-8;x<=8;x+=.5)box(g,.55,.027,1.1,0xbeb68c,x,-.04,1.93+Math.sin(x*.32)*.22);
    for(let i=0;i<54;i++){const z=r()*30-8,x=(r()-.5)*1.35;const stone=box(g,.18+r()*.25,.034,.15+r()*.24,0xcbc29d,x,-.01,z);stone.rotation.y=r()*3;}
    // A cool stream skirts the western tree line.
    for(let z=-29;z<=30;z+=1.4){const x=-18+Math.sin(z*.18)*2.2;box(g,3.2,.035,1.52,0x699f93,x,-.04,z);box(g,2.7,.04,1.52,0x72b2ac,x,-.017,z);if(Math.floor(z)%3===0){box(g,.65,.01,.055,0xb3d2b3,x+.5,.008,z);rock(g,.48,0x939b81,x+1.8,.15,z);}}
    // Wooden bridge, low fences, and a path through the forest.
    for(let i=0;i<15;i++)box(g,.34,.13,1.82,0xb09969,-20.1+i*.34,.21,12);
    for(const z of [11.18,12.82]){box(g,5.4,.1,.1,C.wood,-17.5,.78,z);for(let x=-20;x<-14.7;x+=1.25)box(g,.12,.9,.12,C.wood,x,.52,z);}
    for(let i=0;i<164;i++){
      const x=(r()-.5)*65,z=(r()-.5)*65;if(Math.abs(x)<17&&Math.abs(z)<17)continue;if(z>10&&Math.abs(x)<2.8)continue;if(Math.abs(x-(-18+Math.sin(z*.18)*2.2))<2)continue;tree(g,x,z,.62+r()*.73,r(),r);
    }
    // Patches of wildflowers stay well away from interactive building footprints.
    for(let i=0;i<220;i++){const x=(r()-.5)*30,z=(r()-.5)*30;if(Math.abs(x)<9.9&&Math.abs(z)<9.9)continue;const m=cone(g,.04+r()*.04,.2+r()*.2,0x94b76a,x,.1,z,3);m.rotation.z=(r()-.5)*.4;if(r()>.75)sphere(g,.06,0xe1c679,x,.3,z);}
    this.scenery.add(merged(g));
    const clouds=new THREE.Group();for(let i=0;i<7;i++){const cloud=new THREE.Group();for(let j=0;j<5;j++){const p=sphere(cloud,1.8+r()*1.5,0xf1eed7,j*2.2,0,r()*1.5);p.scale.y=.44;}cloud.position.set(-35+r()*65,16+r()*7,-25+r()*42);cloud.scale.setScalar(.65+r()*.5);cloud.userData.speed=.1+r()*.12;clouds.add(merged(cloud));}
    // Clouds are subtle translucent shadows rather than opaque foreground obstructions.
    clouds.children.forEach((m,i)=>{m.material.transparent=true;m.material.opacity=.11;m.castShadow=false;m.receiveShadow=false;m.userData.speed=.12+i*.015;});this.clouds=clouds;this.scene.add(clouds);
  }
  wallSegment(g,x,z,rotated){const wall=new THREE.Group();box(wall,1.13,.55,.35,0xa5aa86,0,.29,0);for(const v of [-.37,0,.37])box(wall,.19,.22,.38,0xbfc4a1,v,.65,0);wall.position.set(x,0,z);if(rotated)wall.rotation.y=Math.PI/2;g.add(wall);}
  makeSelection(){
    this.selection=new THREE.Group();const lineMaterial=new THREE.LineBasicMaterial({color:0xffe098,transparent:true,opacity:.95});const points=[];for(let i=0;i<=64;i++){const a=i/64*Math.PI*2;points.push(new THREE.Vector3(Math.cos(a),.035,Math.sin(a)));}this.selection.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),lineMaterial));
    const disk=new THREE.Mesh(new THREE.RingGeometry(.92,1,64),new THREE.MeshBasicMaterial({color:0xffda7a,transparent:true,opacity:.26,side:THREE.DoubleSide,depthWrite:false}));disk.rotation.x=-Math.PI/2;disk.position.y=.023;this.selection.add(disk);this.scene.add(this.selection);this.selection.visible=false;
    this.placement=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial({color:0xa3f083,transparent:true,opacity:.48,side:THREE.DoubleSide,depthWrite:false}));this.placement.rotation.x=-Math.PI/2;this.placement.position.y=.06;this.scene.add(this.placement);this.placement.visible=false;
    const borderPoints=[[-8.7,-8.7],[8.7,-8.7],[8.7,8.7],[-8.7,8.7],[-8.7,-8.7]].map(([x,z])=>new THREE.Vector3(x,.09,z));this.battleBorder=new THREE.Line(new THREE.BufferGeometry().setFromPoints(borderPoints),new THREE.LineDashedMaterial({color:0xff8970,dashSize:.48,gapSize:.22,transparent:true,opacity:.9}));this.battleBorder.computeLineDistances();this.scene.add(this.battleBorder);this.battleBorder.visible=false;this.buildGrid=new THREE.GridHelper(29,58,0xd2dfa0,0xbbdba0);this.buildGrid.position.y=.04;this.buildGrid.material.transparent=true;this.buildGrid.material.opacity=.24;this.scene.add(this.buildGrid);this.buildGrid.visible=false;
  }
  rebuild(buildings,battle=false){
    disposeGroup(this.structures);this.structures.clear();disposeGroup(this.actors);this.actors.clear();this.buildingMap.clear();this.unitMap.clear();this.coins=[];this.villagers=[];this.battle=battle;this.battleBorder.visible=battle;this.obstacleGroup.visible=!battle;this.selection.visible=false;
    for(const b of buildings){const model=buildingModel(b,battle);this.structures.add(model);this.buildingMap.set(b.id,model);
      if(battle){const hp=healthSprite();hp.position.y=b.type==='hall'?4.9:b.type==='tower'?4.6:3.3;model.add(hp);model.userData.hp=hp;drawHealth(hp,1,true);}
      else if(['mine','well'].includes(b.type)){
        const coin=new THREE.Group();const isGold=b.type==='mine';if(isGold){const c=cyl(coin,.27,.27,.10,C.gold,0,0,0,12);c.rotation.x=Math.PI/2;cyl(coin,.18,.18,.12,0xf2d578,0,0,0,12).rotation.x=Math.PI/2;}else{const drop=mesh(coin,new THREE.OctahedronGeometry(.30),0xd292dc);drop.scale.y=1.35;}
        coin.position.set(0,b.type==='well'?3.4:2.8,0);model.add(coin);this.coins.push({coin,b,base:coin.position.y});
      }
    }
    if(!battle){for(let i=0;i<7;i++){const v=makeUnit(i%3===0?'ranger':'guardian');v.scale.multiplyScalar(.66);this.actors.add(v);this.villagers.push({model:v,phase:i*.94,route:i%3,speed:.15+i*.025});}}
  }
  replaceBuilding(b){const old=this.buildingMap.get(b.id);if(old){disposeGroup(old);this.structures.remove(old);}this.rebuild([...this.buildingMap.values()].map(v=>v.userData.building).filter(x=>x.id!==b.id).concat(b),false);}
  setSelection(b){this.selected=b;if(b){const radius=TYPES[b.type].size*.7;this.selection.position.set(b.x,0,b.z);this.selection.scale.set(radius,1,radius);this.selection.visible=true;}else this.selection.visible=false;}
  setPlacement(type,state,movingId){
    if(this.ghost){disposeGroup(this.ghost);this.scene.remove(this.ghost);this.ghost=null;}
    this.placing=type?{type,state,movingId,rotation:0}:null;this.placement.visible=!!type;this.buildGrid.visible=!!type;
    if(type){const original=state.buildings.find(b=>b.id===movingId);this.ghost=buildingModel({type,id:'ghost',level:original?.level||1,x:0,z:0});this.ghost.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.material.transparent=true;o.material.opacity=.62;o.material.depthWrite=false;o.castShadow=false;o.userData.buildingId=null;}});this.scene.add(this.ghost);this.placement.scale.set(TYPES[type].size+.35,TYPES[type].size+.35,1);
      let spot=original?[original.x,original.z]:null;for(let z=0;z<14&&!spot;z+=.5)for(let x=-8;x<=8;x+=.5)if(canPlace(state,type,x,z,movingId)){spot=[x,z];break;}this.updatePlacement(...(spot||[0,0]));}
  }
  updatePlacement(x,z){if(!this.placing)return;const p=this.placing;p.x=Math.round(x*2)/2;p.z=Math.round(z*2)/2;p.valid=canPlace(p.state,p.type,p.x,p.z,p.movingId);this.placement.position.set(p.x,.07,p.z);this.placement.material.color.setHex(p.valid?0xa7f17c:0xff8161);this.ghost.position.set(p.x,.04,p.z);this.ghost.rotation.y=p.rotation*Math.PI/2;this.callbacks.placement?.({...p});}
  rotatePlacement(){if(this.placing){this.placing.rotation=(this.placing.rotation+1)%4;this.updatePlacement(this.placing.x,this.placing.z);}}
  setVillageHeroes(heroes,battle,buildings=[]){
    this.heroVisitors??=new THREE.Group();if(!this.heroVisitors.parent)this.scene.add(this.heroVisitors);this.heroVisitors.visible=!battle;
    const camps=buildings.filter(b=>b.type==='camp'&&!b.constructing),camp=camps[0]||buildings.find(b=>b.type==='altar')||{x:0,z:0};
    const sig=JSON.stringify([Object.entries(heroes).map(([k,h])=>[k,h.level,!!h.finishAt,h.recoverAt>Date.now()]),camp.x,camp.z]);if(this.heroVisitSig===sig)return;this.heroVisitSig=sig;
    disposeGroup(this.heroVisitors);this.heroVisitors.clear();let index=0;
    for(const [type,h]of Object.entries(heroes))if(h.level){const a=-Math.PI/2+(index++)*.65,model=makeUnit(type,false,{hero:true,level:h.level});model.position.set(camp.x+Math.cos(a)*2.3,.05,camp.z+Math.sin(a)*2.3);model.rotation.y=-a;model.userData.baseY=.05;model.userData.resting=!!h.finishAt||h.recoverAt>Date.now();model.traverse(o=>o.userData.heroType=type);if(model.userData.resting){model.scale.y*=.75;model.rotation.z=.08;}this.heroVisitors.add(model);}
  }
  setCampArmy(s,battle){
    this.campArmy??=new THREE.Group();if(!this.campArmy.parent)this.scene.add(this.campArmy);this.campArmy.visible=!battle;
    const camps=s.buildings.filter(b=>b.type==='camp'&&!b.constructing);const sig=JSON.stringify([s.army,s.research,camps.map(c=>[c.x,c.z,c.level])]);if(this.campArmySig===sig)return;this.campArmySig=sig;disposeGroup(this.campArmy);this.campArmy.clear();if(!camps.length)return;
    let j=0;for(const [type,count]of Object.entries(s.army))for(let k=0;k<Math.min(count,5)&&j<30;k++){
      if(!TROOPS[type])continue;const camp=camps[j%camps.length],slot=Math.floor(j/camps.length),col=slot%5,row=Math.floor(slot/5);const model=makeUnit(type,false,{level:s.research?.[type]||1});model.scale.multiplyScalar(.72);model.position.set(camp.x+(col-2)*.62,.03,camp.z+1.55+row*.68);model.rotation.y=.3;model.userData.phase=j*.8;model.traverse(o=>o.userData.campUnit=true);this.campArmy.add(model);j++;
    }
  }

  paintPortrait(canvas,type,level=1){const key=type+':'+level;
    try{this.portraits??=new Map();if(!this.portraits.has(key)){this.portraitRenderer??=new THREE.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true});const renderer=this.portraitRenderer;renderer.setSize(180,210,false);renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;const scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xfff7da,0x344b45,2.7));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(3,5,4);scene.add(light);const model=makeUnit(type,false,{level});model.rotation.y=.45;scene.add(model);const camera=new THREE.PerspectiveCamera(33,180/210,.1,50);camera.position.set(3,2.9,5);camera.lookAt(0,1,0);renderer.render(scene,camera);const cached=document.createElement('canvas');cached.width=180;cached.height=210;cached.getContext('2d').drawImage(renderer.domElement,0,0);this.portraits.set(key,cached);if(this.portraits.size>24)this.portraits.delete(this.portraits.keys().next().value);disposeGroup(scene);}canvas.getContext('2d').drawImage(this.portraits.get(key),0,0,canvas.width,canvas.height);}catch{canvas.setAttribute('aria-label',type+' character');}
  }
  setObstacles(obstacles){const sig=JSON.stringify(obstacles.map(o=>[o.id,!!o.finishAt]));if(sig===this.obstacleSig)return;this.obstacleSig=sig;disposeGroup(this.obstacleGroup);this.obstacleGroup.clear();this.obstacleMap.clear();for(const o of obstacles){const g=new THREE.Group();if(o.type==='tree')tree(g,0,0,o.finishAt?.65:.75,.2,seeded(o.x*173+1301));else if(o.type==='gem-box'){box(g,1.02,.55,.88,0x6e4d35,0,.35,0);for(const x of [-.36,.36])box(g,.10,.65,.94,0xefca72,x,.38,0);box(g,1.08,.15,.93,0xb28b4c,0,.68,0);for(let n=0;n<5;n++)mesh(g,new THREE.OctahedronGeometry(.20),0x86f2ad,(n-2)*.17,.84+(n%2)*.19,0).scale.y=1.5;}else{rock(g,.75,0x929b85,0,.4,0);rock(g,.42,C.stone,.45,.23,.26);}const m=merged(g);m.position.set(o.x,0,o.z);m.userData.obstacleId=o.id;this.obstacleGroup.add(m);this.obstacleMap.set(o.id,m);}}
  setBattleBounds(bounds=8.7){const s=bounds/8.7;this.battleBorder.scale.set(s,1,s);}
  point(clientX,clientY){const rect=this.renderer.domElement.getBoundingClientRect(),p2=gamePoint(clientX,clientY,rect,isRotated());this.pointer.set(p2.x*2-1,1-p2.y*2);this.raycaster.setFromCamera(this.pointer,this.camera);const p=new THREE.Vector3();return this.raycaster.ray.intersectPlane(this.groundPlane,p);}
  pick(clientX,clientY){const p=this.point(clientX,clientY);const hits=this.raycaster.intersectObjects([...this.structures.children,...(!this.battle?[...this.obstacleGroup.children,...(this.heroVisitors?.children||[]),...(this.campArmy?.children||[])]:[])],true);const hit=hits.find(h=>h.object.userData.buildingId||h.object.userData.obstacleId||h.object.userData.heroType||h.object.userData.campUnit);return {point:p,buildingId:hit?.object.userData.buildingId,obstacleId:hit?.object.userData.obstacleId,heroType:hit?.object.userData.heroType,campUnit:hit?.object.userData.campUnit};}
  bindInput(){
    const canvas=this.renderer.domElement;
    canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});this.down={x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,moved:false};if(this.placing){const p=this.point(e.clientX,e.clientY);this.down.ghost=p&&Math.hypot(p.x-this.placing.x,p.z-this.placing.z)<TYPES[this.placing.type].size*.8;}if(this.pointers.size===2){const [a,b]=[...this.pointers.values()];this.pinch={dist:Math.hypot(a.x-b.x,a.y-b.y),zoom:this.zoom};}});
    canvas.addEventListener('pointermove',e=>{
      if(this.placing&&(!this.down||this.down.ghost)){const p=this.point(e.clientX,e.clientY);if(p)this.updatePlacement(p.x,p.z);if(this.down?.ghost){this.down.moved=true;return;}}
      if(!this.pointers.has(e.pointerId)){const picked=this.pick(e.clientX,e.clientY);this.callbacks.hover?.(picked.buildingId);return;}
      this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
      if(this.pointers.size===2&&this.pinch){const [a,b]=[...this.pointers.values()];this.setZoom(this.pinch.zoom*Math.hypot(a.x-b.x,a.y-b.y)/Math.max(1,this.pinch.dist));if(this.down)this.down.moved=true;return;}
      if(!this.down)return;const {x:dx,y:dy}=gameDelta(e.clientX-this.down.lastX,e.clientY-this.down.lastY,isRotated());if(Math.hypot(e.clientX-this.down.x,e.clientY-this.down.y)>6)this.down.moved=true;
      if(this.down.moved){const scale=(this.camera.top-this.camera.bottom)/this.container.clientHeight;this.target.x-=dx*scale*.707+dy*scale*.64;this.target.z+=dx*scale*.707-dy*scale*.64;this.target.x=Math.max(-13,Math.min(13,this.target.x));this.target.z=Math.max(-13,Math.min(13,this.target.z));this.positionCamera();}
      this.down.lastX=e.clientX;this.down.lastY=e.clientY;
    });
    canvas.addEventListener('pointerup',e=>{const click=this.down&&!this.down.moved&&this.pointers.size===1;this.pointers.delete(e.pointerId);if(this.pointers.size<2)this.pinch=null;if(click)this.callbacks.click?.(this.pick(e.clientX,e.clientY));if(!this.pointers.size)this.down=null;});
    canvas.addEventListener('pointercancel',e=>{this.pointers.delete(e.pointerId);this.down=null;this.pinch=null;});
    canvas.addEventListener('wheel',e=>{e.preventDefault();this.setZoom(this.zoom*Math.exp(-e.deltaY*.0012));},{passive:false});
    canvas.addEventListener('contextmenu',e=>e.preventDefault());
  }
  resize(){const w=Math.max(1,this.container.clientWidth),h=Math.max(1,this.container.clientHeight);this.renderer.setPixelRatio(renderScale(this.quality,w,h,devicePixelRatio,this.renderer.capabilities.maxTextureSize));this.renderer.setSize(w,h);this.aspect=w/h;const half=(this.aspect<.8?30:this.container.clientHeight<500?19:22)/this.zoom;this.camera.left=-half*this.aspect;this.camera.right=half*this.aspect;this.camera.top=half;this.camera.bottom=-half;this.camera.updateProjectionMatrix();this.positionCamera();}
  positionCamera(){this.camera.position.copy(this.target).add(new THREE.Vector3(31,38,31));this.camera.lookAt(this.target);this.camera.updateMatrixWorld();}
  setZoom(z){this.zoom=Math.max(.68,Math.min(2.35,z));this.resize();}
  recenter(){this.target.set(0,0,0);this.zoom=1;this.resize();}
  project(b){const p=new THREE.Vector3(b.x,b.type==='hall'?4.5:b.type==='tower'?4.6:3.1,b.z).project(this.camera);return {x:(p.x+1)*this.container.clientWidth/2,y:(1-p.y)*this.container.clientHeight/2};}
  addUnit(u){const model=makeUnit(u.type,false,u);model.position.set(u.x,.04,u.z);const hp=healthSprite();hp.position.y=u.type==='giant'?2.5:2.1;model.add(hp);model.userData.hp=hp;this.actors.add(model);this.unitMap.set(u.id,model);this.burst(u.x,.3,u.z,0xe8d4a1,8);}
  updateBattle(battle){
    for(const b of battle.buildings){const m=this.buildingMap.get(b.id);if(!m)continue;if(b.hp<=0&&!m.userData.dead){m.userData.dead=true;m.children.forEach(c=>c.visible=false);this.burst(b.x,1,b.z,0xcaba8d,22);const rubble=new THREE.Group(),rand=seeded(b.x*143+b.z*917+612);for(let i=0;i<9;i++){const p=rock(rubble,.22+rand()*.39,0x969780,(rand()-.5)*TYPES[b.type].size,.25,(rand()-.5)*TYPES[b.type].size);p.scale.y=.65;}const remnant=merged(rubble);remnant.name='rubble';m.add(remnant);}
      if(b.hp>0){if(m.userData.dead){m.userData.dead=false;const rubble=m.getObjectByName('rubble');if(rubble){disposeGroup(rubble);m.remove(rubble);}m.children.forEach(c=>c.visible=true);}drawHealth(m.userData.hp,b.hp/b.maxHp,true);if(m.userData.turret&&b.facing!==undefined)m.userData.turret.rotation.y=b.facing;}
    }
    for(const u of battle.units){const m=this.unitMap.get(u.id);if(!m)continue;if(u.hp<=0){if(m.visible){this.burst(u.x,.4,u.z,0xb3aa87,6);m.visible=false;}continue;}m.position.set(u.x,(unitDefinition(u).flying?1.3:0)+(u.moving?Math.abs(Math.sin(this.lastT*11+u.phase))*.095:0),u.z);m.rotation.y=u.facing||0;if(u.swing)m.rotation.z=Math.sin(u.swing*18)*.14;else m.rotation.z=0;drawHealth(m.userData.hp,u.hp/u.maxHp,false);}
  }
  projectile(x,y,z,tx,ty,tz,color){const m=sphere(this.particles,.09,color,x,y,z);m.castShadow=false;this.effects.push({mesh:m,kind:'projectile',from:new THREE.Vector3(x,y,z),to:new THREE.Vector3(tx,ty,tz),age:0,life:.24});}
  damageLabel(damage,x,y,z){
    if(!damage||this.effects.filter(e=>e.kind==='damage').length>=18)return;
    const canvas=document.createElement('canvas');canvas.width=192;canvas.height=80;const ctx=canvas.getContext('2d');ctx.font='bold 54px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineWidth=8;ctx.strokeStyle='#231814';ctx.strokeText('-'+Math.round(damage),96,40);ctx.fillStyle='#ffe4a4';ctx.fillText('-'+Math.round(damage),96,40);
    const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas),transparent:true,depthTest:false}));sprite.position.set(x,y,z);sprite.scale.set(2.4,1,1);sprite.renderOrder=12;this.particles.add(sprite);this.effects.push({mesh:sprite,kind:'damage',age:0,life:1.1});
  }
  burst(x,y,z,color,count=12){for(let i=0;i<count;i++){const m=box(this.particles,.10+Math.random()*.10,.12,.12,color,x,y,z);m.castShadow=false;this.effects.push({mesh:m,kind:'particle',vx:(Math.random()-.5)*5,vy:1+Math.random()*3,vz:(Math.random()-.5)*5,age:0,life:.45+Math.random()*.6});}}
  spellEffect(type,x,z){if(type==='thunder'){this.lightning(x,z);return;}const color=type==='heal'?0xa7e292:type==='freeze'?0xaadced:0xd09ee8;const ring=new THREE.Mesh(new THREE.RingGeometry(3.35,4,64),new THREE.MeshBasicMaterial({color,transparent:true,opacity:.45,side:THREE.DoubleSide,depthWrite:false}));ring.rotation.x=-Math.PI/2;ring.position.set(x,.08,z);this.particles.add(ring);this.effects.push({mesh:ring,kind:'ring',age:0,life:type==='freeze'?6:8});this.burst(x,.6,z,color,22);}
  lightning(x,z){
    const pts=[new THREE.Vector3(x,11,z),new THREE.Vector3(x-.8,7,z+.1),new THREE.Vector3(x+.55,7.4,z),new THREE.Vector3(x-.4,3.5,z),new THREE.Vector3(x+.23,3.8,z),new THREE.Vector3(x,.2,z)];const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0xeee0ff}));this.particles.add(line);this.effects.push({mesh:line,kind:'flash',age:0,life:.34});this.burst(x,.7,z,0xd7b5f2,34);const ring=new THREE.Mesh(new THREE.RingGeometry(.2,3.5,48),new THREE.MeshBasicMaterial({color:0xc3a3ed,transparent:true,opacity:.5,side:THREE.DoubleSide,depthWrite:false}));ring.rotation.x=-Math.PI/2;ring.position.set(x,.06,z);this.particles.add(ring);this.effects.push({mesh:ring,kind:'ring',age:0,life:.5});
  }
  animate(dt,t){
    for(const item of this.coins){item.coin.position.y=item.base+Math.sin(t*2.1)*.13;item.coin.rotation.y=t*.9;item.coin.visible=(item.b.stored||0)>3&&!item.b.finishAt;}
    for(const v of this.villagers){const a=t*v.speed+v.phase;if(v.route===0){v.model.position.set(Math.sin(a)*.32,.015,Math.cos(a)*7);v.model.rotation.y=Math.sin(a)>0?Math.PI:0;}else if(v.route===1){v.model.position.set(Math.cos(a)*6,.015,2+Math.sin(a)*.28);v.model.rotation.y=Math.sin(a)>0?-Math.PI/2:Math.PI/2;}else{v.model.position.set(2.6+Math.cos(a)*1.5,.015,6.7+Math.sin(a)*.6);v.model.rotation.y=-a;}v.model.position.y+=Math.abs(Math.sin(t*7+v.phase))*.035;}
    for(const model of this.heroVisitors?.children||[])if(!model.userData.resting)model.position.y=.05+Math.sin(t*2+model.position.x)*.035;for(const model of this.campArmy?.children||[])model.position.y=.03+Math.abs(Math.sin(t*2+model.userData.phase))*.025;
    for(const cloud of this.clouds.children){cloud.position.x+=dt*cloud.userData.speed;if(cloud.position.x>50)cloud.position.x=-50;}
    for(let i=this.effects.length-1;i>=0;i--){const e=this.effects[i];e.age+=dt;const u=e.age/e.life;if(e.kind==='damage'){e.mesh.position.y+=dt*.9;e.mesh.material.opacity=Math.max(0,1-u);}else if(e.kind==='projectile'){e.mesh.position.lerpVectors(e.from,e.to,u);e.mesh.position.y+=Math.sin(u*Math.PI)*.6;}else if(e.kind==='particle'){e.mesh.position.x+=e.vx*dt;e.mesh.position.y+=e.vy*dt;e.mesh.position.z+=e.vz*dt;e.vy-=8*dt;e.mesh.rotation.x+=dt*4;e.mesh.scale.setScalar(Math.max(.05,1-u));}else if(e.kind==='ring'){e.mesh.material.opacity=.5*(1-u);e.mesh.scale.setScalar(.6+u*.5);}else if(e.kind==='flash')e.mesh.visible=Math.floor(t*30)%2===0;
      if(e.age>=e.life){this.particles.remove(e.mesh);if(e.kind==='damage')e.mesh.material.map.dispose();else e.mesh.geometry.dispose();if(![...materials.values()].includes(e.mesh.material))e.mesh.material.dispose();this.effects.splice(i,1);}}
    if(this.selection.visible)this.selection.children[1].material.opacity=.20+Math.sin(t*3)*.08;
  }
  setQuality(value){this.quality=graphicsProfile(value);const size=Math.min(GRAPHICS[this.quality].shadow,this.renderer.capabilities.maxTextureSize);if(this.sun.shadow.mapSize.x!==size){this.sun.shadow.map?.dispose();this.sun.shadow.map=null;this.sun.shadow.mapSize.set(size,size);}this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.needsUpdate=true;this.resize();}
}
