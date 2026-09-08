# Gem purchases

Stripe-hosted Checkout is implemented. No card details pass through the game server or game UI.

## Enable

Configure HTTPS, STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in .env. Start with Stripe test credentials. A registered game account is required to purchase.

Webhook: `https://YOUR_DOMAIN/api/payments/webhook`

Events:
- checkout.session.completed
- checkout.session.async_payment_succeeded

Restart after changing keys. compose.https.yml sets PUBLIC_URL and secure cookies from DOMAIN. With an existing proxy, set PUBLIC_URL=https://YOUR_DOMAIN, COOKIE_SECURE=true and NODE_ENV=production yourself.

## Catalog

| Pack | Gems | Price |
|---|---:|---:|
| Pouch | 500 | USD 4.99 |
| Chest | 1,200 | USD 9.99 |
| Vault | 2,500 | USD 19.99 |

Edit GEM_PACKS in dist/model.js to change future orders. Stored orders keep their original amount/quantity. Prices are game configuration choices, not Clash of Clans prices.

## Fulfillment

The browser sends only the pack ID. The server creates and stores an order with its own amount, quantity and player reference, then creates Checkout.

A raw-body webhook must pass HMAC-SHA256 verification and a five-minute timestamp window. Paid status, session ID, player reference, currency and amount must match the stored order. Order credit and event recording happen inside one SQLite transaction. Duplicate event IDs or different events for an already-paid order do not credit twice. Visiting the success URL never grants gems.

Live payment operation was not tested or activated. Tests use a local fake provider and signed local notifications; no external payment request was made. Refund/dispute reconciliation is not automated and requires an operator process. No browser-accessible admin credit endpoint is exposed.

Another payment provider requires adapting server/payments.mjs and the order endpoints, including provider-authenticated notifications. Never accept a browser-supplied paid flag.

Integration references:
- [Stripe Checkout Session API](https://docs.stripe.com/api/checkout/sessions/create)
- [Webhook handling](https://docs.stripe.com/webhooks)
- [Raw-body signature requirements](https://docs.stripe.com/webhooks/signature)
