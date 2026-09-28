"""HTTP API: POST an order, get back a decision with reasons.

Run locally:
    uvicorn orderguard.api:app --reload
Then open http://127.0.0.1:8000/docs for interactive docs.
"""

import os
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from orderguard.models import Address, LineItem, Order
from orderguard.scorer import score_order

# The store's typical (median) order total, in cents. Set it per store.
STORE_MEDIAN_CENTS = int(os.environ.get("STORE_MEDIAN_CENTS", "4000"))

# Recent orders for the velocity rule. In memory only: it resets when the
# server restarts. M3 replaces this with PostgreSQL.
HISTORY_LIMIT = 1000
recent_orders: deque[Order] = deque(maxlen=HISTORY_LIMIT)

app = FastAPI(
    title="OrderGuard",
    description="Fraud screening for small Shopify stores. Flags risky orders and explains why.",
    version="0.1.0",
)


# ---- Request / response shapes. Pydantic validates these and returns a 422 on bad input.

class AddressIn(BaseModel):
    country: str = Field(min_length=2, max_length=2, examples=["US"])
    province: str = Field(min_length=1, examples=["IL"])
    zip_code: str = Field(min_length=1, examples=["60462"])


class LineItemIn(BaseModel):
    title: str
    quantity: int = Field(gt=0)
    unit_price_cents: int = Field(ge=0)


class OrderIn(BaseModel):
    order_id: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["jane@example.com"])
    total_cents: int = Field(ge=0, examples=[24000])
    billing: AddressIn
    shipping: AddressIn
    is_first_order: bool
    created_at: datetime | None = None  # defaults to "now"
    ip: str | None = None
    line_items: list[LineItemIn] = []


class ScoreOut(BaseModel):
    order_id: str
    decision: str
    score: int
    reasons: list[str]


def to_order(data: OrderIn) -> Order:
    created_at = data.created_at or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        # Treat timestamps without a timezone as UTC so comparisons never mix the two.
        created_at = created_at.replace(tzinfo=timezone.utc)

    return Order(
        order_id=data.order_id,
        email=data.email,
        total_cents=data.total_cents,
        billing=Address(**data.billing.model_dump()),
        shipping=Address(**data.shipping.model_dump()),
        is_first_order=data.is_first_order,
        created_at=created_at,
        ip=data.ip,
        line_items=[LineItem(**item.model_dump()) for item in data.line_items],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/score", response_model=ScoreOut)
def score(data: OrderIn) -> ScoreOut:
    order = to_order(data)
    result = score_order(order, STORE_MEDIAN_CENTS, list(recent_orders))

    # Same order sent twice (a retry) is scored again but stored once.
    if not any(past.order_id == order.order_id for past in recent_orders):
        recent_orders.append(order)

    return ScoreOut(
        order_id=order.order_id,
        decision=result.decision,
        score=result.score,
        reasons=result.reasons,
    )
