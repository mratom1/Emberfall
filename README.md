# Emberfall — Kingdoms at War

Version 8 fixes mouse placement and adds clickable upgrade progress bars above buildings and heroes, Gem completion, 20 illustrated home heroes, Town Hall/Barracks unlocks, bridge-side land at Town Hall 3/7/11, 0.48–6.5× zoom, detailed rotating 3D model previews, deployment on cleared building footprints, and 250 purchasable country/territory flags. See [Village update](docs/VILLAGE_UPDATE_V8.md) and [Raids and progression](docs/RAIDS_AND_PROGRESSION.md) for exact rules and preview/server differences.

Version 5.0.0 adds Google/Facebook accounts, six illustrated heroes, High/Ultra HD graphics, a redesigned landscape UI, and native Android, iOS and Windows projects. See [Accounts and apps](docs/ACCOUNTS_AND_APPS.md) for setup, build commands and signing requirements.

A complete frontend and self-hosted Node.js server for an original 3D village strategy game. Burmese deployment guide: [README_MM.md](README_MM.md).

GitHub-to-VPS guide: [GITHUB_DEPLOY_MM.md](GITHUB_DEPLOY_MM.md). Release changes: [CHANGELOG.md](CHANGELOG.md).

## Start

With **Node.js 24 or newer** installed:

```sh
npm start
```

Open `http://YOUR_SERVER_IP:8080`. No npm install, compilation, external database, API key, or account provider is needed to play. SQLite is created automatically in `data/emberfall.sqlite`. All game assets and JavaScript libraries are served locally.

With **Docker Engine and Docker Compose** installed:

```sh
sh start.sh
```

The launcher creates .env if necessary and starts the game. Docker stores player data in a persistent volume.

## Implemented

| System | Behavior |
|---|---|
| Landscape | Automatic landscape layout with mapped touch coordinates; fullscreen/orientation lock where supported |
| Placement | Actual translucent 3D building, grid, blocked/valid footprint, drag/tap positioning, rotation, explicit confirmation |
| Buildings | 20 functional building types plus country flag decorations; Town Hall and building levels up to 15; unlock gates and timers; up to 5 builders |
| Obstacles | Tree clearing has a 42% chance of 1–6 gems; rocks give no gems; weekly Gem Box gives 25 |
| Walls | Individual/batch upgrades, map selection, cost preview, gold or elixir, 15 distinct 3D levels, Town Hall caps |
| Army | Three presets per village, deficit-only quick train, atomic batches, 8 troop types; Barracks unlocks; training queues; camp limits; Laboratory research |
| Heroes | 20 home heroes with portraits, HP/damage/DPS, changing 3D models at every level, camp presence, Town Hall gates, equipment, pets, recovery and abilities |
| Builder Base | Independent village, resources, 10 building levels, army, raids and Battle Machine hero |
| Equipment / pets | Eight equipment items, two slots per hero, four trainable and assignable companions |
| Siege | Three buildable siege machines; one deployed per raid; ground/flying behavior and reinforcements |
| Clan Wars | Real clan versus clan, equal rosters from 1v1 to 5v5, preparation, attack limits, scoreboards and rewards |
| Clan Capital | Shared 3D village, donations, leader construction, three raid districts, persistent damage, five weekly attacks |
| Clan League | Seven-round PvE clan competition against AI strongholds; monthly entry, shared scoring and medals |
| Season journey | Daily challenges, 20 free reward tiers, monthly reset and raid medal shop |
| Spells | Thunder, Heal, Rage, Freeze; Forge unlocks; brewing; 12-spell capacity |
| Defenses | Seven defensive building types, destructible walls, area traps, ground/flying targeting |
| Campaign | Progressively stronger AI strongholds, three-star scoring, loot and quests |
| Player raids | Random level-matched players or AI; saved defenses; maximum 10% stored-resource loot; incoming AI fallback; shields; attack/defense history |
| Clans | Create/join/leave, 30 members, messages, donations, player and clan rankings |
| Gems | Trees, weekly Gem Box and optional Stripe Checkout; spend on Shields, builders, resources and timers |
| Work queue | Construction, training, research, recovery and upgrades across both villages |
| Recovery | Stable-ID command retries, pending confirmation controls, automatic verified backups |
| Accounts | Guest sessions, username/password registration, sign-in on another device, persistent SQLite state |

This original game has its own names, art, balance and progression. Its rules and content catalog are not a one-to-one copy of Clash of Clans. Clan Wars use real clans; the seven-round Clan League uses explicitly labeled AI opponents. Battles are asynchronous. The season pass is a free reward track, not a paid subscription.

## Files

