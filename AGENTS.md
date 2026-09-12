# Emberfall Agent Operating Guide

This file is the first document any coding agent should read when working in this repository.

The goal is to keep work accurate while minimizing unnecessary repository scans, repeated context loading, token/credit usage, and risky broad edits.

## 1. Golden rule: do not scan the whole repository

Do **not** recursively read the entire repository to understand the project.

Start with only:

1. `AGENTS.md`
2. `docs/WORK_STATUS.md`
3. `package.json`
4. The files directly related to the current task

Read `README.md`, `README_MM.md`, `CHANGELOG.md`, `SECURITY.md`, deployment docs, or other documentation only when the task actually needs them.

Use targeted search first. Examples:

```powershell
rg -n "Hero|hero" dist server tests docs
rg -n "deploy|deployment|spawn" dist server tests
rg -n "functionName|className|configKey" dist server tests
```

Prefer exact symbol searches and narrow directory scopes. Do not dump huge search results into context.

Do not repeatedly reopen unchanged files. Reuse knowledge already gathered in the current session.

When a file is large, read only the relevant section first. Expand only when dependencies require it.

Avoid opening more than roughly 10-12 new files in one investigation pass unless the task genuinely spans more files. If more are needed, work in focused batches and keep a concise map of what has already been inspected.

## 2. Project facts

- Project: **Emberfall — Kingdoms at War**
- Runtime: **Node.js 24+**
- Module system: **ES modules**
- Main server: `server/app.mjs`
- Current persistent store: **SQLite**
- Frontend/game source is primarily under `dist/`
- Native shells exist under `apps/android`, `apps/ios`, and `apps/windows`
- Tests are executable Node.js integration/gameplay tests under `tests/`
- The game uses original names, rules, art, balance, and procedural/model assets.

Important: `dist/` is not merely disposable build output in this repository. It contains important game source. Never ignore or regenerate all of `dist/` blindly.

## 3. High-value project map

Use this map before searching broadly.

### Core game / frontend

- `dist/model.js` — shared game rules, economy, progression, timers, combat
- `dist/world.js` — Three.js world, buildings, placement, obstacles, effects
- `dist/game.js` — primary UI/game orchestration
- `dist/features.js` — heroes, research, spells, shop, accounts, clans
- `dist/expansion.js` — hero loadouts, pets, siege, Builder Base, seasons, shared combat additions
- `dist/expansion-ui.js` — hero roster, equipment, pets, world travel, war/league UI
- `dist/quality.js` / `dist/quality-ui.js` — army presets, wall groups, batching, work queue
- `dist/raids.js` / `dist/raid-ui.js` — raid client/shared behavior and battle UI
- `dist/connection.js` — server connection and idempotent commands

### Backend

- `server/app.mjs` — HTTP/static server, SQLite, sessions, accounts, commands, combat, clans, raids
- `server/raids.mjs` — matching, shields, raid state/history and related server rules
- `server/frontiers.mjs` — Clan Capital, wars, persistent raid damage, league state
- `server/security.mjs` — password hashing, transport requirements, security headers
- `server/payments.mjs` — checkout and webhook verification
- `server/backups.mjs` — automatic backup scheduling

### Operations / tooling

- `scripts/backup.mjs` — SQLite backup
- `scripts/balance-check.mjs` — balance checks
- `deploy/` — deployment examples/configuration
- `.github/workflows/` — CI/build/deployment workflows
- `benchmarks/` — benchmark evidence; do not treat local results as production-capacity proof

### Project status

- `docs/WORK_STATUS.md` — current completed work, known gaps, production target, and explicit claims that must not be invented
- `PRODUCTION_REQUIREMENTS.txt` — authoritative production brief when working on scaling/public-release tasks

## 4. Current gameplay/art context

The current project includes a large strategy-game feature set, including village building, armies, heroes, raids, defenses, progression, clans, wars, Builder Base-style secondary progression, equipment, pets, siege, spells, and mobile/native shells.

Army and hero work has already evolved through multiple versions. Before redesigning characters, troop logic, hero progression, combat, cards, portraits, animation, or Blender-generated/model assets, inspect the current implementation first. Do not assume an older roster or older screenshots still describe current source.

When working on character visuals:

- Preserve each troop/hero's gameplay identity.
- Prefer original designs and strong silhouettes.
- Do not reuse one model with only superficial recolors when the task requests unique units.
- Maintain mobile readability and battle readability.
- Keep portrait/card and field-model identity consistent where the current system expects it.
- For Blender automation, prefer deterministic Python/CLI workflows over hundreds of fragile UI clicks when practical.
- Keep generated models/materials organized and optimized for the game's actual renderer/export path.

## 5. Production/scaling truth

The current backend is Node.js + SQLite. The public-release production brief targets a larger VPS deployment and eventual high concurrency, but PostgreSQL/Redis migration and measured 10,000-player production capacity are not complete unless `docs/WORK_STATUS.md` has subsequently been updated with evidence.

Never claim any of the following without measured evidence:

- "10,000 concurrent users supported"
- "hack-proof"
- "production ready"
- "zero exploits"
- a local benchmark proves VPS capacity

When working on scaling, backend, deployment, database, observability, security, or launch-readiness tasks, read `docs/WORK_STATUS.md` and `PRODUCTION_REQUIREMENTS.txt` before implementation.

Preserve authoritative-server rules. Currency, progression, battle results, timers, purchases, rewards, and other trusted state must not become client-authoritative.

## 6. Minimal-context workflow for every task

Follow this order:

### A. Understand the request

Write a one-paragraph internal task map:

- user-visible goal
- likely files/systems affected
- security/data risks
- smallest verification needed

Do not produce a giant architecture report unless requested.

### B. Locate code using search

