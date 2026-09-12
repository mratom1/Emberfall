# Blender Army & Hero Pipeline

This repository now has a headless Blender pipeline for original Emberfall character assets.

## What it covers

- **22 troops** from `dist/model.js`, each with levels **1–15**.
- **20 home heroes + Battle Machine**, each with levels **1–50**.
- Original unit-specific silhouettes, weapons, armor language, color palettes and motifs are defined in `art/blender/unit_specs.json`.
- Each generated level produces a game-ready **GLB**, a transparent **PNG preview**, and `metadata.json`.
- Optional editable **.blend** files are included in the Actions artifact.
- The procedural models use named rigid parts such as `body`, `arm.L`, `arm.R`, `leg.L`, `leg.R`, wings and weapon/offhand nodes so a later integration pass can animate them without requiring a fully skinned mesh first.

The generator intentionally does not download or copy third-party character assets.

## Files

- `art/blender/unit_specs.json` — one design specification per troop and hero.
- `tools/blender/generate_unit.py` — original procedural modeling system.
- `tools/blender/run_generator.py` — Blender Z-up runner used by CI.
- `.github/workflows/blender-characters.yml` — GitHub Actions entry point.

## GitHub Actions

Open **Actions → Build Blender characters → Run workflow**.

Inputs:

- `scope=single` — generate one troop or hero.
- `scope=all-troops` — generate every troop for the requested levels.
- `scope=all-heroes` — generate every hero for the requested levels.
- `scope=all` — generate both groups.
- `kind` — `troop` or `hero` when `scope=single`.
- `unit` — internal id such as `guardian`, `ranger`, `giant`, `king`, `queen`, `regent`.
- `levels` — examples: `1`, `1,5,10,15`, `1-15`, or for heroes `1-50`.
- `save_blend=true` — include editable Blender files in the downloaded workflow artifact.
- `commit_assets=true` — also commit GLB/PNG/metadata (not .blend) under `dist/assets/characters-blender/`.

For visual review, generate one unit first and inspect its PNGs before committing hundreds of binary assets.

## Level evolution

Every level changes at least scale/material/detail parameters. Milestone tiers also alter real geometry and silhouette.

Troops use 15 levels. Across the progression they gain chest armor, belt/trim, shoulder plates, greaves, silhouette spikes, magic/core details and stronger weapon presentation. Unique weapons and class silhouettes remain consistent so a Guardian never becomes a recolored Ranger, for example.

Heroes use 50 levels. Their progression has more geometry tiers than troops: layered armor, bracers, shoulder gems, aura rings, orbiting prestige gems, increasingly elaborate crowns/helmets and stronger elemental materials. The base identity, weapon, offhand, cape/wings and persistent motif are hero-specific.

## Current troop IDs

`guardian`, `ranger`, `giant`, `raider`, `mage`, `breaker`, `wyvern`, `colossus`, `lancer`, `bomber`, `healer`, `berserker`, `musketeer`, `sentinel`, `assassin`, `frostweaver`, `hammerguard`, `stormcaller`, `valkyrie`, `drake`, `duelist`, `phoenix`.

## Current hero IDs

`king`, `queen`, `prince`, `champion`, `warden`, `sentinel`, `oracle`, `berserker`, `huntress`, `alchemist`, `duelist`, `pyromancer`, `beastmaster`, `assassin`, `frostguard`, `templar`, `runesmith`, `captain`, `wraith`, `regent`, plus Builder Base `machine`.

## Output structure

```text
generated/blender/
  manifest.json
  troops/
    guardian/
      level-01/
        guardian-level-01.glb
        guardian-level-01.png
        guardian-level-01.blend   # when requested
        metadata.json
  heroes/
    king/
      level-01/
        king-level-01.glb
        king-level-01.png
        king-level-01.blend       # when requested
        metadata.json
```

## Local Blender command

```powershell
blender -b --python tools/blender/run_generator.py -- --kind troop --unit guardian --levels 1-15 --output generated/blender --preview-size 512 --save-blend
```

Hero example:

```powershell
blender -b --python tools/blender/run_generator.py -- --kind hero --unit king --levels 1-50 --output generated/blender --preview-size 512 --save-blend
```

## Integration note

The current browser game still constructs its live battlefield characters procedurally in `dist/world.js`. The Blender workflow first creates reviewable standalone assets. After the models are visually accepted, integrate their GLBs into the Three.js runtime and preserve the named rigid-part nodes for walking/attack/idle animation. Do not remove the existing procedural constructors until GLB loading has a tested fallback and mobile performance has been measured.
