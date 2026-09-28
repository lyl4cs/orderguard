from datetime import datetime, timezone

from orderguard.models import Address, LineItem, Order

BASE_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
MEDIAN = 4000  # $40.00 typical order


def make_order(
    order_id="order-1",
    email="jane@example.com",
    total_cents=4000,
    billing=("US", "IL"),
    shipping=("US", "IL"),
    is_first_order=False,
    created_at=BASE_TIME,
    ip="203.0.113.10",
    line_items=None,
) -> Order:
    """A normal, low-risk order. Override only the fields a test cares about."""
    return Order(
        order_id=order_id,
        email=email,
        total_cents=total_cents,
        billing=Address(country=billing[0], province=billing[1], zip_code="60462"),
        shipping=Address(country=shipping[0], province=shipping[1], zip_code="60462"),
        is_first_order=is_first_order,
        created_at=created_at,
        ip=ip,
        line_items=line_items if line_items is not None else [LineItem("Lip gloss", 1, 4000)],
    )
