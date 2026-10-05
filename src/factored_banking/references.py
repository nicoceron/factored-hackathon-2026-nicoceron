"""Exact conversational references over validated, already authorized records.

No fuzzy record ranking or model-selected identity: intersect explicit details and
resolve only a unique record. Ordinals refer to the previously displayed order.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from factored_banking.language import detect_language, has_negation, normalize

STATUSES = {
    "completed": ("completada", "completado", "concluida", "concluido", "completed"),
    "pending": ("pendiente", "pendente", "pending"),
    "declined": ("rechazada", "rechazado", "recusada", "recusado", "declined"),
}
ORDINALS = (
    ("primera", "primero", "primer", "primeira", "primeiro"),
    ("segunda", "segundo"),
    ("tercera", "tercero", "tercer", "terceira", "terceiro"),
    ("cuarta", "cuarto", "quarta", "quarto"),
    ("quinta", "quinto"),
)
SELECTION_NOUN = (
    r"(?:opcion|opcao|operacion|operacao|transaccion|transacao|movimiento|movimento|"
    r"pago|pagamento|cargo|cobranca|compra|transferencia|debito)"
)
# Ordinary place, channel, calendar and currency words are descriptive context.
# They do not establish a merchant identity, even when unique in the scoped data.
MERCHANT_CIRCUMSTANCES = {
    "casa",
    "linea",
    "linha",
    "internet",
    "efectivo",
    "dinheiro",
    "espera",
    "proceso",
    "processo",
    "transito",
    "enero",
    "janeiro",
    "febrero",
    "fevereiro",
    "marzo",
    "marco",
    "abril",
    "mayo",
    "maio",
    "junio",
    "junho",
    "julio",
    "julho",
    "agosto",
    "septiembre",
    "setembro",
    "octubre",
    "outubro",
    "noviembre",
    "novembro",
    "diciembre",
    "dezembro",
    "dolares",
    "dolar",
    "pesos",
    "reales",
    "reais",
    "euros",
}
NON_MERCHANT_WORDS = MERCHANT_CIRCUMSTANCES | {
    "mi",
    "mis",
    "meu",
    "minha",
    "la",
    "el",
    "o",
    "a",
    "ayer",
    "ontem",
    "hoy",
    "hoje",
    "tu",
    "su",
    "sua",
    "conta",
    "cuenta",
    "registro",
    "revision",
    "analise",
    "espanol",
    "portugues",
    "castellano",
}
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
    # A leading accepted choice may also contain meaningful report details.
    choice_reply: bool = False


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


def selection_matches(text, choice):
    """Recognize affirmative choice clauses, with courtesy and optional added detail.

    The same wrappers apply to word ordinals and displayed option numbers.
    Complete replies are selection-only; a choice followed by another clause
    identifies the record while leaving that substantive text in the report.
    """
    wrapped = r"(?:(?:si|sim)(?:,\s*|\s+))?" + choice
    wrapped += r"(?:(?:,\s*|\s+)por favor)?"
    full = re.fullmatch(wrapped + r"[.!? ]*", text.strip("¿¡ "))
    spans = [(0, len(text))] if full else []
    rejected = []
    negative = r"(?:no|nao|nunca|jamas|jamais) "
    ending = r"(?:[.!? ]*$|\s*[,.;](?=\s|$))"
    # Decimal punctuation belongs to the amount, never to a new choice clause.
    boundaries = [0] + [match.end() for match in re.finditer(r";|(?<!\d)[.,]|[.,](?!\d)", text)]
    for boundary in boundaries:
        start = boundary + re.match(r"\s*", text[boundary:]).end()
        match = re.match(wrapped + ending, text[start:])
        if match and not full:
            spans.append((start, start + match.end()))
        denial = re.match(negative + wrapped + ending, text[start:])
        if denial and has_negation(denial[0], detect_language(text)):
            rejected.append((start, start + denial.end()))
    return spans, bool(full), rejected


def ordinal_reference(text):
    """An ordinal selects a listed option only in affirmative selection grammar.

    Calendar, duration and first-time statements do not have this structure.
    Multiple named options remain multiple candidates rather than a ranked guess.
    """
    ordinal = "(?:" + "|".join(label for labels in ORDINALS for label in labels) + ")"
    article = r"(?:la|el|a|o|esa|ese|essa|esse|esta|este)"
    selection_verb = r"(?:elijo|escolho|prefiero|prefiro|selecciono|seleciono|quiero|quero)"

    def clause(post_noun):
        return (
            r"(?:"
            + article
            + r" )?(?:"
            + ordinal
            + r"(?: "
            + SELECTION_NOUN
            + r")?|"
            + post_noun
            + r" "
            + ordinal
            + r")"
        )

    choice_clause = clause(r"(?:opcion|opcao)")
    explicit_clause = clause(SELECTION_NOUN)

    def choices(pattern):
        return pattern + r"(?: (?:o|ou|y|e) " + pattern + r")*"

    spans, selection_only, rejected_spans = selection_matches(
        text,
        r"(?:(?:(?:es|e|fue|foi) )?"
        + choices(choice_clause)
        + r"|"
        + selection_verb
        + r" "
        + choices(explicit_clause)
        + r")",
    )
    # Post-noun ordinals can describe timing ("fiz a compra segunda",
    # "o pagamento primeiro"). They need an explicit choice noun or verb;
    # otherwise only a pre-noun qualifier selects a transaction.
    phrases = list(
        re.finditer(
            r"(?<![\w-])(?:"
            + ordinal
            + r" "
            + SELECTION_NOUN
            + r"|"
            + r"(?:opcion|opcao)"
            + r" "
            + ordinal
            + r"|"
            + selection_verb
            + r" (?:"
            + article
            + r" )?"
            + SELECTION_NOUN
            + r" "
            + ordinal
            + r")(?![\w-])",
            text,
        )
    )

    def rejected(start):
        prefix = re.search(
            r"\b(?:no|nao|nunca|jamas|jamais) (?:(?:es|e|fue|foi|era|sera|quiero|quero|"
            r"elijo|escolho|prefiero|prefiro|selecciono|seleciono) )?"
            r"(?:(?:la|el|a|o|esta|este|esa|ese|essa|esse) )?$",
            text[:start],
        )
        # Reuse the per-turn language contract: Portuguese "no" is a
        # preposition, while Spanish "no" rejects the selection.
        return bool(prefix and has_negation(prefix[0], detect_language(text)))

    # "Un segundo cargo" describes another charge, not the second listed one.
    phrases = [
        match
        for match in phrases
        if not re.search(r"\b(?:un|una|um|uma)\s+$", text[: match.start()])
    ]
    rejected_phrases = [match for match in phrases if rejected(match.start())]
    phrases = [match for match in phrases if not rejected(match.start())]
    rejected_spans += [(start, end) for start, end in spans if rejected(start)]
    spans = [(start, end) for start, end in spans if not rejected(start)]
    selected_text = " ".join([text[start:end] for start, end in spans] + [m[0] for m in phrases])
    rejected_text = " ".join(
        [text[start:end] for start, end in rejected_spans] + [m[0] for m in rejected_phrases]
    )
    indices = [
        index
        for index, labels in enumerate(ORDINALS)
        if any(re.search(r"\b" + label + r"\b", selected_text) for label in labels)
    ]
    excluded = [
        index
        for index, labels in enumerate(ORDINALS)
        if any(re.search(r"\b" + label + r"\b", rejected_text) for label in labels)
    ]
    return indices, selection_only and not excluded, excluded, any(start == 0 for start, _ in spans)


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
            and token not in MERCHANT_CIRCUMSTANCES
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
        r"\b(?:(?:cargo|cobro|pago|cobranca|pagamento|compra) (?:de|da|do|en|em) |"
        r"(?:en|em|na|no) (?:(?:la|el|a|o) )?(?:tienda|loja|comercio|estabelecimento) )"
        r"(?!(?:" + "|".join(sorted(NON_MERCHANT_WORDS)) + r")\b)[a-z][a-z0-9-]*",
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
    previous = context.get("transaction_candidates", [])
    number_spans, number_only, rejected_numbers = selection_matches(
        text,
        r"(?:(?:es|e|fue|foi|elijo|escolho|prefiero|prefiro|selecciono|seleciono|"
        r"quiero|quero) )?(?:(?:la|a|el|o) )?"
        r"(?:(?:opcion|opcao|numero) )?[1-9]\d?(?![\w]|[.,]\d)",
    )
    # Keep offsets stable so accepted option-number spans cannot become amounts.
    numeric_text = re.sub(
        r"\b(?:tx-[a-z]{2}-\d+|case-[a-z0-9]+|\d{4}-\d{2}-\d{2})\b",
        lambda match: " " * len(match[0]),
        text,
    )
    for row in records:
        numeric_text = re.sub(
            r"(?<!\w)" + re.escape(normalize(row["id"])) + r"(?!\w)",
            lambda match: " " * len(match[0]),
            numeric_text,
        )
    amounts = []
    # Numbers embedded in time references or option labels do not denote amounts.
    for match in re.finditer(r"(?<![\w-])\d+(?:[.,]\d+)*(?![\w-])", numeric_text):
        if previous and any(
            start <= match.start() < end for start, end in number_spans + rejected_numbers
        ):
            continue
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
    ordinals, ordinal_only, excluded, leading_ordinal = ordinal_reference(text)
    for index in ordinals:
        reference_words.update(ORDINALS[index])
    if number_spans and previous:
        ordinals += [
            int(match[0]) - 1
            for start, end in number_spans
            for match in re.finditer(r"\b[1-9]\d?\b", text[start:end])
        ]
        ordinal_only = ordinal_only or number_only
    if rejected_numbers and previous:
        excluded += [
            int(match[0]) - 1
            for start, end in rejected_numbers
            for match in re.finditer(r"\b[1-9]\d?\b", text[start:end])
        ]
    retracted = bool(set(ordinals) & set(excluded))
    ordinals = [index for index in ordinals if index not in excluded]
    if retracted:
        ordinal_only = False
        if not ordinals:
            mentioned = True
            candidates = []
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
    choice_reply = bool(
        previous and ordinals and (leading_ordinal or any(start == 0 for start, _ in number_spans))
    )
    return Reference(
        candidates, mentioned, mentioned and (ordinal_only or not remaining), choice_reply
    )
