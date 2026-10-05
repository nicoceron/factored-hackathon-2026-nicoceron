"""Exact conversational references over validated, already authorized records.

No fuzzy record ranking or model-selected identity: intersect explicit details and
resolve only a unique record. Ordinals refer to the previously displayed order.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from factored_banking.language import normalize

STATUSES = {
    "completed": ("completada", "completado", "concluida", "concluido", "completed"),
    "pending": ("pendiente", "pendente", "pending"),
    "declined": ("rechazada", "rechazado", "recusada", "recusado", "declined"),
}
ORDINALS = (
    ("primera", "primero", "primeira", "primeiro"),
    ("segunda", "segundo"),
    ("tercera", "tercero", "terceira", "terceiro"),
    ("cuarta", "cuarto", "quarta", "quarto"),
    ("quinta", "quinto"),
)
MERCHANT_DESCRIPTORS = {
    "demo",
    "tienda",
    "mercado",
    "comercio",
    "estabelecimento",
    "loja",
    "supermercado",
    "cafe",
    "restaurante",
    "hotel",
    "farmacia",
    "app",
    "purchase",
    "compra",
    "pago",
}


@dataclass(frozen=True)
class Reference:
    candidates: list[dict]
    mentioned: bool = False
    selection_only: bool = False


def amount_values(value):
    """Accept decimal or grouped notation without binary float rounding."""
    forms = {value.replace(" ", "")}
    plain = value.replace(" ", "")
    if "," in plain and "." in plain:
        decimal_mark = "," if plain.rfind(",") > plain.rfind(".") else "."
        forms.add(plain.replace("." if decimal_mark == "," else ",", "").replace(",", "."))
    elif "," in plain or "." in plain:
        mark = "," if "," in plain else "."
        forms.add(plain.replace(",", "."))
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", plain):
            forms.add(plain.replace(mark, ""))
    values = set()
    for form in forms:
        try:
            number = Decimal(form)
        except InvalidOperation:
            continue
        if number.is_finite() and number >= 0:
            values.add(number)
    return values


def resolve_reference(message, context, records):
    text = normalize(message)
    candidates = list(records)
    mentioned = False
    reference_words = set()
    # Match complete merchant phrases or distinctive words among authorized merchants.
    merchant_tokens = {
        row["id"]: set(re.findall(r"[a-z0-9]+", normalize(row.get("merchant") or "")))
        for row in records
    }
    words = set(re.findall(r"[a-z0-9]+", text))
    merchants = []
    for row in records:
        phrase = normalize(row.get("merchant") or "")
        tokens = merchant_tokens[row["id"]]
        distinctive = {
            token
            for token in tokens
            if len(token) >= 3
            and token not in MERCHANT_DESCRIPTORS
            and sum(token in other for other in merchant_tokens.values()) == 1
        }
        if (phrase and re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text)) or (
            distinctive & words
        ):
            merchants.append(row["id"])
            reference_words.update(tokens)
    if merchants:
        mentioned = True
        candidates = [row for row in candidates if row["id"] in merchants]
    elif re.search(
        r"\b(?:(?:en|em) |(?:cargo|pago|cobranca|pagamento|compra) (?:de|da|do) )"
        r"(?!mi\b|mis\b|meu\b|minha\b|la\b|el\b|o\b|a\b|ayer\b|ontem\b|hoy\b|hoje\b|"
        r"tu\b|su\b|sua\b|conta\b|cuenta\b|revision\b|analise\b|"
        r"espanol\b|portugues\b|castellano\b)[a-z]{3,}",
        text,
    ):
        # An explicitly named unknown establishment cannot reuse the previous record.
        mentioned = True
        candidates = []
    currencies = set(re.findall(r"\b(?:mxn|cop|ars|usd)\b", text))
    if currencies:
        mentioned = True
        reference_words.update(currencies)
        candidates = [row for row in candidates if row["currency"].lower() in currencies]
    statuses = set()
    raw_statuses = {
        status
        for status, labels in STATUSES.items()
        if any(re.search(r"\b" + label + r"\b", text) for label in labels)
    }
    for status, labels in STATUSES.items():
        for label in labels:
            # A status identifies a record only as an affirmative noun qualifier
            # or a short selection reply. A predicate asks whether the unknown
            # payment has that status; using it as evidence would assume the answer.
            phrase = re.search(
                r"\b(?:el|la|los|las|del|un|una|mi|mis|o|a|os|as|do|da|um|uma|meu|minha|"
                r"este|esta|ese|esa|esse|essa|aquele|aquela) "
                r"(?:cargo|cobranca|pago|pagamento|operacion|operacao|transaccion|transacao|"
                r"transferencia|compra|debito|movimiento|movimento) " + label + r"\b",
                text,
            )
            short = re.fullmatch(
                r"(?:(?:el|la|o|a|ese|esa|esse|essa) )?"
                r"(?:(?:cargo|cobranca|pago|pagamento|operacion|operacao|transaccion|transacao|"
                r"transferencia|compra|debito|movimiento|movimento) )?"
                + label
                + r"(?: por favor)?[.! ]*",
                text,
            )
            locator = bool(
                phrase
                or (
                    short
                    and (
                        context.get("transaction_candidates")
                        or re.match(
                            r"(?:el|la|o|a|ese|esa|esse|essa) ",
                            text,
                        )
                    )
                )
            )
            if locator and (
                not phrase or not re.search(r"\b(?:no|nao)\s*$", text[: phrase.start()])
            ):
                statuses.add(status)
                reference_words.add(label)
    if statuses and len(raw_statuses) == 1:
        mentioned = True
        candidates = [row for row in candidates if row["status"] in statuses]
    dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text))
    if dates:
        mentioned = True
        candidates = [row for row in candidates if row.get("date") in dates]
    numeric_text = re.sub(r"\b(?:tx-[a-z]{2}-\d+|case-[a-z0-9]+|\d{4}-\d{2}-\d{2})\b", "", text)
    for row in records:
        numeric_text = re.sub(
            r"(?<!\w)" + re.escape(normalize(row["id"])) + r"(?!\w)", "", numeric_text
        )
    amounts = []
    # Numbers embedded in time references or option labels do not denote amounts.
    for match in re.finditer(r"(?<![\w-])\d+(?:[.,]\d+)*(?![\w-])", numeric_text):
        after = numeric_text[match.end() :]
        before = numeric_text[: match.start()]
        if re.match(r"\s*(?:dias?|horas?|veces|vezes|meses|anos?)\b", after) or re.search(
            r"\b(?:opcion|opcao|numero|nro)\s*$", before
        ):
            continue
        values = amount_values(match[0])
        if re.match(r"\s*mil\b", after):
            values = {number * 1000 for number in values}
            reference_words.add("mil")
        amounts.append(values)
    if amounts:
        mentioned = True
        candidates = [
            row for row in candidates if any(Decimal(row["amount"]) in values for values in amounts)
        ]
    previous = context.get("transaction_candidates", [])
    ordinals = []
    for index, labels in enumerate(ORDINALS):
        if any(re.search(r"\b" + label + r"\b", text) for label in labels):
            ordinals.append(index)
            reference_words.update(labels)
    option_number = re.fullmatch(
        r"(?:(?:la|a|el|o) )?(?:(?:opcion|opcao|numero) )?([1-9]\d?)[.!? ]*", text
    )
    if option_number and previous:
        ordinals = [int(option_number[1]) - 1]
        # An option number is an ordinal, not a monetary amount.
        candidates = list(records)
    if ordinals and previous:
        mentioned = True
        identifiers = {previous[index] for index in ordinals if index < len(previous)}
        candidates = [row for row in candidates if row["id"] in identifiers]
    selection_words = {
        "la",
        "el",
        "las",
        "los",
        "a",
        "o",
        "as",
        "os",
        "de",
        "del",
        "da",
        "do",
        "en",
        "em",
        "esa",
        "ese",
        "essa",
        "esse",
        "esta",
        "este",
        "aquella",
        "aquele",
        "aquela",
        "operacion",
        "operacao",
        "transaccion",
        "transacao",
        "movimiento",
        "movimento",
        "pago",
        "pagamento",
        "cargo",
        "cobranca",
        "por",
        "favor",
        "opcion",
        "opcao",
        "numero",
    }
    remaining = set(re.findall(r"[a-z]+", text)) - reference_words - selection_words
    return Reference(candidates, mentioned, mentioned and not remaining)
