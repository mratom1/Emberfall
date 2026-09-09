// Original characters, progression gates and village land. Shared by client and server.
export const EXTRA_HEROES={
 sentinel:{name:'Iron Sentinel',role:'tank',icon:'shield',desc:'An armored guardian. Bulwark heals nearby allies and empowers their next charge.',hp:2450,damage:85,speed:1.45,range:1.3,rate:1.1,unlock:2,barracks:2,color:0x6c91b0,weapon:'shield'},
 oracle:{name:'Tide Oracle',role:'support',icon:'waves',desc:'A tide mage. Restoring Tide heals every living ally.',hp:1250,damage:95,speed:2,range:5.2,rate:1.05,unlock:3,barracks:2,color:0x37bfc1,weapon:'staff',ability:'heal'},
 berserker:{name:'Rift Berserker',role:'fighter',icon:'axe',desc:'A dual-axe fighter. Rift Fury restores health and enrages nearby allies.',hp:2100,damage:155,speed:2.1,range:1.3,rate:1.1,unlock:4,barracks:3,color:0xc25239,weapon:'axes'},
 huntress:{name:'Grove Huntress',role:'ranged',icon:'bow-arrow',desc:'A forest marksman. Piercing Volley strikes standing defenses.',hp:1350,damage:148,speed:2.5,range:5.8,rate:1.05,unlock:5,barracks:3,color:0x4a995a,weapon:'bow',ability:'volley',female:true},
 alchemist:{name:'Copper Alchemist',role:'support',icon:'flask-conical',desc:'An inventive potion master. Vital Elixir restores the army.',hp:1550,damage:130,speed:1.8,range:4.5,rate:1.2,unlock:5,barracks:4,color:0xbe8554,weapon:'potion',ability:'heal'},
 duelist:{name:'Gale Duelist',role:'fighter',icon:'sword',desc:'A swift spellblade. Wind Rush empowers nearby allies.',hp:1750,damage:165,speed:3,range:1.6,rate:.8,unlock:6,barracks:4,color:0x9ec8db,weapon:'rapier'},
 pyromancer:{name:'Cinder Mage',role:'ranged',icon:'flame',desc:'A flame sorcerer. Cinder Burst damages defenses around her.',hp:1400,damage:190,speed:1.9,range:5,rate:1.3,unlock:7,barracks:5,color:0xca4d37,weapon:'fire',ability:'burst',female:true},
 beastmaster:{name:'Thorn Keeper',role:'support',icon:'leaf',desc:'A woodland protector. Rejuvenation restores the army.',hp:1900,damage:130,speed:1.8,range:4.5,rate:1.2,unlock:8,barracks:6,color:0x697b3c,weapon:'antlers',ability:'heal'},
 assassin:{name:'Nightblade',role:'fighter',icon:'moon',desc:'A masked shadow fighter. Shadow Rush empowers nearby allies.',hp:1500,damage:190,speed:3.2,range:1.4,rate:.72,unlock:8,barracks:7,color:0x765299,weapon:'daggers',female:true},
 frostguard:{name:'Frostguard',role:'tank',icon:'snowflake',desc:'An ice-armored paladin. Deep Winter freezes nearby defenses.',hp:2800,damage:130,speed:1.4,range:1.5,rate:1.25,unlock:9,barracks:7,color:0x84c1de,weapon:'ice',ability:'freeze'},
 templar:{name:'Sun Templar',role:'fighter',icon:'sun',desc:'A radiant spear knight. Solar Lance strikes the nearest defenses.',hp:2250,damage:170,speed:2.2,range:3.7,rate:1,unlock:10,barracks:8,color:0xe0c06b,weapon:'spear',ability:'shield',target:'defense',female:true},
 runesmith:{name:'Rune Smith',role:'tank',icon:'hammer',desc:'A dwarven hammer master. Rune Fury heals and empowers allies.',hp:3000,damage:180,speed:1.4,range:1.4,rate:1.45,unlock:11,barracks:9,color:0x9e704b,weapon:'hammer'},
 captain:{name:'Sky Captain',role:'flying',icon:'bird',desc:'A winged lancer. Skyfall freezes nearby defenses.',hp:2000,damage:165,speed:2.5,range:4.1,rate:1.1,unlock:12,barracks:10,color:0x687ab8,weapon:'wings',ability:'freeze',flying:true,female:true},
 wraith:{name:'Sand Wraith',role:'ranged',icon:'wind',desc:'A desert spellblade. Sandstorm hits standing defenses.',hp:1850,damage:205,speed:2.5,range:5.1,rate:1.15,unlock:13,barracks:11,color:0xc6aa70,weapon:'scimitar',ability:'volley'},
 regent:{name:'Astral Regent',role:'flying',icon:'sparkles',desc:'A cosmic sovereign. Starfall strikes nearby defenses.',hp:2600,damage:215,speed:2,range:5.5,rate:1.25,unlock:15,barracks:13,color:0x9c75c5,weapon:'orb',ability:'burst',flying:true}
};
export const LAND_REGIONS=[
 {id:'home',name:'Home clearing',unlock:1,x1:-14.5,x2:14.5,z1:-14.5,z2:14.5},
 {id:'meadow',name:'Westbank Meadow',unlock:3,x1:-36,x2:-23,z1:4,z2:17},
 {id:'terrace',name:'Pine Terrace',unlock:7,x1:-36,x2:-23,z1:-13,z2:4},
 {id:'heights',name:'Stone Heights',unlock:11,x1:-49,x2:-36,z1:-13,z2:17}
];
export function unlockedLand(s){const level=s.buildings.find(b=>b.type==='hall')?.level||1;return LAND_REGIONS.filter(r=>r.id==='home'||!s.realm&&level>=r.unlock);}
export function landContains(regions,x,z,padding=0){
 if(!Number.isFinite(x)||!Number.isFinite(z)||!Number.isFinite(padding)||padding<0)return false;
 if(!padding)return regions.some(r=>x>=r.x1&&x<=r.x2&&z>=r.z1&&z<=r.z2);
 const left=x-padding,right=x+padding,bottom=z-padding,top=z+padding;
 const cuts=[left,right,...regions.flatMap(r=>[r.x1,r.x2]).filter(v=>v>left&&v<right)].sort((a,b)=>a-b);
 for(let i=1;i<cuts.length;i++){
  if(cuts[i]===cuts[i-1])continue;const mid=(cuts[i]+cuts[i-1])/2;
  const spans=regions.filter(r=>r.x1<=mid&&r.x2>=mid).sort((a,b)=>a.z1-b.z1);let covered=bottom;
  for(const r of spans){if(r.z1>covered)break;if(r.z2>covered)covered=r.z2;}
  if(covered<top)return false;
 }
 return true;
}