Search symbols/phrases first. Open the smallest relevant set of files.

Bad workflow:

1. Read every file in `dist/`
2. Read every file in `server/`
3. Read every test
4. Then decide what matters

Good workflow:

1. Search exact feature/symbol
2. Inspect 2-6 likely files
3. Trace direct imports/callers only as needed
4. Edit targeted locations
5. Run targeted tests

### C. Preserve a concise working map

During the session, remember:

- files already inspected
- important functions/classes discovered
- relevant data flow
- tests already run

Do not reread unchanged files just to reconstruct context.

### D. Make focused edits

Prefer small, reviewable diffs.

Do not rewrite complete files when a targeted change is enough.

Do not perform unrelated cleanup/refactors "while here" unless they are necessary for correctness.

### E. Verify narrowly first

Run the smallest relevant test or syntax check before the entire suite.

Only run the full `npm test` when:

- the task affects shared/core behavior,
- multiple systems changed,
- final verification is required,
- or the user explicitly asks for a full test.

Do not rerun the same expensive full suite repeatedly when no relevant code changed.

## 7. Commands

Start server:

```powershell
npm start
```

Full test suite:

```powershell
npm test
```

Balance check:

```powershell
npm run test:balance
```

Backups:

```powershell
npm run backup
```

For targeted tests, run the relevant test file directly, for example:

```powershell
node tests/gameplay.mjs
node tests/raids.mjs
node tests/mobile-roster.mjs
node tests/animation-flags.mjs
node tests/portraits-balance.mjs
node tests/security.mjs
```

Choose the smallest test that can prove the change first.

## 8. Areas that should not be loaded casually

Do not load large/generated/unrelated content unless the task requires it:

- `node_modules/`
- large binary media/model files
- generated renders
- screenshots/videos
- database files
- backups
- build artifacts from native apps
- huge logs
- large benchmark outputs
- unrelated docs
- entire asset directories

Within `dist/`, source JavaScript is important, but large asset subtrees should still be treated selectively.

Never read `.env` secrets or credentials unless the user explicitly needs configuration diagnosis and the secret values themselves are not required. Do not expose credentials in output, logs, commits, screenshots, or tests.

## 9. Git safety

Before editing, inspect current status when working locally:

```powershell
git status --short
git branch --show-current
```

Do not destroy local work.

Never use destructive commands such as these unless the user explicitly authorizes the exact operation:

```text
git reset --hard
git clean -fd
git checkout -- <user-file>
```

Do not overwrite unrelated user changes.

Do not force-push unless explicitly requested.

Do not commit generated secrets, `.env`, database files, backups, or private credentials.

## 10. Security and authoritative gameplay rules

For server/gameplay changes:

- Validate client input on the server.
- Keep trusted economy/progression mutations server-authoritative.
- Preserve authorization checks.
- Preserve idempotency for retryable commands.
- Use transactions for related persistent state changes.
- Do not trust client-reported loot, currency, level, timers, or battle outcomes.
- Avoid leaking secrets or sensitive account data into logs.
- Do not weaken security just to make a test pass.

For concurrency-sensitive work, consider duplicate requests, retries, race conditions, stale state, and partial failures.

## 11. Performance rules

Do not optimize blindly.

For performance/scaling work:

1. identify the hot path,
2. measure it,
3. make a focused change,
4. measure again,
5. record limitations honestly.

Avoid loading/recomputing large datasets when a targeted query/cache/index can solve the problem.

Do not claim capacity from theory alone.

## 12. UI/mobile rules

The game is mobile-first enough that every UI/gameplay change should consider:

- small screens
- landscape layout
- touch targets
- pinch/zoom interactions
- safe-area/inset behavior
- panel overflow
- readable battle HUD
- unit/hero recognition at small scale

Do not fix desktop while silently breaking mobile.

## 13. Blender / asset-agent rules

When a task involves Blender or procedural 3D assets:

- First locate how the current game constructs/loads/renders the affected models.
- Preserve scale/orientation conventions already used by the project.
- Prefer reproducible Blender Python scripts or deterministic asset-generation steps.
- Avoid creating unnecessarily high-poly assets for small mobile battlefield units.
- Keep materials/meshes reusable only where reuse does not erase unit identity.
- Use LOD/optimization only when compatible with the existing renderer and asset pipeline.
- Validate exported files before replacing current assets.
- Do not regenerate every asset when only a few units need work.

## 14. Completion standard

A task is not complete merely because code was written.

Before reporting completion:

1. confirm intended files changed,
2. run relevant targeted tests/checks,
3. check for obvious regressions,
4. inspect `git diff --check` when local Git access exists,
5. state what was actually verified,
6. state anything that still requires real-device/manual/VPS verification.

Do not claim manual device, browser, payment, Blender visual, or production infrastructure verification if it was not actually performed.

## 15. Response discipline

Keep progress reports concise.

Prefer:

- what you found
- what you changed
- what you tested
- remaining blocker/risk

Avoid repeating the same architecture explanation every turn.

If the user asks for a feature, inspect the existing implementation first, then implement the feature in the context of the full game. Do not stop at the literal request if correctness requires related server validation, persistence, UI updates, tests, or migration work—but keep the scope focused and explain any necessary supporting work.

---

### Quick start for a new agent session

Use this exact workflow:

```text
1. Read AGENTS.md.
2. Read docs/WORK_STATUS.md.
3. Read package.json.
4. Do NOT scan the repository.
5. Search only for symbols/files related to my current task.
6. Reuse files/context already inspected in this session.
7. Make focused edits; avoid broad rewrites.
8. Run the smallest relevant tests first.
9. Run the full suite only when warranted.
10. Report exactly what was changed and verified.
```

This repository values correctness, server authority, mobile usability, security, measured performance, and efficient agent context usage equally.
