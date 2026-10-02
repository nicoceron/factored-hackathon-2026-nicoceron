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


def normalize(message: str) -> str:
    """Unicode normalization for rules and duplicate detection, retaining negations."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", message.casefold()) if not unicodedata.combining(c)
    )


def safety_signals(message: str) -> list[str]:
    """Advisory lexical flags. These do not override the learned label or authorize tools."""
    text = normalize(message)
    signals: list[str] = []
    if re.search(r"\b(no|nao|nunca|jamas|nem|ni)\b", text):
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
    if re.search(
        r"no (?:reconozco|autorice|hice|realice)|nao (?:reconheco|autorizei|fiz|realizei)"
        r"|sin (?:mi )?(?:permiso|consentimiento)|sem (?:meu )?(?:consentimento|permissao)",
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
