"""Minimize submitted sandbox text before storage or external inference.

Pattern redaction is defense in depth, not a guarantee of anonymization. The UI
prohibits real personal data; only team fixtures are supplied by the service.
"""

import re
import unicodedata

REDACTED = "[REDACTED]"
REPORT_LIMIT = 2000


def redact_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    # Customers often disclose short numeric secrets without a colon or verb.
    # Keep the secret's label: it can explain a scam, while dates, amounts and
    # transaction/reference codes must remain available as report evidence.
    text = re.sub(
        r"(?i)(\b(?:pin|cvv|otp|token|password|contrase[ñn]a|senha|"
        r"clave de acceso|c[oó]digo de (?:acceso|acesso|seguridad|seguran[çc]a|"
        r"verificaci[oó]n|verifica[çc][aã]o|autenticaci[oó]n|autentica[çc][aã]o))"
        r"\s*(?:(?:es|[ée]|is)\s+|[:=]\s*)?)"
        r"(?:\d{3}[ -]\d{3}|\d{4}[ -]\d{4}|\d{3,8})(?!\w|[.-]\d)",
        lambda match: match[1] + REDACTED,
        text,
    )
    patterns = (
        r"\b(?:sk-|apikey_)[A-Za-z0-9_-]{12,}\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        r"https?://\S+",
        r"(?i)\b(?:c[eé]dula|documento|dni|cpf|cuenta|account|tarjeta|cart[aã]o)"
        r"\s*(?:es|[ée]|is|:|=|n[uú]mero)?\s*\d[\d .-]{5,}\d",
        r"(?i)\b(?:password|contrase[ñn]a|senha|pin|cvv|otp|token|"
        r"c[oó]digo(?: de (?:acceso|acesso|seguridad|seguran[çc]a|verificaci[oó]n|"
        r"verifica[çc][aã]o|autenticaci[oó]n|autentica[çc][aã]o))?)"
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


def customer_report(
    message: str, context: dict, *, continuation: bool, selection_only: bool = False
) -> str:
    """Retain allegations and added facts through a bounded, redacted continuation."""
    current = redact_text(message)[:REPORT_LIMIT]
    previous = context.get("customer_report", "") if continuation else ""
    if not isinstance(previous, str):
        previous = ""
    previous = redact_text(previous)[:REPORT_LIMIT]
    if not previous:
        return current
    if selection_only or not current or current.casefold() in previous.casefold():
        return previous
    combined = previous + "\n" + current
    if len(combined) <= REPORT_LIMIT:
        return combined
    # Retain the beginning of the original report and the latest details even
    # when the bounded report is full; do not store unbounded chat transcripts.
    previous_budget = max(REPORT_LIMIT - len(current) - 1, REPORT_LIMIT // 2)
    return previous[:previous_budget] + "\n" + current[: REPORT_LIMIT - previous_budget - 1]
