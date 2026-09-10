## 10.0.0
- Fit Army cards to mobile width and remove the Hero gallery height cap.
- Compact rotated-phone battle controls and hide the home resource bar during combat.
- Fix camera jumps after releasing one finger of a pinch gesture.
- Expand the original troop roster to 22, with unique physical geometry, human anatomy and distinct weapons, creatures and automata.
- Add medic healing, additional splash and wall-breaking troop roles, and troop model inspection.
- Remove Your Buildings; retain the wall-upgrade manager.
- Apply owned country flags to all village poles and building banners, including the Town Hall.

# Emberfall v9.0.0

- Defense levels now increase damage/fire rate/range; splash targets groups, Tesla chains and Inferno ramps. Town Hall weapon unlocks at 7. Strategy regression: same 24 Rangers score 0 stars clustered versus 2 when flanking.
- Structural tiers add keeps, annexes, buttresses, weapon platforms, larger armor, helmets/capes and fortified wall thickness/height. Wall single/batch upgrades show current/next HP.
- Combat comparisons expanded to 96 cases; defensive wins and partial victories are recorded.

- Build, Army, owned-building and battle troop cards now show pictures rendered from the actual village/battle 3D model and current level. Hero cards use that same model pipeline, replacing portrait illustrations that differed from gameplay.
- A single shared preview renderer, two queued pictures per frame and a bounded 96-picture cache avoid creating a WebGL context per card.
- Fixed Build's new-building level label and added HP/army damage information.
- Shared defender HP grows with building level to account for larger armies and 20 heroes. Level 1 retains its original HP; existing active battles retain their saved HP. New campaign, human/bot raid and clan battle HP follow the shared progression.
- Deterministic before/after combat simulations include Town Hall 3/7/11/15, three seeds, developing/maxed heroes and legal maximum camp capacity. This is combat tuning evidence, not a public-player load benchmark.

# Emberfall v8.0.0

- Mouse placement pins the chosen ground position while moving to Confirm; click, drag, repeat-wall placement and pinch zoom share the corrected coordinates.
- Clickable progress/time bars above upgrading buildings and camp heroes open a live Gem completion panel. The server computes the price and completes the action once.
- Twenty illustrated home heroes plus the Builder Base Battle Machine; new heroes require Town Hall and Barracks levels. Existing saves retain their progress.
- Bridge-side land opens at Town Hall 3, 7 and 11; adjacent open regions allow shared footprints. Town Hall reaches 15 with sufficient upgraded storage.
- 0.48–6.5× camera zoom, rotating 3D inspectors, detailed character weapons/armor and distinct building appearances across all 15 levels.
- Troops, heroes and siege may deploy in destroyed-building footprints while standing neighboring structures retain their deployment exclusion. Spells reach all expanded land.
- 250 locally bundled country/territory flags can be purchased for 200 gold and moved without cost.
- Original battle logs, shields, 10% raid loot, account/provider setup and server security remain documented in their respective guides.

# Emberfall v4.0.0

- Walls: individual or map-selected batch upgrades, level groups, total cost preview, gold payment or elixir from Town Hall 4, instant completion, fifteen distinct 3D appearances. Home walls cap at min(15, Town Hall + 1); Builder Base walls cap at min(10, Builder Hall + 1).
- Army: three named presets per village, current-army copy, deficit-only quick training, five-troop buttons, atomic cost and capacity checks.
- Work queue: construction, research, troop and spell training, heroes, recovery, pets, equipment and siege across both villages; valid gem skip controls.
- Connection: retry idempotent game commands with the same ID, block new spending while confirmation is unresolved, reject stale/account-switched retries. Checkout and authentication are not automatically replayed.
- Backups: automatic startup and six-hour snapshots in a child process, integrity checks, restricted file permissions, 28-file retention; manual snapshots retained.
- Operations: pinned GitHub Actions, test/build/smoke gates, explicit VPS deployment, SSH host-key verification, backup before replacement, health-gated image rollback, existing-proxy support and Burmese setup guide.
- Fixes: hero-only campaign scouting, mobile upgrade cost visibility, account-switch battle cleanup.

Existing Town Hall hero unlocks/caps, real clan wars, Builder Base, equipment, pets, siege, capital raids, AI clan league, season rewards, signed payment verification and server economy remain part of the source.

## v11 — walking and mobile flags
Ground troops and heroes use separate rigid limbs with opposing leg/arm strides in village patrols and battles. Idle stops the stride; flying units hover and winged models flap. Flag SVGs now have explicit raster dimensions and are drawn to canvas before WebGL upload; unlit double-sided flag materials avoid shadowed black cloth. Regression checks cover all ground/flying character rigs and the raster texture pipeline. Actual phone visual verification remains pending.
