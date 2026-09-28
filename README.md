# OrderGuard

**Fraud screening for small Shopify stores. It flags risky orders and explains why, before they ship.**

> Status: in development. See [Roadmap](#roadmap) for what's built and what isn't.

---

## The problem

When a small store ships a fraudulent order, it usually loses three times:

1. **The product.** It's shipped and gone.
2. **The money.** The real cardholder files a chargeback, and the payment is reversed.
3. **A chargeback fee**, charged on top. Too many chargebacks can also put the store's payment account at risk.

Large retailers have fraud teams. A small store has one owner checking orders between everything else. Fraud is rare, which makes it easy to miss. It only takes one bad order to wipe out the profit from dozens of good ones.

## What OrderGuard does

Every new order is scored against a set of risk rules. Each rule that fires adds points and a plain-language reason. The total score maps to one of three recommendations:

| Decision | Meaning |
|---|---|
| `approve` | Nothing unusual. Ship it. |
| `review` | Something's off. Take a look before shipping. |
| `decline` | Multiple strong risk signals. Contact the customer or cancel. |

Example output:

```
Decision: review (score 40)
- Order total $240.00 is 6.0x the store's typical order ($40.00)
- Billing country (US) differs from shipping country (CA)
- First-time customer
```

Essentially the shop owner will get an alert for high risk orders, so they can decide wether or not they want to fulfill the order in a few seconds.

## Signals it checks (v1)

- **Address mismatch.** Billing and shipping are in different countries or states. Weak on its own, since gifts are common, but meaningful combined with other signals.
- **Unusually large order.** The total is far above what this store normally sees.
- **Velocity.** Several orders from the same email, IP, or address in a short window. This is a common pattern in card testing.
- **First-time customer placing a high-value order.**
- **Disposable email domain.**
- **Bulk quantity of a high-value item.** This often points to resale fraud.

## Why not just use Shopify's built-in fraud analysis?

Shopify already gives each order a risk assessment, and it's a good baseline. OrderGuard isn't meant to replace it. It differs in a few ways:
- **Transparency.** Every point in the score maps to a rule you can read in the code. There's no black box.
- **Store-specific thresholds.** "Large order" is measured against *this* store's typical order, not a global average.
- **Owner-controlled alerting.** You decide what triggers an alert and where it goes.

Honestly, it's also a learning project: building the pipeline end to end (webhooks, signature verification, idempotency, persistence, alerting) is the point.

## Frequently asked questions

**Does it block or cancel orders automatically?**
No, It only recommends and alerts, The owner makes every final call. After repeated use on a store it will adapt and make better and better decisions.

**Does it see customers' card numbers?**
No, Shopify doesn't show full card details, and OrderGuard doesn't need them in order to function. It works from other sorts of order data like total price, billing/shipping adress, email, and IP.

**Why rules instead of machine learning?**
Rules are explainable, testable, and they work from the first order. Small stores rarely have enough fraud history to train a model on. A model trained on the store's own history is planned as a *supplement* to the rules, not a replacement.

**What about false positives?**
A flag means "check this out," not "this is fraud, and needs to be immediately canceled" Weak signals like mismatched addresses due to user error will score low on purpose, so only combinations of signals push an order toward `decline`. Ultimately, the owner will make the final call, OrderGuard can only suggest.

**Is any real customer data in this repo?**
No. All tests and examples use synthetic orders. 

## Roadmap

| Milestone | Status |
|---|---|
| M1: Core scoring rules + tests | In progress |
| M2: FastAPI `/score` endpoint | Not started |
| M3: PostgreSQL persistence + velocity rules | Not started |
| M4: Shopify webhooks (HMAC verification, idempotency) | Not started |
| M5: Owner alerts | Not started |
| M6: Simulated attack suite + deployment | Not started |
| v2: Model trained on store history, owner feedback loop | Planned |

## Tech stack

Python 3.12 · pytest · FastAPI · PostgreSQL
