"""Local bilingual learned intent classification, never an authorization decision.

The release artifact is JSON, not executable pickle. Fitted attributes use the
public sklearn estimator API. Training and all evaluation live in evaluation.py.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files
from typing import Literal

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

INTENTS = (
    "transaction_status",
    "dispute",
    "scam",
    "human",
    "case_status",
    "ambiguous",
    "unsupported",
)
MAX_MESSAGE_LENGTH = 2000


def detect_language(message: str, fallback: str = "es") -> str:
    """Choose ES/PT from clear cues; short/shared replies keep the conversation language.

    This conservative lexical routing is separate from the learned intent model.
    It makes no language-confidence claim and never changes identity or permissions.
    """
    fallback = fallback if fallback in {"es", "pt"} else "es"
    text = normalize(message)
    explicit = re.search(
        r"(?:responde|responda|responder|habla|fale|continua|continue|prefiero|prefiro|"
        r"cambia|mude|escribe|escreva|em|en)\s+(?:en\s+|em\s+)?"
        r"(portugues|espanol|castellano)\b",
        text,
    )
    if explicit:
        return "pt" if explicit[1] == "portugues" else "es"
    cues = {
        "es": {
            "hola",
            "quiero",
            "necesito",
            "reconozco",
            "autorice",
            "cargo",
            "cargos",
            "cobro",
            "pago",
            "pagos",
            "transaccion",
            "operacion",
            "asesor",
            "persona",
            "estafa",
            "contrasena",
            "rechazada",
            "pendiente",
            "gracias",
            "puedes",
            "puedo",
            "tengo",
            "cual",
            "donde",
            "cuando",
            "salio",
            "ya",
            "hablar",
            "espanol",
            "mi",
            "mis",
            "ayuda",
            "dime",
            "tambien",
            "movimiento",
            "despues",
            "llamada",
            "ninguna",
            "ninguno",
        },
        "pt": {
            "ola",
            "quero",
            "preciso",
            "reconheco",
            "autorizei",
            "cobranca",
            "cobrancas",
            "pagamento",
            "pagamentos",
            "transacao",
            "operacao",
            "atendente",
            "pessoa",
            "golpe",
            "senha",
            "recusada",
            "pendente",
            "obrigado",
            "obrigada",
            "voce",
            "posso",
            "tenho",
            "qual",
            "onde",
            "saiu",
            "ja",
            "falar",
            "nao",
            "portugues",
            "meu",
            "meus",
            "minha",
            "minhas",
            "seu",
            "sua",
            "suas",
            "ajuda",
            "lancamento",
            "tambem",
            "oi",
            "bom",
            "boa",
            "movimento",
            "depois",
            "nenhuma",
        },
    }
    words = set(re.findall(r"[a-z]+", text))
    scores = {locale: len(words & tokens) for locale, tokens in cues.items()}
    if scores["es"] == scores["pt"]:
        return fallback
    return max(scores, key=scores.get)


def normalize(message: str) -> str:
    """Unicode normalization for rules and duplicate detection, retaining negations."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", message.casefold()) if not unicodedata.combining(c)
    )


def has_negation(message: str, language: str | None = None) -> bool:
    """Grammatical negators, separate from inferred intent and predicate polarity.

    Portuguese ``no`` contracts ``em o`` and does not negate a clause. A supplied
    conversation locale is the fallback, as in per-turn language routing. Clear
    message cues take precedence when the speaker switches languages.
    """
    language = detect_language(message, language if language in {"es", "pt"} else "es")
    negators = r"nao|nunca|jamas|jamais|nem|ni" + (r"|no" if language == "es" else "")
    return bool(re.search(rf"\b(?:{negators})\b", normalize(message)))


