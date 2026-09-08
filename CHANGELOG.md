# Emberfall v4.0.0

- Walls: individual or map-selected batch upgrades, level groups, total cost preview, gold payment or elixir from Town Hall 4, instant completion, fifteen distinct 3D appearances. Home walls cap at min(15, Town Hall + 1); Builder Base walls cap at min(10, Builder Hall + 1).
- Army: three named presets per village, current-army copy, deficit-only quick training, five-troop buttons, atomic cost and capacity checks.
- Work queue: construction, research, troop and spell training, heroes, recovery, pets, equipment and siege across both villages; valid gem skip controls.
- Connection: retry idempotent game commands with the same ID, block new spending while confirmation is unresolved, reject stale/account-switched retries. Checkout and authentication are not automatically replayed.
- Backups: automatic startup and six-hour snapshots in a child process, integrity checks, restricted file permissions, 28-file retention; manual snapshots retained.
- Operations: pinned GitHub Actions, test/build/smoke gates, explicit VPS deployment, SSH host-key verification, backup before replacement, health-gated image rollback, existing-proxy support and Burmese setup guide.
- Fixes: hero-only campaign scouting, mobile upgrade cost visibility, account-switch battle cleanup.

Existing Town Hall hero unlocks/caps, real clan wars, Builder Base, equipment, pets, siege, capital raids, AI clan league, season rewards, signed payment verification and server economy remain part of the source.
