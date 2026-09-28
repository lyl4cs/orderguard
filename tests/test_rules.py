from datetime import timedelta

import pytest

from orderguard.models import LineItem
from orderguard.rules import (
    check_address_mismatch,
    check_bulk_quantity,
    check_disposable_email,
    check_first_order_high_value,
    check_high_value,
    check_velocity,
)
from tests.helpers import BASE_TIME, MEDIAN, make_order


# ---- Address mismatch

def test_same_address_returns_none():
    assert check_address_mismatch(make_order()) is None


def test_different_state_is_weak_signal():
    result = check_address_mismatch(make_order(shipping=("US", "TX")))
    assert result.points == 5
    assert result.reason == "Billing state (IL) differs from shipping state (TX)"


def test_different_country_beats_state():
    result = check_address_mismatch(make_order(shipping=("NG", "LA")))
    assert result.points == 25
    assert result.reason == "Billing country (US) differs from shipping country (NG)"


def test_address_comparison_is_case_insensitive():
    assert check_address_mismatch(make_order(billing=("us", "il"))) is None


# ---- High value

def test_normal_total_returns_none():
    assert check_high_value(make_order(total_cents=4000), MEDIAN) is None


def test_exactly_3x_median_is_15_points():
    assert check_high_value(make_order(total_cents=12000), MEDIAN).points == 15


def test_just_under_5x_is_still_15_points():
    assert check_high_value(make_order(total_cents=19999), MEDIAN).points == 15


def test_exactly_5x_median_is_30_points():
    assert check_high_value(make_order(total_cents=20000), MEDIAN).points == 30


def test_high_value_reason_text():
    result = check_high_value(make_order(total_cents=24000), MEDIAN)
    assert result.reason == "Order total $240.00 is 6.0x the store's typical order ($40.00)"


@pytest.mark.parametrize("bad_median", [0, -100])
def test_non_positive_median_raises(bad_median):
    with pytest.raises(ValueError):
        check_high_value(make_order(), bad_median)


# ---- First-time customer + high value

def test_first_order_high_value_fires():
    result = check_first_order_high_value(make_order(is_first_order=True, total_cents=12000), MEDIAN)
    assert result.points == 20
    assert result.reason == "First-time customer placing a $120.00 order"


def test_first_order_normal_value_is_fine():
    assert check_first_order_high_value(make_order(is_first_order=True), MEDIAN) is None


def test_returning_customer_high_value_is_fine():
    assert check_first_order_high_value(make_order(total_cents=12000), MEDIAN) is None


# ---- Disposable email

def test_disposable_email_fires():
    result = check_disposable_email(make_order(email="x@Mailinator.com"))
    assert result.points == 20
    assert result.reason == "Email uses a disposable domain (mailinator.com)"


def test_normal_email_is_fine():
    assert check_disposable_email(make_order(email="jane@gmail.com")) is None


# ---- Bulk quantity

def test_many_units_of_expensive_item_fires():
    order = make_order(line_items=[LineItem("Serum", 5, 4500)])
    result = check_bulk_quantity(order, MEDIAN)
    assert result.points == 20
    assert result.reason == "5 units of 'Serum' at $45.00 each"


def test_many_units_of_cheap_item_is_fine():
    order = make_order(line_items=[LineItem("Hair tie", 20, 300)])
    assert check_bulk_quantity(order, MEDIAN) is None


def test_few_units_of_expensive_item_is_fine():
    order = make_order(line_items=[LineItem("Serum", 4, 4500)])
    assert check_bulk_quantity(order, MEDIAN) is None


# ---- Velocity

def _earlier(n, minutes_ago, **overrides):
    return make_order(order_id=f"past-{n}", created_at=BASE_TIME - timedelta(minutes=minutes_ago), **overrides)


def test_no_history_returns_none():
    assert check_velocity(make_order(), []) is None


def test_third_order_from_same_email_in_window_fires():
    history = [_earlier(1, 2, ip="198.51.100.1"), _earlier(2, 5, ip="198.51.100.2")]
    result = check_velocity(make_order(), history)
    assert result.points == 30
    assert result.reason == "3 orders from this email in the last 10 minutes"


def test_email_match_is_case_insensitive():
    history = [_earlier(1, 2, email="JANE@example.com"), _earlier(2, 5, email="jane@EXAMPLE.com")]
    assert check_velocity(make_order(), history) is not None


def test_same_ip_different_emails_fires():
    history = [_earlier(1, 1, email="a@example.com"), _earlier(2, 3, email="b@example.com")]
    result = check_velocity(make_order(), history)
    assert result.reason == "3 orders from this IP address in the last 10 minutes"


def test_orders_outside_window_are_ignored():
    history = [_earlier(1, 30), _earlier(2, 60)]
    assert check_velocity(make_order(), history) is None


def test_duplicate_delivery_of_same_order_is_not_counted():
    same = make_order()
    assert check_velocity(same, [same, same]) is None
