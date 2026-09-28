# OrderGuard

**Fraud screening for small Shopify stores. It learns what a normal order looks like for one store, explains every flag in plain language, and alerts the owner before a risky order ships.**

> 🚧 **Status: in development.** This README describes what the project is being built to do. Features are marked as they ship.

---

## The problem

Small online stores lose real money to fraud. Someone checks out with a stolen card, the real cardholder disputes the charge, and the store loses the product, the payment, *and* a chargeback fee on top. For a small business, a handful of these a month adds up fast.

## What OrderGuard does

1. **Receives every new order** automatically through Shopify webhooks.
2. **Scores its risk** using a set of transparent rules plus a model trained on the store's own order history.
3. **Explains every decision** in plain language, e.g.:
   > ⚠️ High risk: shipping address is 1,200 miles from billing address · 3rd order from this card in 10 minutes · order value is 4× this store's average
4. **Alerts the owner before the order ships**, so they can review it instead of finding out after the chargeback.

## How this differs from Shopify's built-in fraud analysis

Shopify's fraud analysis is built for every store. OrderGuard is built for one.

| | Shopify fraud analysis | OrderGuard |
|---|---|---|
| **Baseline** | Generic, across all merchants | Learns *this store's* normal order size, regions, and products |
| **Transparency** | Risk rating with limited indicators | Every flag explained; rules and thresholds are editable |
| **Action** | Rating on an admin page you have to check | Proactive alert to the owner before shipping |
| **Network data** | ✅ Sees patterns across millions of stores | ❌ Doesn't have this, and doesn't try to replace it |

An order that's completely normal for a big retailer can be a real red flag for a small beauty brand. OrderGuard is meant to **complement** Shopify's network-level signals, not replace them.

## Planned architecture

```
Shopify store ──(order webhook)──▶ FastAPI service ──▶ Rules engine ──┐
                                        │                             ├──▶ Risk score + reasons ──▶ Owner alert
                                        │               Anomaly model ─┘
                                        ▼
                                    PostgreSQL
                         (orders, scores, reviews, store baselines)
```

**Stack:** Python · FastAPI · PostgreSQL · pytest · scikit-learn

## Roadmap

- [ ] **v1: Single store**
  - [ ] Core risk scoring in plain Python (rules + explanations), fully tested
  - [ ] FastAPI endpoint that accepts an order and returns a decision
  - [ ] Shopify webhook integration
  - [ ] Owner alerts for high-risk orders
  - [ ] Simulated attack test suite (card testing, address mismatch, velocity bursts)
- [ ] **v2: Learning**
  - [ ] Anomaly model trained on the store's own order history
  - [ ] Feedback loop: owner marks flags as "fraud" or "false alarm," accuracy is tracked
- [ ] **v3: Multi-store**
  - [ ] Per-store baselines, rules, and thresholds (multi-tenancy)
  - [ ] Cold start: new stores begin on a general model and shift to their own baseline
  - [ ] Privacy-preserving shared signals across stores (hashed identifiers only)

## Privacy

This project handles real customer data, so:

- **No real customer data is ever committed** to this repository. All examples and tests use synthetic data.
- **Secrets live in `.env`**, which is git-ignored.
- Cross-store signals (v3) will only ever share one-way hashes of identifiers, never raw customer information.

## Running locally

_Coming with v1._

---

Built by [Layth Sarama](https://github.com/lyl4cs).
