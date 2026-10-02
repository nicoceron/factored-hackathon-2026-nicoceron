"""Minimize submitted sandbox text before storage or external inference.

Pattern redaction is defense in depth, not a guarantee of anonymization. The UI
prohibits real personal data; only team fixtures are supplied by the service.
"""

import re
import unicodedata

REDACTED = "[REDACTED]"


def redact_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    patterns = (
        r"\b(?:sk-|apikey_)[A-Za-z0-9_-]{12,}\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        r"https?://\S+",
        r"(?i)\b(?:c[eé]dula|documento|dni|cpf|cuenta|account|tarjeta|cart[aã]o)"
        r"\s*(?:es|[ée]|is|:|=|n[uú]mero)?\s*\d[\d .-]{5,}\d",
        r"(?i)\b(?:password|contrase[ñn]a|senha|pin|cvv|otp|token|"
        r"c[oó]digo(?: de (?:acceso|acesso|seguridad|seguran[çc]a|verificaci[oó]n))?)"
        r"\s*(?:es|[ée]|is|:|=)\s*[\w!@#$%^&*.-]{3,}",
    )
    for pattern in patterns:
        text = re.sub(pattern, REDACTED, text)
    # Preserve ISO dates: timing is material to a customer's report. A broad
    # phone/card expression otherwise mistakes dates for identifiers.
    text = re.sub(
        r"\b\d{4}-\d{2}-\d{2}\b|(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)",
        lambda match: (
            match[0]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", match[0])
            or sum(c.isdigit() for c in match[0]) < 10
            else REDACTED
        ),
        text,
    )
    return text.strip()


def customer_report(message: str, context: dict, *, continuation: bool) -> str:
    """Retain the reported problem through selection; never turn it into a bank fact."""
    current = redact_text(message)[:2000]
    previous = context.get("customer_report", "") if continuation else ""
    if not isinstance(previous, str):
        previous = ""
    previous = redact_text(previous)[:2000]
    return previous or current