- `dist/quality.js` / `dist/quality-ui.js`: army presets, wall groups, atomic batches and work queue.
- `dist/raids.js` / `dist/raid-ui.js` / `server/raids.mjs`: shared raid rules, matching, shields, history, weekly gems and incoming AI.
- `server/backups.mjs`: nonblocking automatic backup scheduler.
- `.github/workflows/`: verified builds, image publishing and manual VPS deployment.
- `dist/model.js`: shared game rules, economy, timers, progression, combat.
- `dist/world.js`: Three.js scene, buildings, placement preview, obstacles and effects.
- `dist/game.js`: main UI and game orchestration.
- `dist/features.js`: heroes, research, spells, shop, accounts and clans.
- `dist/expansion.js`: hero loadouts, pets, siege, Builder Base, seasons and shared combat additions.
- `dist/expansion-ui.js`: hero roster, equipment, pets, world travel, war maps and league screens.
- `server/frontiers.mjs`: shared Clan Capital, wars, raid damage and league state.
- `server/security.mjs`: password hashing, transport requirements and security headers.
- `dist/connection.js`: server connection and idempotent commands.
- `server/app.mjs`: HTTP/static server, SQLite, sessions, accounts, commands, combat, clans and raids.
- `server/payments.mjs`: Checkout creation and raw-body webhook verification.
- `scripts/backup.mjs`: consistent SQLite backup.
- `deploy/`: Caddy, Nginx and systemd examples.
- `tests/`: executable gameplay and server integration checks.

The server owns currency balances, gem randomness, timers, army mutations, battle results and purchase credits. It does not accept client save uploads or client-reported loot.

Serving only `dist/` gives standalone browser play, including Builder Base and hero practice. That mode uses editable localStorage and cannot provide trusted wallets, accounts, clans, player raids or purchases. Local browser saves are not imported into server wallets.

## HTTPS

Point a domain to your server, copy .env.example to .env if needed, set `DOMAIN=game.your-domain.com`, then:

```sh
docker compose -f compose.https.yml up -d --build
```

This uses Caddy, enables secure cookies, and keeps the game port internal. Ports 80/443 must be available. With an existing HTTPS proxy, use standard Compose with `BIND_ADDRESS=127.0.0.1`, `PUBLIC_URL=https://YOUR_DOMAIN`, `COOKIE_SECURE=true`, and `NODE_ENV=production`. See deploy/nginx.conf.example.

## Payments

The shop displays three packs. Purchases stay unavailable until HTTPS and Stripe keys are configured. Earned gems and other gameplay work without keys. See [PAYMENTS.md](PAYMENTS.md). Start with test keys; live payments were not activated or exercised.

## Operations

```sh
docker compose logs -f game
docker compose up -d --build
docker compose exec game node scripts/backup.mjs
docker compose cp game:/app/data/backups ./backups
```

The CLI/Docker server also takes automatic backups at startup and every six hours. It retains 28 automatic snapshots; manual backups are never pruned. BACKUP_ENABLED, BACKUP_INTERVAL_HOURS and BACKUP_KEEP configure this behavior. Backups remain on the server until you copy them elsewhere.

For HTTPS, add `-f compose.https.yml` after `docker compose`. Do not use `down -v` unless deleting all player data is intended.

To restore, stop the game, preserve the old data, replace the SQLite file with a verified backup, remove the stopped database's stale -wal/-shm companions, and restart.

This is a single Node.js process with SQLite for a small self-hosted game, not a horizontally scaled MMO. Password change and sign out are included; changing a password revokes other sessions. Email password recovery, moderation dashboards and automated refund/dispute reconciliation are not implemented. Use HTTPS before registering real passwords or taking payments.

## Verification

The full suite requires Node.js 24 and Python 3 (deployment fault simulation). Docker/SSH simulation verifies failure handling; actual image build and smoke gates run in GitHub Actions. No external VPS was deployed during source preparation.


```sh
npm test
```

The suite covers gameplay, core HTTP integration, expansion systems, security, quality/recovery, deployment fault simulations, OAuth/native app source, WebView layout/connection recovery, and raids/progression. Tests cover accounts, concurrent actions, transactional loot, shields, clans and simulated signed payment notifications. No external payment request is made. See the test output for the current checks. Target-device browser behavior, public TLS deployment and live Stripe credentials need separate operator verification.

Original game code, procedural models and campaign artwork are included. Three.js and Lucide licenses are included under dist/assets. Emberfall is not affiliated with Supercell.

## Security

Public account registration, sign-in and password changes require HTTPS. Localhost HTTP remains available for development. Guest gameplay can start without a domain. Server rules reject client-supplied currency, levels and battle outcomes. See [SECURITY.md](SECURITY.md) for implemented controls, test coverage and operational limits.

## Hero progression

| Hero | Town Hall unlock | Level cap |
|---|---:|---|
| Ember King | 2 | min(50, (Town Hall − 2 + 1) × 5) |
| Moon Ranger | 3 | min(50, (Town Hall − 3 + 1) × 5) |
| Dusk Prince | 4 | min(50, (Town Hall − 4 + 1) × 5) |
| Storm Warden | 5 | min(50, (Town Hall − 5 + 1) × 5) |
| Dawn Champion | 7 | min(50, (Town Hall − 7 + 1) × 5) |

Each home hero also needs a completed Hero Hall and dark elixir. The Builder Base has its own Battle Machine, upgraded with builder elixir up to five levels per Builder Hall level. Training grounds lend heroes for practice without changing ownership, unlocks, wallets or real army stock.
