import {escapeHtml as e} from './features.js?v=9.0.0';
import {nativeApp, openExternal} from './native.js?v=9.0.0';
const names = {google:'Google', facebook:'Facebook'};
export class AccountUI {
  constructor(features) {
    this.f = features; this.api = features.api; this.active = null; this.timer = null;
    features.account = () => this.show();
    document.addEventListener('click', event => {
      const button = event.target.closest('[data-oauth]'); if(!button || button.disabled) return;
      if(button.dataset.oauth === 'cancel') this.cancel();
      else if(button.dataset.oauth === 'switch') this.show(true);
      else this.start(button.dataset.oauth, button.dataset.mode);
    });
    document.addEventListener('visibilitychange', () => {if(!document.hidden && this.active && !this.polling) {clearTimeout(this.timer); this.poll();}});
  }
  show(switchAccount = false) {
    const u = this.api.user, mode = u?.registered && !switchAccount ? 'link' : 'signin';
    const connected = u?.providers || [];
    const password = `<form id="account-form" class="account-form"><label>Username<input id="account-name" autocomplete="username" minlength="3" maxlength="24" placeholder="Your chief name"></label><label>Password<input id="account-password" type="password" autocomplete="${switchAccount?'current-password':'new-password'}" minlength="10" maxlength="128" placeholder="At least 10 characters"></label><div class="panel-actions">${!u?.registered?'<button class="btn btn-gold" data-v2="register">Save this village</button>':''}<button class="btn" data-v2="login">Sign in</button></div></form>`;
    let body = `<div class="account-profile"><span class="auth-emblem">E</span><div><small>${u?.registered?'VILLAGE ACCOUNT':'YOUR NEXT CHAPTER'}</small><h3>${u?.registered?e(u.name):'Keep your kingdom.'}</h3><p>${u?.registered?'Your village follows you across devices.':'Save your progress and return from any device.'}</p></div></div>`;
    if(!this.api.online) body += '<p class="account-notice">You are playing on this device. Connect to your kingdom server to sign in and play with others.</p>';
    else if(this.active) body += this.waiting();
    else {
      body += `<p class="modal-intro">${mode==='link'?'Link another way to sign in to this village.':u?.registered?'Signing in opens the village saved to that account.':'Choose an account. A new account saves this village; an existing account opens its saved village.'}</p><div class="provider-buttons">${Object.entries(names).map(([id,name]) => {const enabled = this.api.config.oauth?.[id]?.enabled, linked = mode==='link' && connected.includes(id);return `<button class="provider-button provider-${id}" data-oauth="${id}" data-mode="${mode}" ${!enabled||linked?'disabled':''}><span class="provider-letter" aria-hidden="true">${id==='google'?'G':'f'}</span><span>${linked?name+' connected':(mode==='link'?'Connect ':'Continue with ')+name}${!enabled?'<small>Not available on this server yet</small>':''}</span></button>`;}).join('')}</div>`;
      if(!u?.registered || switchAccount) body += `<details class="password-option"><summary>Use username and password</summary>${password}</details>`;
      if(u?.registered && !switchAccount) {
        if(u.hasPassword) body += '<details class="password-option"><summary>Change password</summary><form id="password-form" class="account-form"><label>Current password<input id="current-password" type="password" autocomplete="current-password"></label><label>New password<input id="new-password" type="password" autocomplete="new-password" minlength="10" maxlength="128"></label><button class="btn" data-v2="change-password">Update password</button></form></details>';
        body += '<div class="account-actions"><button class="btn" data-oauth="switch">Use another account</button><button class="btn" data-v2="logout">Sign out</button></div>';
      }
    }
    this.f.show('account', 'Your kingdom, everywhere', body, 'EMBERFALL · ACCOUNT');
  }
  waiting() {return `<div class="signin-wait" role="status"><span class="signin-spinner"></span><h3>Finish in ${names[this.active.provider]}</h3><p>Your browser is open. Come back here after signing in.</p><a class="btn" href="${e(this.active.authorizationUrl)}" target="_blank" rel="noopener noreferrer">Open sign-in again</a><button class="btn" data-oauth="cancel">Cancel</button></div>`;}
  async start(provider, mode) {
    if(this.active || !names[provider]) return;
    if(this.api.pending) return this.f.b.toast('Confirm your pending village action before signing in.', true);
    let popup; if(!nativeApp()) {popup = window.open('about:blank', '_blank'); if(popup) popup.opener = null;}
    try {
      await this.api.chain;
      const result = await this.api.request('/auth/oauth/start', {method:'POST', data:{provider,mode}});
      this.active = {...result, provider}; openExternal(result.authorizationUrl, popup); this.show(); this.timer = setTimeout(() => this.poll(), 1800);
    } catch(error) {popup?.close(); this.active = null; this.f.b.toast(error.message, true);}
  }
  async poll() {
    if(!this.active || this.polling) return;
    if(Date.now() >= this.active.expiresAt) {this.active=null; this.f.b.toast('Sign-in expired. Please try again.',true); return this.show();}
    this.polling = true; const active = this.active;
    try {
      // Serialize with commands so an account switch cannot inherit pending spending.
      const result = await this.api.enqueue(async () => {
        if(this.api.pending) return {status:'pending'};
        return this.api.request('/oauth/poll', {method:'POST', data:{id:active.id,pollToken:active.pollToken}});
      });
      if(result.status === 'complete') {this.active = null; this.f.b.apply(result); this.f.b.toast('Account connected. Your village is ready.'); this.show();}
    } catch(error) {
      if(!error.retryable) {this.active = null; this.f.b.toast(error.message,true); this.show();}
    } finally {this.polling = false; if(this.active === active) this.timer = setTimeout(() => this.poll(), 2000);}
  }
  async cancel() {
    if(this.polling) return this.f.b.toast('Finishing the sign-in check. Please try again in a moment.');
    const a=this.active; this.active=null; clearTimeout(this.timer);
    if(a) try {await this.api.request('/oauth/poll', {method:'POST', data:{id:a.id,pollToken:a.pollToken,cancel:true}});} catch {}
    this.show();
  }
}
