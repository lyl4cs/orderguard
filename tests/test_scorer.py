from datetime import timedelta

from orderguard.models import LineItem
from orderguard.scorer import decide, score_order
from tests.helpers import BASE_TIME, MEDIAN, make_order


def test_thresholds():
    assert decide(0) == "approve"
    assert decide(29) == "approve"
    assert decide(30) == "review"
    assert decide(59) == "review"
    assert decide(60) == "decline"


def test_normal_order_is_approved_with_no_reasons():
    result = score_order(make_order(), MEDIAN)
    assert result.decision == "approve"
    assert result.score == 0
    assert result.reasons == []


def test_gift_to_another_state_alone_is_approved():
    result = score_order(make_order(shipping=("US", "TX")), MEDIAN)
    assert result.decision == "approve"
    assert result.score == 5


def test_large_first_order_goes_to_review():
    result = score_order(make_order(total_cents=12000, is_first_order=True), MEDIAN)
    assert result.score == 35  # 15 high value + 20 first-time
    assert result.decision == "review"


def test_stacked_signals_decline():
    order = make_order(total_cents=24000, is_first_order=True, shipping=("CA", "ON"))
    result = score_order(order, MEDIAN)
    assert result.score == 75  # 30 + 20 + 25
    assert result.decision == "decline"
    assert result.reasons == [
        "Order total $240.00 is 6.0x the store's typical order ($40.00)",
        "First-time customer placing a $240.00 order",
        "Billing country (US) differs from shipping country (CA)",
    ]


# ---- Simulated attacks

def test_card_testing_burst_is_caught():
    """A fraudster tries stolen cards: many small orders, same IP, new emails."""
    history = []
    results = []
    for i in range(5):
        order = make_order(
            order_id=f"burst-{i}",
            email=f"buyer{i}@mailinator.com",
            total_cents=1500,
            created_at=BASE_TIME + timedelta(minutes=i),
            is_first_order=True,
        )
        results.append(score_order(order, MEDIAN, history))
        history.append(order)

    assert results[0].decision == "approve"  # 20 pts: disposable email only
    assert all(r.decision == "review" for r in results[2:])  # + velocity from the 3rd order on


def test_resale_fraud_is_caught():
    order = make_order(
        total_cents=45000,
        is_first_order=True,
        email="reseller@yopmail.com",
        line_items=[LineItem("Serum", 10, 4500)],
    )
    result = score_order(order, MEDIAN)
    assert result.decision == "decline"
    assert result.score == 90  # 30 high value + 20 first-time + 20 disposable + 20 bulk