def authorization_polarity(message: str) -> Literal["affirmed", "negated"] | None:
    """Recognize bounded first-person transaction reports, never tool authorization.

    Negators may precede an object/subject pronoun, as in ``no lo reconozco``
    or ``nao a reconheco``. First-person perfect auxiliaries and explicit
    self-identification clauses use the same prefix, such as ``no he autorizado``
    and ``nao fui eu quem autorizou``. Negation elsewhere does not deny this
    predicate. Any denied occurrence keeps a mixed report eligible for review.
    """
    text = normalize(message)
    objects = r"(?:lo|la|los|las|o|a|os|as|me|nos)"
    predicates = re.finditer(
        r"\b(?:reconozco|reconocemos|reconheco|reconhecemos|autorice|autorizei|"
        r"autorizamos|realice|realizei|realizamos|hice|hicimos|fiz|fizemos|"
        r"(?:he|hemos|habia|habiamos)\s+(?:autorizado|realizado|hecho|reconocido)|"
        r"(?:tenho|temos|tinha|tinhamos)\s+(?:autorizado|realizado|feito|reconhecido)|"
        rf"(?:fui|fuimos|soy|somos)\s+(?:yo|nosotros|nosotras)\s+(?:quien|quienes)\s+"
        rf"(?:{objects}\s+)?(?:autorizo|autorizamos|realizo|realizamos|hizo|hicimos|"
        r"reconocio|reconocimos)|"
        rf"(?:fui|fomos|sou|somos)\s+(?:eu|nos)\s+(?:quem|que)\s+(?:{objects}\s+)?"
        r"(?:autorizou|autorizamos|realizou|realizamos|fez|fizemos|reconheceu|reconhecemos))\b",
        text,
    )
    found = False
    for predicate in predicates:
        found = True
        if re.search(
            r"\b(?:no|nao|nunca|jamas|jamais)\s+"
            r"(?:(?:lo|la|los|las|o|a|os|as|me|yo|eu|nosotros|nosotras|nos)\s+){0,2}$",
            text[: predicate.start()],
        ):
            return "negated"
    return "affirmed" if found else None


def safety_signals(message: str) -> list[str]:
    """Advisory lexical flags. These do not override the learned label or authorize tools."""
    text = normalize(message)
    signals: list[str] = []
    if has_negation(message):
        signals.append("negation_present")
    if re.search(
        r"(?:ignora|ignore).{0,40}(?:instru|regra)|(?:revela|revele).{0,40}"
        r"(?:prompt|clave|chave)|(?:borra|apague).{0,30}auditoria",
        text,
    ):
        signals.append("possible_prompt_injection")
    # Match narrow affirmative requests. A nearby explicit negation suppresses the flag.
    if re.search(
        r"(?:quiero|quero|necesito|preciso|prefiero|prefiro).{0,30}"
        r"(?:persona|pessoa|humano|humana|agente|asesor|atendente|supervisor|representante)",
        text,
    ) and not re.search(r"\b(?:no|nao) (?:quiero|quero|necesito|preciso|prefiero|prefiro)", text):
        signals.append("explicit_human_request")
    if authorization_polarity(message) == "negated" or re.search(
        r"sin (?:mi )?(?:permiso|consentimiento)|sem (?:meu )?(?:consentimento|permissao)",
        text,
    ):
        signals.append("customer_reported_dispute")
    if re.search(
        r"(?:me|fui) (?:engan|estaf)|(?:comparti|compartilhei).{0,40}(?:codigo|senha)"
        r"|(?:piden|pediram|quieren|querem|exigiendo|exigindo).{0,30}"
        r"(?:contrasena|senha|codig|pin|token)|(?:supuesto|suposto|falso).{0,30}"
        r"(?:banco|asesor|assessor|soporte|suporte)|(?:amenaz|ameac|extors|extorqu)",
        text,
    ):
        signals.append("customer_reported_scam")
    return signals


def _result(intent: str, confidence: float, version: str, signals: list[str]) -> dict:
    return {
        "intent": intent,
        "confidence": round(float(confidence), 6),
        "model_version": version,
        "signals": signals,
    }


def baseline_classify(message: str, language: str = "es") -> dict:
    """Frozen practical keyword/rule baseline; confidence is a routing constant."""
    signals = safety_signals(message)
    text = normalize(message)
    if language not in ("es", "pt") or not text.strip() or len(message) > MAX_MESSAGE_LENGTH:
        return _result("ambiguous", 0.0, "keyword-v1", signals + ["input_rejected"])
    rules = (
        ("scam", r"estafa|golpe|phishing|impostor|enganad|enganar|contrasena|senha|otp|pin\b"),
        ("dispute", r"no reconozco|nao reconheco|no autorice|nao autorizei|duplicad|reclamar"),
        ("human", r"humano|humana|persona|pessoa|asesor|atendente|supervisor|operador"),
        ("case_status", r"caso|ticket|folio|protocolo|expediente|reclamo|reclamacao|chamado"),
        ("transaction_status", r"transacci|transac|pago|pagamento|transfer|compra|cargo|cobranca"),
        ("unsupported", r"prestamo|emprestimo|clima|poema|cripto|invierte|invista|borra|apague"),
    )
    for intent, pattern in rules:
        if re.search(pattern, text):
            return _result(intent, 1.0, "keyword-v1", signals)
    return _result("ambiguous", 0.0, "keyword-v1", signals)


