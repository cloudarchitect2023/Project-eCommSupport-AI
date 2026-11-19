from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS = (
    r"\b(ignore|disregard|override)\b.{0,50}\b(instructions|rules|guardrails|system prompt)\b",
    r"\b(reveal|show|print|repeat)\b.{0,40}\b(system prompt|hidden instructions|api key|secret)\b",
    r"\b(another|other|someone else's|different customer's)\b.{0,50}\b(order|account|purchase)\b",
    r"\b(write|generate|create)\b.{0,50}\b(code|script|program)\b",
    r"<\s*system\s*>",
    r"\bdeveloper message\b",
)
ECOMMERCE_TERMS = {
    "order", "delivery", "shipping", "shipment", "tracking", "product",
    "price", "stock", "inventory", "buy", "purchase", "return", "refund",
    "exchange", "warranty", "damaged", "cancel", "policy", "payment",
    "store", "ecommerce", "e-commerce", "customer", "item",
}


@dataclass(frozen=True)
class Validation:
    allowed: bool
    reason: str = ""


def validate_input(text: str) -> Validation:
    query = text.strip()
    if not query:
        return Validation(False, "Please enter a support question.")
    if len(query) > 2000:
        return Validation(False, "Please keep the question under 2,000 characters.")
    if any(re.search(pattern, query, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        return Validation(False, "I can help with eCommerce support, but not requests to override my instructions or reveal protected system information.")
    tokens = set(re.findall(r"[a-z0-9-]+", query.lower()))
    if not tokens.intersection(ECOMMERCE_TERMS):
        return Validation(False, "I can help with products, orders, delivery, returns, refunds, and store policies.")
    return Validation(True)


_PII_PATTERNS = (
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[EMAIL]"),
    (re.compile(r"\b(?:\+?\d[\d .()-]{7,}\d)\b"), "[PHONE]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[PAYMENT_NUMBER]"),
)


def redact_pii(value: object) -> object:
    if isinstance(value, str):
        redacted = value
        for pattern, replacement in _PII_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    if isinstance(value, dict):
        return {key: redact_pii(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_pii(item) for item in value]
    return value
