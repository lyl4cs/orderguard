"""Individual risk rules.

Every rule follows the same shape:
    1. pull out the data it needs from the order
    2. one `if` per case, most severe first, each returning a RuleResult
    3. `return None` when the rule doesn't fire

Rules never add up totals or make the final decision. That's scorer.py's job.
"""

from datetime import timedelta

from orderguard.models import Order, RuleResult

# Starter list, not exhaustive. Real services use lists with thousands of domains.
DISPOSABLE_EMAIL_DOMAINS = {
    "10minutemail.com",
    "dispostable.com",
    "getnada.com",
    "guerrillamail.com",
    "maildrop.cc",
    "mailinator.com",
    "sharklasers.com",
    "temp-mail.org",
    "tempmail.com",
    "throwawaymail.com",
    "trashmail.com",
    "yopmail.com",
}


def _dollars(cents: int) -> str:
    return f"${cents / 100:.2f}"


def _require_positive_median(store_median_cents: int) -> None:
    # A median of 0 is a caller bug. Returning None would silently mean "all clear".
    if store_median_cents <= 0:
        raise ValueError("store_median_cents must be positive")


def check_address_mismatch(order: Order) -> RuleResult | None:
    billing_country = order.billing.country.upper()
    shipping_country = order.shipping.country.upper()
    billing_province = order.billing.province.upper()
    shipping_province = order.shipping.province.upper()

    if billing_country != shipping_country:
        return RuleResult(
            points=25,
            reason=f"Billing country ({billing_country}) differs from shipping country ({shipping_country})",
        )

    # Weak signal on purpose: gifts shipped to another state are common.
    if billing_province != shipping_province:
        return RuleResult(
            points=5,
            reason=f"Billing state ({billing_province}) differs from shipping state ({shipping_province})",
        )

    return None


def check_high_value(order: Order, store_median_cents: int) -> RuleResult | None:
    _require_positive_median(store_median_cents)

    total = order.total_cents
    multiple = total / store_median_cents  # float is fine here: display only
    reason = (
        f"Order total {_dollars(total)} is {multiple:.1f}x "
        f"the store's typical order ({_dollars(store_median_cents)})"
    )

    # Decisions use integer math. Check 5x before 3x, or a 6x order would stop at 15 points.
    if total >= 5 * store_median_cents:
        return RuleResult(points=30, reason=reason)

    if total >= 3 * store_median_cents:
        return RuleResult(points=15, reason=reason)

    return None


def check_first_order_high_value(order: Order, store_median_cents: int) -> RuleResult | None:
    _require_positive_median(store_median_cents)

    if order.is_first_order and order.total_cents >= 3 * store_median_cents:
        return RuleResult(
            points=20,
            reason=f"First-time customer placing a {_dollars(order.total_cents)} order",
        )

    return None


def check_disposable_email(order: Order) -> RuleResult | None:
    domain = order.email.rsplit("@", 1)[-1].strip().lower()

    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return RuleResult(points=20, reason=f"Email uses a disposable domain ({domain})")

    return None


def check_bulk_quantity(
    order: Order, store_median_cents: int, min_quantity: int = 5
) -> RuleResult | None:
    """Many units of one expensive item often means resale fraud.

    "Expensive" = unit price at or above the store's typical order total.
    """
    _require_positive_median(store_median_cents)

    for item in order.line_items:
        if item.quantity >= min_quantity and item.unit_price_cents >= store_median_cents:
            return RuleResult(
                points=20,
                reason=(
                    f"{item.quantity} units of '{item.title}' "
                    f"at {_dollars(item.unit_price_cents)} each"
                ),
            )

    return None


def check_velocity(
    order: Order,
    recent_orders: list[Order],
    window_minutes: int = 10,
    threshold: int = 3,
) -> RuleResult | None:
    """Several orders from the same email or IP in a short window.

    This is the classic card-testing pattern: a fraudster tries stolen cards
    one after another. `threshold` counts the current order too, so the default
    fires on the 3rd order within 10 minutes.
    """
    window_start = order.created_at - timedelta(minutes=window_minutes)
    email = order.email.strip().lower()

    email_count = 1
    ip_count = 1
    for past in recent_orders:
        if past.order_id == order.order_id:
            continue  # don't count a duplicate delivery of the same order
        if not (window_start <= past.created_at <= order.created_at):
            continue
        if past.email.strip().lower() == email:
            email_count += 1
        if order.ip and past.ip == order.ip:
            ip_count += 1

    if email_count >= threshold:
        return RuleResult(
            points=30,
            reason=f"{email_count} orders from this email in the last {window_minutes} minutes",
        )

    if ip_count >= threshold:
        return RuleResult(
            points=30,
            reason=f"{ip_count} orders from this IP address in the last {window_minutes} minutes",
        )

    return None
