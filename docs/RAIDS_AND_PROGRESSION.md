# Raids, progression and gems

This update keeps existing saves and adds the following playable systems. The landscape web preview runs locally against AI; running `npm start` on one shared server enables player matchmaking and trusted wallets. GitHub stores the source and builds the apps; GitHub Pages cannot run this Node/SQLite backend.

## Heroes and villages

- The roster shows each original hero's portrait, current 3D appearance, HP, damage per hit, DPS, range, and next-level improvement. Town Hall unlocks and level caps still apply.
- All home heroes and the Builder Base Battle Machine change geometry, armor or ornaments at every level. Material tiers change at levels 11, 21, 31 and 41. The illustrated portrait retains the character's identity; its rank frame changes alongside the live 3D model.
- Owned heroes appear near the actual army camp. Resting/upgrading heroes have a resting pose. Trained troops also appear at camps, with a representative maximum of five models per type and thirty total. The army panel retains the exact counts.
- Every building changes visible geometry, trim or material with its level. Walls have fifteen distinct levels.
- After placing a wall, the next wall preview stays active at an available adjacent tile. Tap another tile to change the direction; use **Add wall** to continue and **Done** to finish. Each tile is collision-checked and charged separately. The existing group upgrade tool remains available.

## Random raids

**Find a match** chooses a random unshielded player within two Town Hall levels, preferring the closest level and avoiding recent opponents where possible. Clanmates and villages already in battle are excluded. If no suitable player is available, the game creates an explicitly labeled AI village within one Town Hall level of the attacker. **Next village** changes the opponent before deployment without spending troops.

Raids use the defender's saved building positions, levels and defensive damage rules. The server simulates movement, wall blocking, damage and results. Player battles are asynchronous attacks against saved defenses, not simultaneous live control by both players.

For each of gold, elixir and dark elixir:

```
available loot = floor(defender's stored balance / 10)
earned loot = floor(available loot * destruction percent / 100)
```

Gold/elixir awards are limited to the attacker's remaining storage. The defender loses only the amount actually credited. Gems cannot be stolen. Player loot is reserved when the opponent is selected; unused loot is refunded when the battle ends or an untouched scouting session expires after five minutes. One open raid can reserve a village at a time. Settlement and command retries are transactional and do not award loot twice.

Both players receive timestamped attack/defense records with opponent type, Town Hall, stars, destruction and all three resource amounts. The UI retains the latest 100 records. Campaign and other battle rewards remain governed by their own modes; the 10% rule applies to rival village raids.

## Incoming AI raids

An unshielded village becomes eligible six hours after initialization or its last incoming raid. If no suitable human attacker has been active in the last fifteen minutes, and the owner has been away for at least five minutes, the server can send a level-matched AI army. It uses the same combat simulation and maximum 10% loss rule. There is no accumulation of attacks for every missed six-hour period.

The shared server checks for incoming AI raids once a minute and processes at most five villages per pass. The standalone preview cannot run while its page is closed; it checks for one eligible AI raid on return. All AI activity is labeled as AI in the history.

## Shields

| Shield | Gem cost |
|---|---:|
| 12 hours | 100 |
| 1 day | 180 |
| 2 days | 320 |

Shields protect against player and AI raids, with a maximum of seven days stacked. First deployment in a rival raid removes the attacker's shield; scouting and campaign battles preserve it. An incoming attack grants five minutes of protection when it finishes. A shield cannot be bought while the village is already under attack. The server supplies prices and expiration times; client-supplied discounts are ignored.

## Gem sources

- **Trees:** eight-second removal, 75 gold; a 42% chance of 1–6 gems. The shared server selects the reward. Rocks do not award gems.
- **Gem Box:** a visible box grants exactly 25 gems after a free twelve-second collection. The first box is immediately available; the next appears seven days after collection completes. At most one box waits at a time. Missed weeks cannot be claimed repeatedly.
- **Purchases:** existing Stripe Checkout packs remain unavailable until the server's payment configuration is supplied. Only a verified, matching paid webhook credits gems. The web preview cannot process purchases.

New players retain the existing starting gem allowance. Season rewards and the medal shop do not generate extra gems. Existing saved balances are preserved.

## Verification and operating limits

`npm test` includes real HTTP integration, transactional wallet and shield tests, weekly-box timing, matching and AI defense checks, camp roster checks, and a geometry/material comparison for every building level 1–15 and hero level 1–50. These checks do not replace testing the final build on the target phone. Actual Google/Facebook credentials, live payments and a shared production server must be configured by the operator. See [Accounts and apps](ACCOUNTS_AND_APPS.md), [Payments](../PAYMENTS.md), and [Security](../SECURITY.md).
