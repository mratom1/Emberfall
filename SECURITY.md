# Emberfall v4 security notes

Use the complete Node server for any shared game or purchases. Standalone localStorage is intentionally a local game: players control it. The server does not import that state or accept wallet, level, timer, damage or reward uploads.

## Controls implemented

- Server-authoritative economy, construction, Town Hall hero gates, training, combat and rewards.
- Cryptographic session tokens stored only as hashes in SQLite; HttpOnly, SameSite cookies; Secure cookies with the HTTPS configuration.
- Public account operations require HTTPS. Localhost HTTP is allowed for development.
- Session rotation on registration/sign-in, explicit sign out, and password changes that revoke other sessions.
- Salted asynchronous scrypt (`N=32768, r=8, p=3`), bounded to four concurrent computations. Legacy v2 hashes migrate after a successful login.
- CSRF tokens and Origin checks on authenticated mutations. Every player battle lookup checks ownership; clan actions check membership and leadership.
- JSON object validation, 64 KiB request limits, request/header timeouts, per-IP authentication/session limits and per-player API limits. Active battles are capped at 128.
- Parameterized SQL and transactions for currency, idempotency, war results and payments.
- Reserved PvP loot prevents the same defender funds from being spent and looted twice. Unused loot returns after settlement.
- War, Capital and league attack budgets are recorded on the server. Rewards have claim records. Duplicate payment event types cannot credit the same paid order twice.
- Stripe prices and quantities come from the server. Raw-body signatures, timestamp windows, order/player identity, session ID, amount, currency and paid status are checked. A success URL never grants gems.
- Content Security Policy restricts scripts to local files; no inline script handlers. Framing is blocked. HSTS is enabled with secure deployment settings.
- Only `dist/` assets are served; dot paths, backend files, environment files and databases are not public.
- Docker runs as a non-root user with a read-only root filesystem, dropped capabilities, no-new-privileges, process/memory limits and a separate writable data volume.

- Wall batches validate unique owned IDs, current levels, Town Hall caps, currency eligibility and total funds before any debit. Army presets never grant locked troops or camp capacity.
- Commands retry with one ID for less than the 24-hour server cache window. Unconfirmed commands block new command spending; retries are bounded and account-bound.
- Automatic backups run separately, validate SQLite integrity, restrict permissions and rotate only automatic snapshots.
- GitHub actions are pinned to verified commits with least-privilege permissions. VPS transfer verifies SSH host keys; deploy checks backups and health before completing. Rollback preserves player volumes.

## Verification and limits

`npm test` runs gameplay, integration, expansion and security checks. Security checks exercise forged balances/levels/rewards, foreign battles, CSRF, malformed bodies, token rotation/revocation, password checks, data-file exposure, payment signatures and loot reservation. Payment integration tests simulate signed provider events; no live charge was made.

These controls and passing checks are not a guarantee against all vulnerabilities. An external penetration test, browser security review, load test, Docker execution and live TLS/payment deployment were not performed here. This is a single-process SQLite server intended for a small deployment, not a large MMO platform.

For Internet deployment, use the HTTPS Compose configuration or a correctly configured existing reverse proxy. Keep Node/Docker/OS images patched and back up the data volume outside the server. Protect SSH and payment credentials. Restrict direct access to the backend port when using a proxy. Apply edge rate limiting or bot/DDoS protection appropriate to your traffic; the built-in limits do not replace network-level protection. No MFA, email password recovery, anti-bot attestation, moderation console or automated refund/dispute reconciliation is included.

The server deliberately does not trust forwarded IP headers from arbitrary clients. Behind a reverse proxy, the built-in IP-based auth limit may be shared by visitors; apply per-client limits at the trusted proxy and tune server limits for your real deployment. Do not change this to blindly trust X-Forwarded-For.

## References used for the implementation

- [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): scrypt work factors and gradual rehashing.
- [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): session renewal and invalidation.
- [OWASP Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html): browser execution restrictions.
- [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature): raw-body signature verification.
