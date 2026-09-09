# Pictures and combat durability — update 9

Build, Army, owned buildings, deployment troops and heroes now show rendered pictures of the same 3D model used in the village and battlefield, at the corresponding level. A new building previews level 1; research levels apply to troop pictures. The earlier illustrated hero atlases remain in the source but are no longer the roster representation. Lighting and camera angle can differ; geometry, weapons and materials share the world constructors.

Pictures render through one offscreen renderer, two per animation frame. Up to 96 bitmaps are cached. This avoids one GPU context per card. No browser/device visual acceptance test has been performed.

## Shared building HP

For building level L (1–15), n = L − 1:

`HP = round(baseHP × (1 + 0.25n) × (1 + 0.24n + 0.04n²))`

Level 1 is unchanged. The fixed defender-level rule applies equally to human and bot raids and newly created clan battle buildings. Campaigns retain their scenario multiplier with the new fortification curve. Already active battles retain saved HP, preventing mid-battle changes. HP never depends on client-supplied values or the current attacker.

## Defense behavior and structural upgrades

Defense damage and fire rate scale at every level; range grows by up to 1.4 tiles. Mortar/Wizard splash aims at dense groups, high-level Tesla chains to nearby units, Inferno ramps against a retained target and resets on loss/freeze. Ground-only and air-only restrictions remain enforced. The Town Hall gains a defensive weapon from level 7. Existing saved battles without combat version 9 retain previous defense rules.

Real geometry grows with progression: Town Halls gain keeps and turrets; other buildings gain annexes, buttresses and taller structures; defenses gain battlements and additional weapon barrels/platforms; walls become taller and thicker with braces, spikes and crystal caps. Troops gain plate armor, helmets and capes; heroes gain larger shoulder armor, helmets, capes and higher-tier crests. Every menu picture uses the same constructors as the world.

Wall HP increases at each level. The building panel shows current/next HP; wall batch selection shows combined current/next HP. Defense panels show current/next DPS and target categories.

## Measured combat simulations

`npm run test:balance` records 96 cases: Town Hall 3/7/11/15, three seeds, developing/maxed heroes, clustered/four-sided deployments, and old/new rules. Legal maximum camp capacity and legal hero/research levels are used. Both sides deploy all units and use hero abilities at 12 seconds. The old mode uses old HP and defense rules; the new mode uses the shared durability and defense rules.

| TH | Heroes | Deployment | Old median stars | New median stars | New median destruction |
|---|---|---|---:|---:|---:|
| 3 | developing | clustered | 3 | 3 | 100% |
| 3 | developing | split | 3 | 3 | 100% |
| 3 | maxed | clustered | 3 | 3 | 100% |
| 3 | maxed | split | 3 | 3 | 100% |
| 7 | developing | clustered | 3 | 3 | 100% |
| 7 | developing | split | 3 | 3 | 100% |
| 7 | maxed | clustered | 3 | 3 | 100% |
| 7 | maxed | split | 3 | 3 | 100% |
| 11 | developing | clustered | 3 | 0 | 17% |
| 11 | developing | split | 3 | 0 | 44% |
| 11 | maxed | clustered | 3 | 3 | 100% |
| 11 | maxed | split | 3 | 3 | 100% |
| 15 | developing | clustered | 3 | 0 | 11% |
| 15 | developing | split | 3 | 0 | 17% |
| 15 | maxed | clustered | 3 | 1 | 50% |
| 15 | maxed | split | 3 | 2 | 78% |

A separate controlled regression uses the same 24 Rangers against the same level-5 Town Hall and level-6 Mortar: a clustered attack earns 0 stars; a four-sided attack earns 2. This verifies strategy-sensitive outcomes, not a global win-rate guarantee. Some maxed armies still win, and weak attacks can fail.

These are deterministic combat checks, not measurements of human PvP win rates or VPS capacity. Real-player tuning and the full 10,000-player production benchmark remain unfinished. Device/browser visual acceptance is also unverified.
