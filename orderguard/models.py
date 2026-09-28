from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Address:
    country: str  # ISO 2-letter code, e.g. "US"
    province: str  # state/province code, e.g. "IL"
    zip_code: str  # a string: "02134" must keep its leading zero


@dataclass
class LineItem:
    title: str
    quantity: int
    unit_price_cents: int


@dataclass
class Order:
    order_id: str
    email: str
    total_cents: int  # integer cents, never float dollars
    billing: Address
    shipping: Address
    is_first_order: bool
    created_at: datetime
    ip: str | None = None
    line_items: list[LineItem] = field(default_factory=list)


@dataclass
class RuleResult:
    points: int
    reason: str  # plain-language explanation shown to the store owner


@dataclass
class ScoreResult:
    decision: str  # "approve", "review" or "decline"
    score: int
    reasons: list[str]
