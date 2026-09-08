export function requestId(){if(globalThis.crypto?.randomUUID)return crypto.randomUUID();const bytes=new Uint8Array(16);if(globalThis.crypto?.getRandomValues)crypto.getRandomValues(bytes);else for(let i=0;i<16;i++)bytes[i]=Math.floor(Math.random()*256);return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}

export class Connection {
  constructor({fetcher = (...args) => fetch(...args), pause = ms => new Promise(resolve => setTimeout(resolve, ms)), onStatus = () => {}} = {}) {
    this.online = false;
    this.csrf = '';
    this.user = null;
    this.config = {packs: [], payments: false};
    this.chain = Promise.resolve();
    this.fetcher = fetcher;
    this.pause = pause;
    this.onStatus = onStatus;
    this.status = 'connecting';
    this.pending = null;
  }
  setStatus(status) { this.status = status; this.onStatus(status); }
  async request(path, {method = 'GET', data} = {}) {
    let response, result;
    try {
      response = await this.fetcher('/api' + path, {method, credentials: 'same-origin', headers: {...(data ? {'Content-Type': 'application/json'} : {}), ...(this.csrf ? {'X-CSRF-Token': this.csrf} : {})}, ...(data ? {body: JSON.stringify(data)} : {}), signal: AbortSignal.timeout(18000)});
      result = await response.json();
    } catch {
      if (!this.pending) this.setStatus('disconnected');
      throw Object.assign(new Error('Connection lost. Your server village is safe. Reconnect and retry.'), {retryable: true});
    }
    if (!response.ok) throw Object.assign(new Error(result.error || 'Request failed.'), {status: response.status, retryable: [502, 503, 504].includes(response.status)});
    if (result.csrf) this.csrf = result.csrf;
    if (result.user) this.user = result.user;
    if (!this.pending) this.setStatus('connected');
    return result;
  }
  async connect() {
    let response;
    const serverOnly = globalThis.document?.querySelector('meta[name="emberfall-runtime"]')?.content === 'server';
    try { response = await this.fetcher('/api/config', {signal: AbortSignal.timeout(8000)}); }
    catch (e) { if (serverOnly) throw e; this.setStatus('standalone'); return null; }
    if (response.status === 404 && !serverOnly) { this.setStatus('standalone'); return null; }
    if (!response.ok) throw new Error('The game server is unavailable. Please reload.');
    const data = await response.json();
    if (!data.server) { if (serverOnly) throw new Error('The game server returned an invalid configuration.'); this.setStatus('standalone'); return null; }
    this.config = data;
    this.online = true;
    return this.request('/session', {method: 'POST', data: {}});
  }
  enqueue(job) {
    const result = this.chain.then(job);
    this.chain = result.catch(() => {});
    return result;
  }
  command(action) {
    const payload = {...action, requestId: requestId()}, owner = this.user?.id;
    return this.enqueue(() => {
      if (this.pending) throw new Error('Your previous action needs confirmation. Use Retry connection first.');
      if (owner !== this.user?.id) throw new Error('Your account changed. Please choose the action again.');
      this.pending = {payload, owner, createdAt: Date.now()};
      return this.sendPending();
    });
  }
  retryPending() { return this.enqueue(() => this.pending ? this.sendPending() : this.request('/state')); }
  async sendPending() {
    const pending = this.pending;
    if (pending.owner !== this.user?.id || Date.now() - pending.createdAt >= 23 * 3600000) {
      this.pending = null;
      this.setStatus('connected');
      throw new Error('This action is too old or belongs to another account. Refresh your village before continuing.');
    }
    for (let attempt = 0; attempt < 3; attempt++) {
      if (pending.owner !== this.user?.id) { this.pending = null; this.setStatus('connected'); throw new Error('Your account changed before confirmation. Refresh your village.'); }
      this.setStatus(attempt ? 'reconnecting' : 'saving');
      try {
        const result = await this.request('/command', {method: 'POST', data: pending.payload});
        this.pending = null;
        this.setStatus('connected');
        return result;
      } catch (e) {
        if (!e.retryable) { this.pending = null; this.setStatus('connected'); throw e; }
        if (attempt === 2) { this.setStatus('unconfirmed'); throw new Error('Waiting for server confirmation. Use Retry connection; your action will not be charged twice.'); }
        this.setStatus('reconnecting');
        await this.pause(600 * 2 ** attempt);
      }
    }
  }
}
