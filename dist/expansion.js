import {EXTRA_HEROES} from './content.js?v=13.0.0';
import * as M from './model.js?v=13.0.0';

export const EQUIPMENT={
 ironheart:{name:'Ironheart',icon:'shield',desc:'More hit points.',hp:.08},
 emberblade:{name:'Ember Blade',icon:'sword',desc:'Stronger attacks.',damage:.06},
 longbow:{name:'Moon Bow',icon:'bow-arrow',desc:'Damage and attack range.',damage:.035,range:.06},
 lifebloom:{name:'Lifebloom',icon:'heart',desc:'Regenerates health in battle.',regen:3},
 frostcharm:{name:'Frost Charm',icon:'snowflake',desc:'Hero abilities also freeze nearby defenses.',freeze:.5},
 stormboots:{name:'Storm Boots',icon:'footprints',desc:'Faster movement.',speed:.025},
 wardstone:{name:'Wardstone',icon:'shield-half',desc:'Hero abilities briefly protect nearby allies.',ward:.35},
 sunmedal:{name:'Sun Medal',icon:'sun',desc:'Improves damage and hit points.',hp:.04,damage:.025}
};
export const PETS={
 fox:{name:'Ember Fox',icon:'paw-print',desc:'A swift companion that attacks buildings.',hp:500,damage:35,speed:3.2,range:1.1,rate:.8,color:0xe39753,unlock:2},
 owl:{name:'Moon Owl',icon:'bird',desc:'A flying ranged companion.',hp:400,damage:45,speed:2.8,range:4.4,rate:1.1,color:0xa091c0,flying:true,unlock:3},
 yak:{name:'Iron Yak',icon:'mountain',desc:'A tough companion that crushes walls.',hp:1500,damage:55,speed:1.6,range:1.1,rate:1.3,color:0xa79677,wallPower:4,unlock:4},
 sprite:{name:'Life Sprite',icon:'heart-pulse',desc:'Follows and heals its hero.',hp:450,damage:0,speed:2.7,range:3,rate:1,color:0x83cdad,flying:true,heal:30,unlock:5}
};
export const SIEGE={
 ram:{name:'Fortress Ram',icon:'axe',desc:'Crushes walls and releases three Guardians when destroyed.',hp:2800,damage:125,speed:1.2,range:1.2,rate:1.3,color:0xb7854b,wallPower:5,cost:650,time:12,unlock:4},
 airship:{name:'Ember Airship',icon:'cloud',desc:'Flies over walls and drops three Rangers when destroyed.',hp:1900,damage:140,speed:1.8,range:3.5,rate:1.4,color:0x976952,flying:true,cost:850,time:16,unlock:5},
 catapult:{name:'Siege Catapult',icon:'target',desc:'Long-range shells damage clusters of buildings.',hp:1500,damage:165,speed:.9,range:8,rate:2.2,color:0x927c56,splash:2.4,cost:1000,time:20,unlock:6}
};
export const HOME_HEROES=['king','queen','prince','warden','champion',...Object.keys(EXTRA_HEROES)];
export const BUILDER_TYPES=['mine','well','storage','camp','barracks','tower','cannon','mortar','tesla','air','wall','bomb','laboratory'];
export const SEASON_TASKS=[{id:'victory',title:'Win 3 battles',stat:'wins',goal:3,xp:150},{id:'build',title:'Construct 3 buildings',stat:'built',goal:3,xp:120},{id:'training',title:'Train 15 troops',stat:'trained',goal:15,xp:100},{id:'upgrades',title:'Complete 3 upgrades',stat:'upgraded',goal:3,xp:130}];
const month=now=>new Date(now).toISOString().slice(0,7),day=now=>new Date(now).toISOString().slice(0,10);
const error=message=>({error:message});
export function builderState(now){
 return {realm:'builder',version:3,gold:5000,elixir:4500,dark:0,gems:0,glory:0,builders:1,lastTick:now,army:{guardian:12,ranger:8,giant:2},queue:[],research:{guardian:2,ranger:2},researchQueue:[],heroes:{machine:{level:1,recoverAt:0}},spells:{},spellQueue:[],obstacles:M.seedObstacles().slice(0,10),nextObstacleAt:now+1800000,cleared:{},claimed:[],stats:{built:0,trained:0,wins:0,upgraded:0},settings:{},buildings:[{id:'bh',type:'hall',x:0,z:0,level:1},{id:'bb',type:'barracks',x:5,z:0,level:1},{id:'bm',type:'mine',x:-5,z:1,level:1,stored:100},{id:'bw',type:'well',x:0,z:5,level:1,stored:100},{id:'bs',type:'storage',x:-4,z:-5,level:1},{id:'bc',type:'camp',x:5,z:5,level:1},{id:'bt',type:'tower',x:4,z:-5,level:1},{id:'bn',type:'cannon',x:-5,z:5,level:1}]};
}
export function ensure(s,now=Date.now()){
 if(s.realm)return s;
 for(const k of HOME_HEROES)s.heroes[k]??={level:0,recoverAt:0};
 s.expansion??={};const e=s.expansion;
 e.ore??=250;e.medals??=0;e.capitalGold??=1000;e.equipment??=Object.fromEntries(Object.keys(EQUIPMENT).map(k=>[k,1]));e.loadouts??={};e.pets??=Object.fromEntries(Object.keys(PETS).map(k=>[k,{level:0}]));e.petAssignments??={};e.siege??={ram:0,airship:0,catapult:0};e.siegeQueue??=[];e.builder??=builderState(now);
 for(const k of HOME_HEROES)e.loadouts[k]??=['ironheart','emberblade'];
 if(e.season?.id!==month(now))e.season={id:month(now),points:0,claimed:[]};
 if(e.daily?.id!==day(now))e.daily={id:day(now),baseline:{...s.stats},claimed:[]};
 s.version=3;return s;
}
export function advance(s,now,events){
 if(s.realm)return;ensure(s,now);const e=s.expansion;
 e.builder.gems=s.gems;M.advance(e.builder,now);s.gems=e.builder.gems;
 for(const [id,p]of Object.entries(e.pets))if(p.finishAt&&p.finishAt<=now){p.level++;delete p.finishAt;events.push({kind:'pet',id});}
 if(e.equipmentWork?.finishAt<=now){e.equipment[e.equipmentWork.id]++;delete e.equipmentWork;events.push({kind:'equipment'});}
 for(const q of e.siegeQueue.filter(q=>q.finishAt<=now))e.siege[q.type]++;e.siegeQueue=e.siegeQueue.filter(q=>q.finishAt>now);
}
export function equipmentCost(level){return 40*level*level;}
export function heroStats(s,type,level){
 const e=s.expansion,base=M.HEROES[type],n=1+(level-1)*.09,stats={hp:base.hp*n,damage:base.damage*n,speed:base.speed,range:base.range,regen:0,freeze:0,ward:0};
 for(const id of e?.loadouts[type]||[]){const d=EQUIPMENT[id],l=e.equipment[id]||1;for(const key of ['hp','damage'])stats[key]+=d[key]?base[key]*d[key]*l:0;for(const key of ['speed','range'])stats[key]+=d[key]?base[key]*d[key]*l:0;for(const key of ['regen','freeze','ward'])stats[key]+=(d[key]||0)*l;}
 return stats;
}
export function action(s,a,now){
 if(a.realm==='builder'&&!s.realm){ensure(s,now);const b=s.expansion.builder,allowed=['build','move','upgrade','train','research','collect','clear','skip','claim','machine-upgrade','train-batch','army-preset-save','army-preset-train','wall-upgrade'];if(!allowed.includes(a.type))return error('Use this action in your home village.');
  if(a.type==='build'&&!BUILDER_TYPES.includes(a.building))return error('This building belongs in your home village.');
  const target=b.buildings.find(x=>x.id===a.id);if(a.type==='upgrade'&&target?.level>=10)return error('Builder Base maximum level is 10.');
  if(a.type==='machine-upgrade'){const h=b.heroes.machine,c=500*(h.level+1);if(h.finishAt)return error('Battle Machine is upgrading.');if(h.recoverAt>now)return error('Battle Machine is recovering.');if(h.level>=M.hallLevel(b)*5)return error('Upgrade Builder Hall first.');if(b.elixir<c)return error('Not enough builder elixir.');b.elixir-=c;h.startedAt=now;h.finishAt=now+(20+h.level*8)*1000;return {ok:true};}
  b.gems=s.gems;const r=M.applyAction(b,{...a,realm:undefined},now);s.gems=b.gems;return r;
 }
 if(s.realm)return undefined;ensure(s,now);const e=s.expansion;
 if(a.type==='equipment-equip'){
  if(!HOME_HEROES.includes(a.hero)||!s.heroes[a.hero].level||![0,1].includes(a.slot)||!Object.hasOwn(EQUIPMENT,a.item))return error('Choose an unlocked hero, equipment and slot.');
  if(e.loadouts[a.hero][1-a.slot]===a.item)return error('Choose two different equipment pieces.');e.loadouts[a.hero][a.slot]=a.item;return {ok:true};
 }
 if(a.type==='equipment-upgrade'){
  if(!Object.hasOwn(EQUIPMENT,a.item))return error('Unknown equipment.');if(e.equipmentWork)return error('One equipment upgrade at a time.');const l=e.equipment[a.item],cost=equipmentCost(l);if(l>=18)return error('Maximum equipment level reached.');if(e.ore<cost)return error('Earn ore from raids or season rewards.');e.ore-=cost;e.equipmentWork={id:a.item,finishAt:now+(10+l*5)*1000};return {ok:true};
 }
 if(a.type==='pet-upgrade'){
  const d=PETS[a.pet],p=e.pets[a.pet];if(!Object.hasOwn(PETS,a.pet))return error('Unknown pet.');if(M.hallLevel(s)<d.unlock)return error('Requires Town Hall '+d.unlock+'.');if(Object.values(e.pets).some(p=>p.finishAt))return error('Another pet is training.');if(p.level>=10)return error('Maximum pet level reached.');const c=100*(p.level+1);if(s.dark<c)return error('Not enough dark elixir.');s.dark-=c;p.finishAt=now+(20+p.level*10)*1000;return {ok:true};
 }
 if(a.type==='pet-assign'){
  if(!HOME_HEROES.includes(a.hero)||!s.heroes[a.hero].level)return error('Unlock this hero first.');if(a.pet!=='none'&&(!Object.hasOwn(PETS,a.pet)||!e.pets[a.pet].level||e.pets[a.pet].finishAt))return error('Train this pet first.');if(a.pet!=='none')for(const h of HOME_HEROES)if(e.petAssignments[h]===a.pet)delete e.petAssignments[h];if(a.pet==='none')delete e.petAssignments[a.hero];else e.petAssignments[a.hero]=a.pet;return {ok:true};
 }
 if(a.type==='siege-build'){
  const d=SIEGE[a.siege];if(!Object.hasOwn(SIEGE,a.siege))return error('Unknown siege machine.');if(M.hallLevel(s)<d.unlock)return error('Requires Town Hall '+d.unlock+'.');if(Object.values(e.siege).reduce((a,b)=>a+b,0)+e.siegeQueue.length>=3)return error('Siege storage is full (3).');if(s.elixir<d.cost)return error('Not enough elixir.');s.elixir-=d.cost;e.siegeQueue.push({type:a.siege,finishAt:Math.max(now,e.siegeQueue.at(-1)?.finishAt||0)+d.time*1000});return {ok:true};
 }
 if(a.type==='daily-claim'){
  const task=SEASON_TASKS.find(q=>q.id===a.id);if(!task||e.daily.claimed.includes(a.id)||(s.stats[task.stat]||0)-(e.daily.baseline[task.stat]||0)<task.goal)return error('Challenge is not complete.');e.daily.claimed.push(a.id);e.season.points+=task.xp;e.ore+=30;return {ok:true};
 }
 if(a.type==='season-claim'){
  const tier=Number(a.tier);if(!Number.isInteger(tier)||tier<1||tier>20||e.season.points<tier*100||e.season.claimed.includes(tier))return error('Season reward is not ready.');e.season.claimed.push(tier);e.ore+=50+tier*5;e.capitalGold+=100;return {ok:true};
 }
 if(a.type==='medal-exchange'){
  const deals={ore:{cost:20,amount:200},capitalGold:{cost:15,amount:500}},d=deals[a.item];if(!Object.hasOwn(deals,a.item)||e.medals<d.cost)return error('Not enough raid medals.');e.medals-=d.cost;e[a.item]+=d.amount;return {ok:true};
 }
 return undefined;
}
export function wallet(s,b){return b.practice?b.trainingState:b.realm==='builder'?s.expansion.builder:s;}
export function enrichBattle(s,b){
 if(!s.realm)ensure(s);b.siegeStock={...(s.expansion?.siege||{})};b.heroLoadouts=structuredClone(s.expansion?.loadouts||{});b.petStock={};
 for(const [hero,pet]of Object.entries(s.expansion?.petAssignments||{})){const p=s.expansion.pets[pet];if(p.level&&!p.finishAt)b.petStock[hero]={type:pet,level:p.level};}return b;
}
export function createModeBattle(s,mode,now=Date.now()){
 ensure(s,now);let b;
 if(mode==='training'){
  const training=M.initialState(now);ensure(training,now);for(const k of HOME_HEROES)training.heroes[k]={level:5,recoverAt:0};training.army={guardian:15,ranger:12,giant:4,wyvern:2};training.spells={thunder:3,heal:3,rage:3,freeze:3};training.expansion.siege={ram:1,airship:1,catapult:1};for(const [i,k]of HOME_HEROES.entries()){const p=Object.keys(PETS)[i%4];training.expansion.pets[p].level=3;training.expansion.petAssignments[k]=p;}
  b=M.createBattle(training,2);b.practice=true;b.trainingState=training;b.enemy.name='Hero Training Grounds';
 }else if(mode==='builder'){
  const v=s.expansion.builder,index=Object.keys(v.cleared).length?Math.max(...Object.keys(v.cleared).map(Number))+1:0;b=M.createBattle(v,index);b.realm='builder';b.enemy.name='Nightfall Outpost '+(index+1);b.enemy.gold*=2;b.enemy.elixir*=2;
 }else return {error:'Unknown battle mode.'};return {battle:b};
}
export function addPet(s,b,hero){const p=b.petStock?.[hero.type];if(!p)return;const d=PETS[p.type],boost=1+(p.level-1)*.15;b.units.push({id:'u'+b.units.length,type:p.type,pet:true,owner:hero.id,x:hero.x+1,z:hero.z,hp:d.hp*boost,maxHp:d.hp*boost,damage:d.damage*boost,cooldown:0,phase:0});delete b.petStock[hero.type];}
export function deploySiege(s,b,type,x,z){
 if(!Object.hasOwn(SIEGE,type)||!b.siegeStock?.[type]||b.ended||b.siegeDeployed)return error('One siege machine can deploy per battle.');if(!M.canDeploy(b,x,z))return error('Deploy outside standing buildings or inside a cleared area.');
 const d=SIEGE[type],u={id:'u'+b.units.length,type,siege:true,x,z,hp:d.hp,maxHp:d.hp,damage:d.damage,cooldown:0,phase:0};b.units.push(u);b.siegeStock[type]--;wallet(s,b).expansion.siege[type]--;b.siegeDeployed=true;b.started=true;return {unit:u};
}
export function combatTick(b,dt){
 for(const u of [...b.units]){
  if(u.hp>0){if(u.regen)u.hp=Math.min(u.maxHp,u.hp+u.regen*dt);u.ward=Math.max(0,(u.ward||0)-dt);
   if(u.pet&&PETS[u.type].heal){const owner=b.units.find(h=>h.id===u.owner&&h.hp>0)||b.units.find(h=>h.hp>0&&!h.pet);if(owner){const dx=owner.x-u.x,dz=owner.z-u.z,d=Math.hypot(dx,dz);u.moving=d>2;if(d>2){u.x+=dx/d*PETS[u.type].speed*dt;u.z+=dz/d*PETS[u.type].speed*dt;}if(d<4)owner.hp=Math.min(owner.maxHp,owner.hp+PETS[u.type].heal*dt);}}
  }else if(u.siege&&!u.released){u.released=true;const type=u.type==='airship'?'ranger':'guardian';for(let i=0;i<3;i++){const d=M.TROOPS[type];b.units.push({id:'u'+b.units.length,type,x:u.x+(i-1)*.6,z:u.z,hp:d.hp,maxHp:d.hp,damage:d.damage,cooldown:0,phase:0});}}
 }
}
export function extraAbility(b,u){for(const a of b.units)if(a.hp>0&&Math.hypot(a.x-u.x,a.z-u.z)<5)a.ward=Math.max(a.ward||0,u.wardPower||0);if(u.freeze)for(const d of b.buildings)if(Math.hypot(d.x-u.x,d.z-u.z)<5)d.frozen=Math.max(d.frozen||0,u.freeze);}
export function reward(s,b,result){
 if(b.practice)return;ensure(s);const e=s.expansion;if(result.stars){const ore=15+result.stars*10,capitalGold=40+result.stars*30;e.ore+=ore;e.capitalGold+=capitalGold;e.season.points+=20*result.stars;result.ore=ore;result.capitalGold=capitalGold;}
}
