"""Generator configuration.

Every value here is a *synthetic* implementation default (PRD section 18 /
TAD section 25). Nothing is a claim about any real marketplace.
Values are version-controlled so metric outputs stay traceable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ---------------------------------------------------------------- namespace
# Deterministic UUIDv5 generation: same seed + natural key => same UUID.
UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "marketplace-fulfillment-warehouse")


def stable_uuid(kind: str, natural_key: str) -> uuid.UUID:
    """Deterministic UUIDv5 from a kind + business natural key."""
    return uuid.uuid5(UUID_NAMESPACE, f"{kind}:{natural_key}")


# ---------------------------------------------------------------- timeframe
DATA_START = datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
DATA_END = datetime(2026, 11, 8, 0, 0, 0, tzinfo=timezone.utc)  # exclusive

# ---------------------------------------------------------------- fee policy
FEE_RATE = 0.15  # 15% synthetic seed default (fictional; configurable)
FEE_CURRENCY = "USD"

# ------------------------------------------------------- lifecycle behaviour
ACCEPTANCE_WINDOW_MINUTES = 240          # CREATED -> EXPIRED if not accepted
PAYMENT_RETRY_LIMIT = 3                  # attempts per booking
PAYMENT_RETRY_SPACING_MINUTES = 5
PAYOUT_DELAY_MIN_DAYS = 1                # completion -> payout initiation
PAYOUT_DELAY_MAX_DAYS = 7
COHORT_MATURITY_WINDOW_DAYS = 14         # cohort maturity cutoff (PRD 8.1)

# Booking status values (TAD 8.1)
STATUS_CREATED = "CREATED"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_CANCELLED = "CANCELLED"
STATUS_REJECTED = "REJECTED"
STATUS_EXPIRED = "EXPIRED"
STATUS_NO_SHOW = "NO_SHOW"

# Allowed-transition contract — the single source of truth shared by the
# generator AND the dbt validation tests (TAD 8.2).
ALLOWED_TRANSITIONS: dict[str | None, set[str]] = {
    None: {STATUS_CREATED},
    STATUS_CREATED: {STATUS_ACCEPTED, STATUS_REJECTED, STATUS_EXPIRED, STATUS_CANCELLED},
    STATUS_ACCEPTED: {STATUS_SCHEDULED, STATUS_CANCELLED},
    STATUS_SCHEDULED: {STATUS_IN_PROGRESS, STATUS_CANCELLED, STATUS_NO_SHOW},
    STATUS_IN_PROGRESS: {STATUS_COMPLETED, STATUS_CANCELLED},
}
TERMINAL_STATUSES = {
    STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_REJECTED,
    STATUS_EXPIRED,
    STATUS_NO_SHOW,
}

ACTOR_CUSTOMER = "CUSTOMER"
ACTOR_PROVIDER = "PROVIDER"
ACTOR_SYSTEM = "SYSTEM"

# ------------------------------------------------------------- scenario mix
# Outcome proportions for ordinary (non-fixture) bookings. Sum of completed +
# cancelled + rejected + expired + no_show must equal 1.0.
DEFAULT_SCENARIO_PROPORTIONS = {
    "completed": 0.62,
    "customer_cancelled": 0.12,
    "provider_cancelled": 0.06,
    "rejected": 0.06,
    "expired": 0.06,
    "no_show": 0.05,
    # reserved: 0.03 -> booking whose payment attempts all fail (cannot complete)
    "payment_exhausted": 0.03,
}

# Share of bookings that are rescheduled at least once (booking ID retained).
RESCHEDULE_PROPORTION = 0.18

# Payment / refund mix for completed bookings.
PARTIAL_REFUND_PROPORTION = 0.25   # 10-40% of captured value refunded
FULL_REFUND_PROPORTION = 0.05      # 100% of captured value refunded
REVERSAL_PROPORTION = 0.03         # posted capture reversal instead of refund
FAILED_FIRST_ATTEMPT_PROPORTION = 0.15  # retry after one failure

# Payout status mix.
PAYOUT_PAID_PROPORTION = 0.85
PAYOUT_PENDING_PROPORTION = 0.12   # remainder split failed/reversed

CANCELLATION_REASONS_CUSTOMER = ["CHANGE_OF_PLANS", "FOUND_ALTERNATIVE", "PRICE"]
CANCELLATION_REASONS_PROVIDER = ["SCHEDULE_CONFLICT", "EMERGENCY", "CAPACITY"]
RESCHEDULE_REASONS = ["CUSTOMER_REQUEST", "PROVIDER_REQUEST", "CONFLICT"]
FAILURE_CODES = ["CARD_DECLINED", "INSUFFICIENT_FUNDS", "PROCESSOR_ERROR"]

# ------------------------------------------------------------------ scales
@dataclass
class ScaleConfig:
    name: str
    customers: int
    providers: int
    bookings: int
    neighborhoods_per_borough: int = 3
    availability_intervals_per_provider: int = 100

    @property
    def availability_intervals(self) -> int:
        return self.providers * self.availability_intervals_per_provider


SCALES: dict[str, ScaleConfig] = {
    # Fast development / CI fixture dataset.
    "small": ScaleConfig("small", 50, 10, 200, 3, 25),
    # Portfolio demo target (PRD section 9.1 volume targets).
    "medium": ScaleConfig("medium", 5000, 500, 50000, 3, 100),
}

# ------------------------------------------------------------------ catalog
SERVICE_CATEGORIES = [
    "furniture_assembly",
    "home_cleaning",
    "plumbing",
    "electrical_repairs",
    "painting",
    "moving_assistance",
]

BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

NEIGHBORHOODS = {
    "Manhattan": ["Harborview", "Midline", "Eastcrest"],
    "Brooklyn": ["Ferngate", "Dockside", "Maple Row"],
    "Queens": ["Larkspur", "Auburndale South", "Willow Point"],
    "Bronx": ["Rivermont", "Hillcrest North", "Sycamore"],
    "Staten Island": ["Bayberry", "Cedar Landing", "Fox Hollow"],
}
# Synthetic names on purpose: generated activity is not a representation of
# actual local demand/supply in these areas (PRD 5.2).

# Duration / value distributions per category (minutes, USD).
CATEGORY_PROFILE = {
    "furniture_assembly": {"duration": (90, 180), "value": (60.0, 150.0)},
    "home_cleaning": {"duration": (120, 240), "value": (80.0, 200.0)},
    "plumbing": {"duration": (60, 150), "value": (90.0, 250.0)},
    "electrical_repairs": {"duration": (60, 180), "value": (100.0, 280.0)},
    "painting": {"duration": (180, 360), "value": (150.0, 400.0)},
    "moving_assistance": {"duration": (180, 300), "value": (120.0, 320.0)},
}

# Eligibility: each provider is eligible for 2-4 categories and 2-4 regions.
ELIGIBILITY_MIN_CATEGORIES = 2
ELIGIBILITY_MAX_CATEGORIES = 4
ELIGIBILITY_MIN_REGIONS = 2
ELIGIBILITY_MAX_REGIONS = 4
