# Village update 8

The game link receives the updated web client. Existing village saves are migrated without resetting resources, buildings or heroes. The Node.js 24 server serves the same client and validates game commands against the shared rules.

## Placement and camera

Choose Build or Move, click a free location or drag the translucent building, then click Confirm (or press Enter). The chosen location remains fixed when the mouse moves to Confirm. Repeated wall placement stays active and suggests the next free neighbor. Right-click does not open the browser context menu on the battlefield. Pinch, the wheel and zoom buttons support 0.48–6.5× zoom.

The west bridge connects to new land. Westbank Meadow unlocks at Town Hall 3, Pine Terrace at 7, and Stone Heights at 11. Open regions show a green grid; locked regions show their required Town Hall level. The Lands button moves the camera to each region. Buildings must fit completely on open land; the river and bridge are reserved. Adjacent unlocked regions can share a building footprint.

## Upgrade time bars and Gems

Construction/upgrading buildings and upgrading heroes at the camp have time bars above their 3D models. Select a bar to see current/next level, remaining time, progress and the Gem price. Select **Finish now** to spend Gems. The price is one Gem per started 10 seconds remaining, minimum one. The authoritative command verifies the actual finish time and balance. A completed upgrade cannot be charged again. Insufficient Gems leave the upgrade running. Progress continues while offline and includes the Builder Base hero.

## Heroes and models

The main Heroes button opens a pictured 20-hero roster. Each detail panel includes hit points, damage per hit, DPS, range, next-level changes, unlock requirements and upgrade actions. Twenty original home heroes are separate from the Builder Base Battle Machine. The original five retain their Town Hall gates; the additional fifteen require both Town Hall and Barracks upgrades. Hero caps never exceed level 50. Locked heroes remain visible in the roster, and owned/upgrading heroes stand near Army Camps.

Building selection and hero detail panels include **Inspect 3D**. Rotate the model and preview levels with the sliders. Previewing a level does not spend currency or upgrade the village. Every building level through 15 changes geometry and colors; heroes change armor, size, rank ornaments and higher-level effects. New heroes have distinct weapons and silhouettes. These are original game assets, not Clash of Clans artwork.

## Battle placement

Standing buildings retain a deployment exclusion around their footprint. Once a building is destroyed, the cleared footprint becomes available for troop, hero or siege deployment unless a standing neighbor still covers it. Green ground marks show available cleared tiles; red lines mark standing-building exclusion areas. Spells can target the expanded land. Human raids use saved server villages; matching AI villages remain available when no eligible player exists.

## Country flags

The flag shop contains 250 country and territory flags, searchable by name or country code. A flag costs 200 gold, with up to 30 placed flags per home village. Choose a flag and confirm an empty tile. Select a placed flag to move it for free. Flags are decorations and do not change battle damage or loot. All SVG artwork is bundled locally from flag-icons 7.5.0, with its MIT license and source attribution in `dist/assets/`.

## Runtime scope

The private Sites preview uses local village saves and simulated bot activity. Shared human PvP, authenticated accounts and persistent server state require deploying the included Node.js server. Google/Facebook login and real-money Gem checkout additionally need the owner's provider configuration. Static GitHub Pages cannot run this server. Native app projects bundle this client through their existing build workflow; signing and store submission are separate owner configuration steps.

## Regression coverage

`npm test` includes mouse/drag/pinch handlers, land and footprint boundaries, hero save migration/unlocks, cleared-area troop/hero/siege deployment, expanded spell targeting, flag prices/collisions, upgrade progress/Gem completion, Town Hall affordability, and the existing account, server, raid/economy and appearance suites. Model tests compare every building level 1–15 and hero level 1–50. These checks do not substitute for testing on the owner's exact phone/browser.
