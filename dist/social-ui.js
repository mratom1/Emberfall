import {escapeHtml as e} from './features.js?v=14.0.0';
export class SocialUI{
 constructor(f){f.profile=()=>this.show().catch(err=>f.b.toast(err.message,true));this.f=f;this.api=f.api;document.addEventListener('click',event=>{const b=event.target.closest('[data-social]');if(b&&!b.disabled)this.handle(b).catch(err=>f.b.toast(err.message,true));});document.addEventListener('submit',event=>{if(event.target.id==='social-search'){event.preventDefault();this.show(event.target.elements.q.value).catch(err=>f.b.toast(err.message,true));}});}
 async show(q=''){
 const f=this.f,u=this.api.user;let data;
 if(this.api.online)data=await this.api.request('/social?q='+encodeURIComponent(q));
 const s=f.b.root(),p=data?.profile||{name:'Local village',hall:s.buildings.find(b=>b.type==='hall')?.level||1,glory:s.glory},button=(label,action,target,extra='')=>`<button class="btn" data-social="${action}" data-target="${e(target||'')}" ${extra}>${label}</button>`;
 const row=(p,buttons)=>`<article class="social-row"><div><strong>${e(p.name)}</strong><small>${e(p.code||'')} · Town Hall ${p.hall||1} · ${p.glory||0} trophies</small></div>${buttons}</article>`;
 let body=`<div class="account-profile"><span class="auth-emblem">E</span><div><h3>${e(p.name)}</h3><strong class="profile-code">${e(p.code||'Device-only village')}</strong><p>Town Hall ${p.hall} · ${p.glory||0} trophies</p><small>${u?.registered?'Signed in'+(u.providers?.length?' · '+e(u.providers.join(' / ')):''):this.api.online?'Guest account':'Playing on this device'}</small></div></div><button class="btn" data-v2="account">${u?.registered?'Manage account':'Sign in / save account'}</button>`;
 if(!data)body+='<p>Connect to your game server to receive a permanent Player ID, find friends and join clans.</p>';
 else{
 body+=`<form id="social-search" class="social-search"><input name="q" value="${e(q)}" maxlength="40" placeholder="Player ID, clan ID or name" aria-label="Find players or clans"><button class="btn btn-gold">Search</button></form>`;
 if(q)body+=`<h3>Players</h3>${data.players.map(x=>row(x,x.id===p.id?'':button('Add friend','request',x.id)+(p.clanId?button('Invite to clan','invite',x.id):''))).join('')||'<p>No matching players.</p>'}`;
 body+=`<h3>Friends & requests</h3>${data.friends.map(x=>row(x,(x.status==='pending'&&x.incoming?button('Accept','accept',x.id):`<small>${x.status==='accepted'?'Friends':'Request sent'}</small>`)+button(x.status==='accepted'?'Remove':'Dismiss','remove',x.id)+(x.status==='accepted'&&p.clanId?button('Invite','invite',x.id):''))).join('')||'<p>No friends added yet.</p>'}`;
 body+=data.invites.map(x=>`<article class="social-row"><div>Clan invitation: ${e(x.name)}<small>${e(x.code)}</small></div><button class="btn" data-social="join-invite" data-clan="${e(x.clan_id)}">Join</button><button class="btn" data-social="decline-invite" data-clan="${e(x.clan_id)}">Decline</button></article>`).join('');
 body+=`<h3>Clans</h3>${data.clans.map(x=>`<article class="social-row"><div><strong>${e(x.name)}</strong><small>${e(x.code)} · ${x.members}/30 members</small></div>${!p.clanId?button('Join clan','join',x.id):x.id===p.clanId?'<span>Your clan</span>':''}</article>`).join('')||'<p>No matching clans.</p>'}<button class="btn" data-v2="social">Clan management</button><button class="btn" data-x="frontiers" data-tab="war">Clan wars</button>`;
 }
 f.show('profile','Player profile',body,'YOUR KINGDOM');
 }
 async handle(b){if(b.dataset.social==='profile')return this.show();b.disabled=true;try{if(b.dataset.social==='join'){const r=await this.api.request('/clans',{method:'POST',data:{action:'join',id:b.dataset.target}});this.api.user=r.user;}else await this.api.request('/social',{method:'POST',data:{action:b.dataset.social,target:b.dataset.target,clanId:b.dataset.clan}});await this.show();}finally{if(b.isConnected)b.disabled=false;}}
}