def _restore(artifact: dict) -> tuple[list[TfidfVectorizer], LogisticRegression]:
    """Reconstruct only known numeric fitted state, with dimensions/finite checks."""
    if artifact["schema_version"] != 1 or set(artifact["classes"]) != set(INTENTS):
        raise ValueError("Unsupported language artifact schema/classes")
    vectorizers = []
    for item in artifact["vectorizers"]:
        params = dict(item["params"])
        params["ngram_range"] = tuple(params["ngram_range"])
        vocabulary = item["vocabulary"]
        if set(vocabulary.values()) != set(range(len(vocabulary))):
            raise ValueError("Language vocabulary indices are not contiguous")
        vectorizer = TfidfVectorizer(vocabulary=vocabulary, **params)
        idf = np.asarray(item["idf"], dtype=float)
        if idf.shape != (len(vocabulary),) or not np.isfinite(idf).all():
            raise ValueError("Invalid language IDF weights")
        vectorizer.idf_ = idf
        vectorizers.append(vectorizer)
    model = LogisticRegression(**artifact["classifier_params"])
    model.classes_ = np.asarray(artifact["classes"])
    model.coef_ = np.asarray(artifact["coef"], dtype=float)
    model.intercept_ = np.asarray(artifact["intercept"], dtype=float)
    model.n_features_in_ = sum(len(v.vocabulary) for v in vectorizers)
    if (
        model.coef_.shape != (len(INTENTS), model.n_features_in_)
        or model.intercept_.shape != (len(INTENTS),)
        or not np.isfinite(model.coef_).all()
        or not np.isfinite(model.intercept_).all()
    ):
        raise ValueError("Invalid language classifier weights")
    return vectorizers, model


@lru_cache(maxsize=1)
def load_model() -> tuple[dict, list[TfidfVectorizer], LogisticRegression]:
    artifact = json.loads(
        files("factored_banking").joinpath("resources/language_model.json").read_text()
    )
    vectorizers, model = _restore(artifact)
    return artifact, vectorizers, model


def predict_with_artifact(message: str, artifact: dict, vectorizers: list, model) -> dict:
    vectors = hstack([v.transform([message]) for v in vectorizers], format="csr")
    probabilities = model.predict_proba(vectors)[0]
    ordered = np.argsort(probabilities)
    first, second = ordered[-1], ordered[-2]
    confidence = float(probabilities[first])
    intent = str(model.classes_[first])
    signals = safety_signals(message)
    if vectors.nnz == 0:
        signals.append("out_of_vocabulary")
    if confidence < artifact["threshold"]:
        signals.append("low_confidence")
    if confidence - float(probabilities[second]) < artifact["margin"]:
        signals.append("small_margin")
    if any(s in signals for s in ("out_of_vocabulary", "low_confidence", "small_margin")):
        intent = "ambiguous"
    return _result(intent, confidence, artifact["model_version"], signals)


def classify(message: str, language: str = "es") -> dict:
    """Classify Spanish/Portuguese; uncertain or unavailable inference asks clarification.

    confidence is the uncalibrated maximum logistic probability, including when
    intent is changed to ambiguous by abstention. It is not a correctness guarantee.
    """
    if language not in ("es", "pt"):
        return _result("ambiguous", 0.0, "language-input-guard-v1", ["unsupported_language"])
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
        return _result("ambiguous", 0.0, "language-input-guard-v1", ["input_rejected"])
    try:
        artifact, vectorizers, model = load_model()
    except (OSError, ValueError, KeyError, TypeError):
        # A missing/invalid release cannot silently become confident automation.
        return _result("ambiguous", 0.0, "language-unavailable-v1", ["model_unavailable"])
    return predict_with_artifact(message, artifact, vectorizers, model)
