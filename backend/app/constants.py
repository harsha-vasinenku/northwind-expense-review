"""Application-wide constants for Northwind Expense Review."""

from enum import Enum


class Verdict(str, Enum):
    COMPLIANT = "compliant"
    FLAGGED = "flagged"
    NEEDS_REVIEW = "needs_review"


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseCategory(str, Enum):
    MEALS = "Meals"
    TRAVEL_AIR = "Travel-Air"
    TRAVEL_GROUND = "Travel-Ground"
    LODGING = "Lodging"
    CONFERENCE = "Conference"
    OTHER = "Other"


# Policy document IDs present in the data — used for missing policy detection
ALL_TE_POLICY_IDS: dict[str, str] = {
    "TEP-001": "T&E Overview",
    "TEP-005": "Air Travel Policy",
    "TEP-009": "Employee Grades Reference",
    "TEP-013": "International Travel Policy",
}

NON_TE_POLICY_IDS: frozenset[str] = frozenset({"COC-001", "REC-001", "SEC-201", "SUS-001"})

# Confidence thresholds
CONFIDENCE_HIGH = 0.9
CONFIDENCE_MEDIUM = 0.6

# Max file size for uploads (20 MB)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".txt"})

EXPENSE_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Meals": ["restaurant", "cafe", "diner", "eatery", "food", "grill", "bistro", "kitchen"],
    "Travel-Air": ["airlines", "air lines", "airways", "flight", "delta", "united", "southwest", "american", "alaska"],
    "Travel-Ground": ["uber", "lyft", "taxi", "rideshare", "transit", "cab"],
    "Lodging": ["hotel", "marriott", "hilton", "hyatt", "inn", "resort", "suites", "lodge"],
    "Conference": ["conference", "registration", "summit", "workshop", "seminar", "symposium"],
    "Other": [],
}
