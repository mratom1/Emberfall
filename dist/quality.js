import * as M from './model.js?v=10.0.0';

export const PRESET_SLOTS = 3;
const error = message => ({error: message});

function validateArmy(s, army) {
  if (!army || typeof army !== 'object' || Array.isArray(army)) return 'Choose troop counts.';
  for (const [type, count] of Object.entries(army)) {
    if (!Object.hasOwn(M.TROOPS, type) || !Number.isInteger(count) || count < 0 || count > 500) return 'Invalid troop count.';
    if (count && !M.troopUnlocked(s, type)) return 'Unlock the requested troops in your Barracks first.';
  }
  if (!M.armySize(army)) return 'Choose at least one troop.';
  if (M.armySize(army) > M.armyCapacity(s)) return 'This army exceeds your camp capacity.';
}

// Only commit a batch after every troop passes the ordinary training rules.
export function trainBatch(s, counts, now = Date.now()) {
  const invalid = validateArmy(s, counts);
  if (invalid) return error(invalid);
  const draft = {...s, queue: s.queue.map(q => ({...q}))};
  let queued = 0;
  for (const [type, count] of Object.entries(counts)) {
    for (let i = 0; i < count; i++) {
      const result = M.train(draft, type, now);
      if (result.error) return result;
      queued++;
    }
  }
  const cost = s.elixir - draft.elixir;
  s.elixir = draft.elixir;
  s.queue = draft.queue;
  return {ok: true, queued, cost};
}

export function presetPlan(s, slot) {
  const saved = s.armyPresets?.[slot];
  if (!saved) return error('Save an army in this slot first.');
  const invalid = validateArmy(s, saved.army);
  if (invalid) return error(invalid);
  const waiting = {};
  for (const q of s.queue) waiting[q.type] = (waiting[q.type] || 0) + 1;
  const counts = Object.fromEntries(Object.entries(saved.army).map(([type, n]) => [type, Math.max(0, n - (s.army[type] || 0) - (waiting[type] || 0))]));
  const cost = Object.entries(counts).reduce((sum, [type, n]) => sum + M.TROOPS[type].cost * n, 0);
  return {counts, cost, space: M.armySize(counts), queued: Object.values(counts).reduce((a, b) => a + b, 0)};
}

export function action(s, a, now) {
  if (a.type === 'wall-upgrade') {
    const quote = wallQuote(s, a.ids, a.currency);
    if (quote.error) return quote;
    if (a.levels && (!Array.isArray(a.levels) || a.levels.length !== quote.walls.length || quote.walls.some((wall, i) => wall.level !== a.levels[i]))) return error('These walls changed. Review the new upgrade price.');
    if (s[quote.currency] < quote.cost) return error('Not enough ' + quote.currency + ' for all selected walls.');
    s[quote.currency] -= quote.cost;
    for (const wall of quote.walls) wall.level++;
    s.stats.upgraded += quote.walls.length;
    return {ok: true, upgraded: quote.walls.length, cost: quote.cost, currency: quote.currency};
  }
  if (a.type === 'train-batch') {
    if (!Number.isInteger(a.count) || a.count < 1 || a.count > 50 || !Object.hasOwn(M.TROOPS, a.troop)) return error('Choose 1–50 troops.');
    return trainBatch(s, {[a.troop]: a.count}, now);
  }
  if (!['army-preset-save', 'army-preset-train'].includes(a.type)) return undefined;
  if (!Number.isInteger(a.slot) || a.slot < 0 || a.slot >= PRESET_SLOTS) return error('Choose one of the three army slots.');
  if (a.type === 'army-preset-save') {
    const invalid = validateArmy(s, a.army);
    if (invalid) return error(invalid);
    if (typeof a.name !== 'string' || !a.name.trim() || a.name.length > 32 || /[\u0000-\u001f]/.test(a.name)) return error('Use an army name of 1–32 characters.');
    s.armyPresets ??= [null, null, null];
    s.armyPresets[a.slot] = {name: a.name.trim(), army: {...a.army}};
    return {ok: true};
  }
  const plan = presetPlan(s, a.slot);
  if (plan.error) return plan;
  if (!plan.queued) return {ok: true, queued: 0, cost: 0};
  return trainBatch(s, plan.counts, now);
}

export function wallQuote(s, ids, currency = 'gold') {
  if (!Array.isArray(ids) || ids.length < 1 || ids.length > M.TYPES.wall.max || ids.some(id => typeof id !== 'string') || new Set(ids).size !== ids.length) return error('Choose distinct walls to upgrade.');
  if (!['gold', 'elixir'].includes(currency)) return error('Choose gold or elixir.');
  if (currency === 'elixir' && M.hallLevel(s) < 4) return error('Elixir wall upgrades unlock at Town Hall level 4.');
  const walls = ids.map(id => s.buildings.find(b => b.id === id));
  if (walls.some(b => !b || b.type !== 'wall' || b.finishAt)) return error('Choose completed walls in this village.');
  const cap = Math.min(s.realm ? 10 : 15, M.hallLevel(s) + 1);
  if (walls.some(b => b.level >= cap)) return error('Some selected walls need a higher Town Hall or are at maximum level.');
  return {walls, currency, cost: walls.reduce((sum, b) => sum + M.upgradeCost(b).gold, 0), cap};
}

export function workOrders(root, now = Date.now()) {
  const jobs = [];
  for (const [realm, s] of [['home', root], ['builder', root.expansion?.builder]]) {
    if (!s) continue;
    const add = (title, kind, id, finishAt, canSkip = true) => {
      if (finishAt > now) jobs.push({title, kind, id, finishAt, realm, canSkip});
    };
    for (const b of s.buildings) add(`${M.TYPES[b.type].name} · Level ${b.constructing ? b.level : b.level + 1}`, 'building', b.id, b.finishAt);
    for (const o of s.obstacles || []) add('Clear ' + o.type, 'obstacle', o.id, o.finishAt);
    for (const [id, h] of Object.entries(s.heroes || {})) {
      add(`${M.HEROES[id].name} · Level ${h.level + 1}`, 'hero', id, h.finishAt);
      if (!h.finishAt) add(M.HEROES[id].name + ' · Recovery', 'recovery', id, h.recoverAt, false);
    }
    for (const [key, kind, defs] of [['queue', 'training', M.TROOPS], ['researchQueue', 'research', M.TROOPS], ['spellQueue', 'spell', M.SPELLS]]) {
      for (const [i, q] of (s[key] || []).entries()) add(defs[q.type].name + (kind === 'research' ? ' · Research' : ' · Training'), kind, q.id || q.type, q.finishAt, i === 0);
    }
  }
  const e = root.expansion;
  if (e) {
    for (const [id, p] of Object.entries(e.pets)) if (p.finishAt > now) jobs.push({title: id + ' · Pet training', realm: 'home', finishAt: p.finishAt, canSkip: false});
    if (e.equipmentWork?.finishAt > now) jobs.push({title: e.equipmentWork.id + ' · Equipment', realm: 'home', finishAt: e.equipmentWork.finishAt, canSkip: false});
    for (const q of e.siegeQueue) if (q.finishAt > now) jobs.push({title: q.type + ' · Siege workshop', realm: 'home', finishAt: q.finishAt, canSkip: false});
  }
  return jobs.sort((a, b) => a.finishAt - b.finishAt);
}
