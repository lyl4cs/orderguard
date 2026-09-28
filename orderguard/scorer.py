"""Combines every rule into one decision."""

from orderguard.models import Order, ScoreResult
from orderguard import rules

# Score thresholds. A single weak signal can't reach "review";
# "decline" needs several strong signals stacking up.
REVIEW_AT = 30
DECLINE_AT = 60


def decide(score: int) -> str:
    if score >= DECLINE_AT:
        return "decline"
    if score >= REVIEW_AT:
        return "review"
    return "approve"


def score_order(
    order: Order,
    store_median_cents: int,
    recent_orders: list[Order] | None = None,
) -> ScoreResult:
    results = [
        rules.check_high_value(order, store_median_cents),
        rules.check_first_order_high_value(order, store_median_cents),
        rules.check_velocity(order, recent_orders or []),
        rules.check_address_mismatch(order),
        rules.check_disposable_email(order),
        rules.check_bulk_quantity(order, store_median_cents),
    ]

    # Rules that didn't fire return None, so they never show up as empty reasons.
    fired = [r for r in results if r is not None]
    score = sum(r.points for r in fired)

    return ScoreResult(
        decision=decide(score),
        score=score,
        reasons=[r.reason for r in fired],
    )
