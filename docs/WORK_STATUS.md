# Emberfall work checkpoint

Keep this file and `PRODUCTION_REQUIREMENTS.txt` with the project until the public-release task is completed. The requirements file is an exact copy of the owner's supplied brief; do not replace it with a shortened plan or mark untested targets complete.

## Current game update

Version 9 adds model-rendered pictures to Build, Army, owned buildings and battle deployment cards. Hero pictures render the identical world models at the shown level. Building durability is shared across UI, player/bot raids and clan battles; deterministic before/after combat evidence is in `benchmarks/combat-v9.json`. Defense upgrades now scale firing power and target behavior; structural model tiers add architecture/armor rather than only recoloring. Wall upgrades show current/next HP. The PostgreSQL/Redis/public-load work below remains open.

Implemented in the version 8 source: pinned mouse placement, continued wall placement, 20 illustrated home heroes plus Battle Machine, Town Hall/Barracks hero gates, level-dependent 3D models, 0.48–6.5× zoom, 3D inspection, bridge land at Town Hall 3/7/11, Town Hall 15, cleared-footprint deployment, 250 country flags, and clickable building/hero upgrade time bars with authoritative Gem finish actions.

Verification on 2026-09-09: all 99 existing and new automated checks passed locally. The pointer event harness and game/economy tests cover the reported regressions. Device/browser visual acceptance remains unverified. Release publishing and source synchronization must be checked against the latest commit.

## Public-release objective — not complete

The owner's target is a Linux VPS with **8 CPU cores, 18 GB RAM, 240 GB SSD and 300 Mbps unmetered networking**, with Nginx and Cloudflare where appropriate. Engineer toward **10,000+ concurrent authenticated players**, then measure realistic workload capacity. This is a target, not a supported-capacity claim.

Current backend: Node.js 24 with SQLite, shared testable authoritative game rules, sessions/CSRF, validated and idempotent economy actions, persistent timestamp timers and server-simulated battles. Static Sites preview uses local saves and AI; it is not the production shared-player backend.

The following production brief work remains open:

- P0: inspect backend bottlenecks; implement PostgreSQL persistence with reviewable versioned migrations, bounded connection pools, normalized practical data access, concurrency-safe transactions and compatible migration of existing saves; retain authorization, authentication, idempotency and server authority.
- P1: query/index optimization, shared Redis rate limits/cache where useful, separated static delivery, production Nginx/Compose, PostgreSQL backups and restore verification, structured redacted logs, rotation, readiness and operational metrics.
- P2: realistic load scenarios A–H, progressive 100/500/1,000/2,500/5,000/10,000-player tests, concurrent economy/reward/timer failure tests, benchmark → identify bottleneck → optimize → benchmark again. Record measured throughput, p50/p95/p99, errors, CPU/RAM, database/cache/network usage and first bottleneck.
- P3: stateless multi-API readiness, graceful overload/shutdown, backward-compatible migration/deployment procedures, hardening and exact launch runbook.

No PostgreSQL/Redis implementation or production load benchmark has been completed for this brief. The target VPS is not connected to this workspace. Do not invent a capacity number, claim 10,000-user support, imply the game is hack-proof, or treat a local benchmark as proof about the specified VPS.

## Completion rule

Use the full brief's 20 acceptance tests and 10 final deliverables as the checklist. Preserve previous gameplay work while implementing the backend. Record evidence and material blockers here. Production readiness is not complete merely because a plan, source ZIP, static preview or functional test suite exists.

## v10 — mobile roster and battle controls

Implemented responsive Army cards and continuously scrolling Hero gallery, removed Your Buildings, fixed pinch-release camera jumps, compacted the mobile battle HUD and hid home resources during combat. The roster now has 22 original troop types with distinct geometry, Barracks 1–15 unlocks and shared server training rules. Human models have faces, jointed limbs, hands, armor and distinct weapons; flying creatures and automata use their own bodies. Portraits and field units share constructors. Added support healing and additional splash/wall-breaking roles. Country ownership persists; selecting an owned design changes all poles and Town Hall/building banners.

Device screenshots supplied by the user guided these changes. No browser/device visual verification was performed. Production PostgreSQL/Redis migration and measured 10k concurrent-user capacity remain pending as specified above.

## v11 — walking and mobile flags
Ground troops and heroes use separate rigid limbs with opposing leg/arm strides in village patrols and battles. Idle stops the stride; flying units hover and winged models flap. Flag SVGs now have explicit raster dimensions and are drawn to canvas before WebGL upload; unlit double-sided flag materials avoid shadowed black cloth. Regression checks cover all ground/flying character rigs and the raster texture pipeline. Actual phone visual verification remains pending.
