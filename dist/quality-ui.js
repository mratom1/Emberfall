import * as M from './model.js?v=11.0.0';
import * as Q from './quality.js?v=11.0.0';
import {escapeHtml as esc} from './features.js?v=11.0.0';

const icon = name => `<i data-lucide="${name}"></i>`;
const time = finish => { const s = Math.max(0, Math.ceil((finish - Date.now()) / 1000)); return s >= 3600 ? `${Math.floor(s / 3600)}h ${Math.ceil(s % 3600 / 60)}m` : s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`; };

export class QualityUI {
  constructor(bridge) {
    this.b = bridge;
    this.slot = 0;
    this.signature = '';
    document.getElementById('work-button').addEventListener('click', () => this.work());
    document.getElementById('connection-status').addEventListener('click', async () => {
      try { const result = await this.b.api.retryPending(); this.b.apply(result); await this.b.sync(); }
      catch (e) { this.b.toast(e.message, true); }
    });
    this.b.api.onStatus = status => this.status(status);
    this.status(this.b.api.status);
    document.addEventListener('click', e => {
      const button = e.target.closest('[data-q]');
      if (!button || button.disabled) return;
      this.handle(button).catch(error => this.b.toast(error.message, true));
    });
  }
  status(status) {
    const el = document.getElementById('connection-status');
    el.dataset.status = status;
    el.hidden = ['standalone', 'connected'].includes(status);
    el.disabled = ['connecting', 'saving', 'reconnecting'].includes(status);
    el.textContent = {connecting: 'Connecting…', saving: 'Saving…', reconnecting: 'Reconnecting…', disconnected: 'Retry connection', unconfirmed: 'Confirm pending action · Retry connection'}[status] || '';
  }
  presets(slot = this.slot) {
    if (this.b.realm() === 'capital') return;
    this.slot = slot;
    const s = this.b.village(), saved = s.armyPresets?.[slot];
    this.b.showModal('presets', this.b.header(this.b.realm() === 'builder' ? 'BUILDER BASE' : 'HOME VILLAGE', 'Army presets') + `<div class="modal-body"><p class="modal-intro">Save three armies for each village. Quick train adds only missing troops and includes troops already in your queue.</p><div class="preset-tabs">${Array.from({length: 3}, (_, i) => `<button class="btn ${i === slot ? 'btn-gold' : ''}" data-q="slot" data-slot="${i}">${esc(s.armyPresets?.[i]?.name || 'Army ' + (i + 1))}</button>`).join('')}</div><label class="preset-name">Army name<input id="preset-name" maxlength="32" value="${esc(saved?.name || 'Army ' + (slot + 1))}"></label><div class="preset-grid">${Object.entries(M.TROOPS).map(([type, d]) => `<label class="preset-troop">${icon(d.icon)}<span>${d.name}<small>${M.troopUnlocked(s, type) ? d.space + ' camp spaces each' : 'Barracks level ' + (d.unlock || 1)}</small></span><input type="number" min="0" max="500" step="1" data-preset-troop="${type}" aria-label="${d.name} count" value="${saved?.army[type] || 0}" ${M.troopUnlocked(s, type) ? '' : 'disabled'}></label>`).join('')}</div><p class="capacity-note" id="preset-summary"></p><div class="panel-actions"><button class="btn" data-q="copy-army">Use current army</button><button class="btn btn-gold" data-q="save">Save preset</button><button class="btn btn-gold" data-q="quick-train" ${saved ? '' : 'disabled'}>${icon('droplets')}Train saved army</button></div><p class="guide-foot">Other troops stay in your camp. If the complete order does not fit or you need more elixir, nothing is charged.</p></div>`);
    document.querySelectorAll('[data-preset-troop]').forEach(input => input.addEventListener('input', () => this.summary()));
    this.summary();
  }
  counts() { return Object.fromEntries([...document.querySelectorAll('[data-preset-troop]')].map(input => [input.dataset.presetTroop, Number(input.value)])); }
  summary() {
    const el = document.getElementById('preset-summary');
    if (!el) return;
    const s = this.b.village(), plan = Q.presetPlan(s, this.slot);
    el.textContent = `${M.armySize(this.counts())} / ${M.armyCapacity(s)} saved army spaces` + (plan.error ? '' : ` · Saved order: ${plan.queued} missing troops · ${plan.cost} elixir`);
  }
  work() {
    this.b.showModal('work', this.b.header('YOUR VILLAGES AT A GLANCE', 'Work in progress') + '<div class="modal-body"><p class="modal-intro">Construction, troop training, research and hero recovery across both villages.</p><div id="work-orders"></div></div>');
    this.signature = '';
    this.tick('work');
  }
  walls(selectedId) {
    const s = this.b.village();
    if (this.b.realm() === 'capital') return;
    this.wallIds = new Set(selectedId ? [selectedId] : []);
    const walls = s.buildings.filter(b => b.type === 'wall');
    const cap = Math.min(s.realm ? 10 : 15, M.hallLevel(s) + 1);
    this.b.showModal('walls', this.b.header('FORTIFY YOUR VILLAGE', 'Wall upgrades') + `<div class="modal-body"><p class="modal-intro">Tap walls on the map or select a level group. Each selected wall rises one level instantly. Your current maximum is level ${cap}.</p><svg class="wall-map" viewBox="-15 -15 30 30" aria-label="Village wall selection map"><rect x="-14.5" y="-14.5" width="29" height="29" fill="#28452e" rx="1"/>${s.buildings.map(b => b.type === 'wall' ? `<g class="wall-tile ${b.level >= cap ? 'wall-max' : ''}" data-q="wall-toggle" data-id="${b.id}" role="checkbox" tabindex="0" aria-label="Wall level ${b.level} at ${b.x}, ${b.z}" aria-checked="false"><rect x="${b.x - .46}" y="${b.z - .46}" width=".92" height=".92" rx=".1"/><title>Level ${b.level} · ${M.buildingHp(b)} HP</title></g>` : `<rect x="${b.x - M.TYPES[b.type].size / 2}" y="${b.z - M.TYPES[b.type].size / 2}" width="${M.TYPES[b.type].size}" height="${M.TYPES[b.type].size}" fill="${b.type === 'hall' ? '#a78155' : '#617454'}" rx=".2"><title>${M.TYPES[b.type].name}</title></rect>`).join('')}</svg><div class="preset-tabs">${[...new Set(walls.filter(b => b.level < cap && !b.finishAt).map(b => b.level))].sort((a,b) => a-b).map(level => `<button class="btn btn-small" data-q="wall-level" data-level="${level}">Select level ${level} (${walls.filter(b => b.level === level).length})</button>`).join('')}<button class="btn btn-small" data-q="wall-clear">Clear selection</button></div><label class="wall-currency">Pay with <select id="wall-currency"><option value="gold">Gold</option><option value="elixir" ${M.hallLevel(s) < 4 ? 'disabled' : ''}>Elixir${M.hallLevel(s) < 4 ? ' · Town Hall 4' : ''}</option></select></label><p id="wall-quote" class="capacity-note"></p><button class="btn btn-gold btn-full" id="wall-confirm" data-q="wall-upgrade" disabled>Upgrade selected walls</button><p class="guide-foot">No builder required. Each level increases wall HP, height, thickness and fortification details. ${walls.length ? 'Dark walls are at your current level limit.' : 'Build walls from the Build menu to start fortifying your village.'}</p></div>`);
    document.getElementById('wall-currency').addEventListener('change', () => this.wallSummary());
    document.querySelectorAll('.wall-tile').forEach(tile => tile.addEventListener('keydown', e => { if ([' ', 'Enter'].includes(e.key)) { e.preventDefault(); this.toggleWall(tile.dataset.id); } }));
    this.wallSummary();
  }
  toggleWall(id) {
    const s = this.b.village(), wall = s.buildings.find(b => b.id === id);
    if (!wall || wall.level >= Math.min(s.realm ? 10 : 15, M.hallLevel(s) + 1) || wall.finishAt) return;
    if (this.wallIds.has(id)) this.wallIds.delete(id); else this.wallIds.add(id);
    this.wallSummary();
  }
  wallSummary() {
    const s = this.b.village(), currency = document.getElementById('wall-currency').value;
    this.wallOrder = Q.wallQuote(s, [...this.wallIds], currency);
    const quote = this.wallOrder, confirm = document.getElementById('wall-confirm');
    document.querySelectorAll('.wall-tile').forEach(tile => tile.setAttribute('aria-checked', String(this.wallIds.has(tile.dataset.id))));
    document.getElementById('wall-quote').textContent = quote.error ? (this.wallIds.size ? quote.error : 'Select walls to see the total upgrade cost.') : `${quote.walls.length} walls · ${quote.cost.toLocaleString()} ${currency} · ${s[currency] < quote.cost ? 'Not enough resources' : '+1 level each'}`;
    if(!quote.error){const hp=quote.walls.reduce((n,b)=>n+M.buildingHp(b),0),next=quote.walls.reduce((n,b)=>n+M.buildingHp({...b,level:b.level+1}),0);document.getElementById('wall-quote').textContent+=` · Combined HP ${hp.toLocaleString()} → ${next.toLocaleString()}`;}
    confirm.disabled = !!quote.error || s[currency] < quote.cost;
    confirm.textContent = quote.error ? 'Upgrade selected walls' : `Upgrade ${quote.walls.length} walls · ${quote.cost.toLocaleString()} ${currency}`;
  }
  tick(kind) {
    const jobs = Q.workOrders(this.b.root());
    document.getElementById('work-button').setAttribute('aria-label', `Work in progress · ${jobs.length} jobs`);
    if (kind !== 'work') return;
    const sig = JSON.stringify(jobs);
    if (sig !== this.signature) {
      this.signature = sig;
      document.getElementById('work-orders').innerHTML = jobs.map((job, i) => `<article class="work-row"><span class="card-icon">${icon(job.kind === 'hero' ? 'crown' : 'hourglass')}</span><div><strong>${esc(job.title)}</strong><small>${job.realm === 'builder' ? 'Builder Base' : 'Home village'} · <span data-work-time="${job.finishAt}">${time(job.finishAt)}</span></small></div>${job.canSkip ? `<button class="btn btn-small" data-q="finish" data-job="${i}">${icon('gem')}<span data-work-cost="${job.finishAt}">${M.skipCost(job.finishAt)}</span> · Finish</button>` : '<span class="work-wait">In progress</span>'}</article>`).join('') || '<p class="modal-intro">All work is complete. Your villages are ready.</p>';
      this.jobs = jobs;
      window.lucide?.createIcons({attrs: {'aria-hidden': 'true'}});
    }
    document.querySelectorAll('[data-work-time]').forEach(el => el.textContent = time(Number(el.dataset.workTime)));
    document.querySelectorAll('[data-work-cost]').forEach(el => el.textContent = M.skipCost(Number(el.dataset.workCost)));
  }
  async handle(button) {
    const action = button.dataset.q;
    if (action === 'walls') return this.walls(button.dataset.id);
    if (action === 'wall-toggle') return this.toggleWall(button.dataset.id);
    if (action === 'wall-clear') { this.wallIds.clear(); return this.wallSummary(); }
    if (action === 'wall-level') { this.wallIds = new Set(this.b.village().buildings.filter(b => b.type === 'wall' && b.level === Number(button.dataset.level) && !b.finishAt).map(b => b.id)); return this.wallSummary(); }
    if (action === 'presets') return this.presets();
    if (action === 'slot') return this.presets(Number(button.dataset.slot));
    if (action === 'copy-army') {
      const s = this.b.village();
      document.querySelectorAll('[data-preset-troop]').forEach(input => { if (!input.disabled) input.value = (s.army[input.dataset.presetTroop] || 0) + s.queue.filter(q => q.type === input.dataset.presetTroop).length; });
      this.summary(); return;
    }
    button.disabled = true;
    try {
      const realm = this.b.realm();
      if (action === 'wall-upgrade') {
        const quote = this.wallOrder;
        if (!quote || quote.error) return;
        const r = await this.b.mutate({type: 'wall-upgrade', realm, ids: quote.walls.map(b => b.id), levels: quote.walls.map(b => b.level), currency: quote.currency});
        this.b.toast(`${r.upgraded} walls upgraded · ${r.cost} ${r.currency}`);
        this.walls();
      }
      if (action === 'save') { await this.b.mutate({type: 'army-preset-save', realm, slot: this.slot, name: document.getElementById('preset-name').value, army: this.counts()}); this.b.toast('Army preset saved.'); this.presets(); }
      if (action === 'quick-train') { const r = await this.b.mutate({type: 'army-preset-train', realm, slot: this.slot}); this.b.toast(r.queued ? `${r.queued} troops queued · ${r.cost} elixir` : 'Your saved army is ready or already training.'); this.summary(); }
      if (action === 'batch') { const r = await this.b.mutate({type: 'train-batch', realm, troop: button.dataset.troop, count: 5}); this.b.toast(`${r.queued} troops queued.`); }
      if (action === 'finish') { const job = this.jobs[Number(button.dataset.job)]; if (job) await this.b.mutate({type: 'skip', realm: job.realm, kind: job.kind, id: job.id}); this.work(); }
    } finally { if (button.isConnected) button.disabled = false; }
  }
}
