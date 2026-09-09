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
