# OrderGuard

**Fraud screening for small Shopify stores. It flags risky orders and explains why, before they ship.**

> Status: scoring engine and HTTP API are built and tested. Shopify integration is next. See [Roadmap](#roadmap).

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

```json
{
  "order_id": "demo-1001",
  "decision": "decline",
  "score": 75,
  "reasons": [
    "Order total $240.00 is 6.0x the store's typical order ($40.00)",
    "First-time customer placing a $240.00 order",
    "Billing country (US) differs from shipping country (CA)"
  ]
}
```

Scores below 30 are `approve`, 30 to 59 are `review`, and 60 or more are `decline`.

The shop owner will get an alert for high-risk orders, so they can decide whether to fulfill the order in a few seconds.

## Signals it checks (v1)

- **Address mismatch.** Billing and shipping are in different countries or states. Weak on its own, since gifts are common, but meaningful combined with other signals.
- **Unusually large order.** The total is far above what this store normally sees.
- **Velocity.** Several orders from the same email or IP in a short window. This is a common pattern in card testing.
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
No. It only recommends and alerts. The owner makes every final call. A planned v2 will use the owner's decisions to tune the scoring over time.

**Does it see customers' card numbers?**
No. Shopify doesn't show full card details, and OrderGuard doesn't need them in order to function. It works from other sorts of order data like total price, billing/shipping address, email, and IP.

**Why rules instead of machine learning?**
Rules are explainable, testable, and they work from the first order. Small stores rarely have enough fraud history to train a model on. A model trained on the store's own history is planned as a *supplement* to the rules, not a replacement.

**What about false positives?**
A flag means "check this out," not "this is fraud, and needs to be immediately canceled." Weak signals like billing/shipping mismatches (common with gifts) score low on purpose, so only combinations of signals push an order toward `decline`.

**Is any real customer data in this repo?**
No. All tests and examples use synthetic orders. 

## Roadmap

| Milestone | Status |
|---|---|
| M1: Core scoring rules + tests | Done (6 rules, 40+ tests) |
| M2: FastAPI `/score` endpoint | Done (recent-order history is in memory until M3) |
| M3: PostgreSQL persistence + velocity rules | Not started |
| M4: Shopify webhooks (HMAC verification, idempotency) | Not started |
| M5: Owner alerts | Not started |
| M6: Simulated attack suite + deployment | Started (card-testing and resale scenarios are tested) |
| v2: Model trained on store history, owner feedback loop | Planned |

## Run it locally

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m pytest                       # run the tests
uvicorn orderguard.api:app --reload    # start the API
```

Then score the example order:

```bash
curl -X POST http://127.0.0.1:8000/score \
  -H "Content-Type: application/json" \
  -d @examples/risky_order.json
```

Interactive API docs are at http://127.0.0.1:8000/docs.

Set `STORE_MEDIAN_CENTS` to the store's typical order total in cents (default `4000`, i.e. $40.00).

## Project layout

```
orderguard/
├── models.py   # Order, Address, LineItem, RuleResult, ScoreResult
├── rules.py    # the six risk rules, one function each
├── scorer.py   # runs every rule, adds up points, picks a decision
└── api.py      # FastAPI app: POST /score, GET /health
tests/          # rule, scorer, simulated-attack and API tests
examples/       # sample order JSON
```

## Tech stack

Python · pytest · FastAPI · PostgreSQL (M3)
