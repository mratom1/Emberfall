import * as M from '../dist/model.js';
import * as R from '../dist/raids.js';
import * as X from '../dist/expansion.js';
let seed;function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
const oldRandom=Math.random,results=[];Math.random=random;
try{for(const hall of [3,7,11,15])for(const sample of [1,2,3])for(const readiness of ['developing','maxed'])for(const strategy of ['clustered','split']){
 seed=sample;const s=M.initialState(1700000000000);M.advance(s,1700000000000);for(const b of s.buildings)b.level=hall;
 for(let i=1;i<M.TYPES.camp.max;i++)s.buildings.push({id:'camp-'+i,type:'camp',level:hall,x:i*5,z:8});
 s.buildings.push({id:'altar',type:'altar',level:hall,x:-8,z:8});s.army=Object.fromEntries(Object.keys(M.TROOPS).map(k=>[k,0]));
 let spaces=M.armyCapacity(s);for(const k of ['giant','ranger','guardian']){const n=k==='guardian'?spaces:Math.floor(spaces/3/M.TROOPS[k].space);s.army[k]=n;spaces-=n*M.TROOPS[k].space;s.research[k]=Math.min(15,hall);}
 for(const k of X.HOME_HEROES)s.heroes[k].level=readiness==='maxed'?M.heroMaxLevel(s,k):Math.min(10,M.heroMaxLevel(s,k));
 const defender=R.botVillage(s,()=>.5,1700000000000);
 for(const mode of ['before','after']){
  seed=sample;const a=structuredClone(s),b=R.configureBattle(M.createBattle(a,0),defender);
  if(mode==='before')b.combatVersion=8;
  if(mode==='before')for(const building of b.buildings)building.hp=building.maxHp=M.TYPES[building.type].hp*(1+(building.level-1)*.25);
  const totalHp=b.buildings.reduce((n,x)=>n+x.hp,0);let i=0;const position=()=>{const k=i++,side=k%4,t=-9+(Math.floor(k/4)%19);return strategy==='clustered'?[0,17]:[[t,17],[17,t],[t,-17],[-17,t]][side];};
  for(const [k,n]of Object.entries(a.army))for(let j=0;j<n;j++){const r=M.deploy(a,b,k,...position());if(r.error)throw Error(r.error);}
  for(const [k,h]of Object.entries(a.heroes))if(h.level){const r=M.deployHero(a,b,k,...position());if(r.error)throw Error(r.error);}
  let abilities=false;while(!b.ended&&b.elapsed<151){M.stepBattle(b,.1);if(b.elapsed>=12&&!abilities){abilities=true;for(const k of X.HOME_HEROES)M.heroAbility(b,k);}}
  results.push({hall,sample,readiness,strategy,mode,heroes:Object.values(s.heroes).filter(h=>h.level).length,armySpaces:M.armySize(s.army),totalBuildingHp:totalHp,seconds:Number(b.elapsed.toFixed(1)),destruction:b.stats.percent,stars:b.stats.stars});
 }
}}finally{Math.random=oldRandom;}
console.log(JSON.stringify({method:'Deterministic 150-second server combat, matched bot village, legal camp capacity, all unlocked heroes at level 10 or legal maximum, max research for TH, abilities at 12 seconds; three seeds per tier. Balance smoke test, not player win-rate or server-load benchmark.',results},null,2));
