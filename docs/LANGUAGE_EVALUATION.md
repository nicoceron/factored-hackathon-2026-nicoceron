# Bilingual intent evaluation

The deployed default is a local **word + character TF-IDF logistic classifier**, trained offline and released as JSON numeric weights. It is a learned text classifier, not a foundation model or a claim of state-of-the-art accuracy. A pretrained **Gemma 3 4B** challenger was also evaluated locally. Jev was not called because a free entitlement was not established and this implementation has a zero-paid-service constraint.

## Frozen workload and provenance

The versioned resources contain **196 training cases, 56 development cases, and 140 held-out cases**. Each split is balanced between Spanish and Portuguese and across seven intents: transaction status, dispute, scam, human assistance, existing case status, ambiguity, and unsupported requests. The test set has 70 cases per language and 20 per intent.

These are **team-authored synthetic scenarios produced with coding-assistant help**. They are not organizer records, real customer messages, independently human-reviewed labels, or native-Portuguese-reviewed translations. The label is the author's intended behavior under the published taxonomy. This is a developer-authored challenge holdout, not an externally blind evaluation. The planned independent review remains an explicit limitation.

Each Spanish/Portuguese pair shares a semantic group and stays in one split. Corpus validation checks frozen SHA-256 hashes, exact normalized duplicates, labels, language balance, and group isolation. Scenario wording and motifs were authored separately across splits; top-level intent semantics necessarily overlap. Group IDs and duplicate checks cannot prove the absence of all paraphrase similarity. The official organizer corpus has not been relabeled or attached to these cases.

Training fits vocabulary, IDF weights and coefficients using **training rows only**. Regularization `C ∈ {1,4,8,16}`, abstention thresholds `{0.25,0.35,0.45}`, and margins `{0,.05,.10}` were selected on development macro-F1. Ties use the first candidate in that order. The selected settings are `C=4`, threshold `0.25`, margin `0`, and development macro-F1 `0.7966`. Final test predictions were generated after selection. The model was not changed after inspecting the reported failures. Future model improvements require a new untouched evaluation set; this set can remain a regression suite.

## Measured comparison

One sequential run on the development Mac, Python 3.12 and the locked scikit-learn version. Both trained default and rules received identical test text. Gemma used the identical cases, a frozen schema-constrained prompt, temperature zero, seed 2026, and the already installed model. All reported API spend is zero; local electricity, hardware and hosting costs were not measured.

| System | Exact labels correct | Macro-F1 | ES macro-F1 / n=70 | PT macro-F1 / n=70 | Warm p50 / p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Keyword rules v1 | 65/140 | 0.4207 | 0.4481 | 0.3890 | 0.013 / 0.021 ms |
| TF-IDF + logistic v1 | 117/140 | **0.8230** | 0.8005 | 0.8456 | 0.390 / 0.575 ms |
| Local Gemma 3 4B | 115/140 | 0.8045 | 0.8130 | 0.7962 | 640.7 / 752.5 ms |

The practical keyword baseline is intentionally simple and its patterns are public; improvement over this baseline does not establish superiority over a tuned commercial service. The paired semantic-group bootstrap 95% interval for learned-minus-rules macro-F1 is **[0.2732, 0.5293]**, 1,000 draws, seed 2026. Translation pairs are resampled together. This interval only describes variation among these authored scenarios, not label bias or real customer demand. The learned/Gemma difference is small and is not presented as statistically significant.

The Gemma run used digest `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`, 37,198 prompt tokens and 1,133 output tokens. It made no cloud calls and incurred no model API charge. Its first warmup request took 5.26 seconds. There was one run; hardware-dependent variation and stochastic variability were not estimated. Gemma is a research challenger, not a dependency of the public CPU deployment. The default is chosen for CPU portability, bounded latency, absence of external service calls, and the measured baseline improvement—not because modern foundation models are generally inferior.

Latency measures the classification component, including the Python function and local Gemma loopback transport where applicable, excluding session/authentication, banking tools, network delivery to a user, and confirmation turns. The TF-IDF model is loaded before the benchmark's warmup; its model-deserialization time is not included. No concurrency/capacity claim follows from these values. See the separate system benchmark for HTTP/workflow results.

## Safety behavior and failure analysis

The default routed all **40/40 authored scam/dispute reports** to a human-required intent, but it made **23 exact-label errors** and **11 unnecessary human-intent predictions**. Two overlapping scam+dispute cases became dispute, losing scam priority. Several unsupported refund, debt, loan, or third-party-address requests were incorrectly classified as dispute or transaction status. Negated human requests and affirmative recognition also caused false escalation. Short ambiguous messages sometimes became specific intents. These errors are why record ownership, allowed actions, explicit confirmation, and read-back verification must remain deterministic service responsibilities.

The classifier's `confidence` is the **uncalibrated maximum logistic probability**, not a proven probability of correctness. It remains the raw maximum even when threshold abstention changes the returned intent to `ambiguous`. Inputs over 2,000 characters, blank/non-string inputs, unsupported language settings, unknown vocabulary, missing/corrupt model artifacts, or probabilities below the development-selected threshold fail to clarification. A classifier output never establishes fraud, authorizes an action, chooses a customer identity, or proves a tool succeeded.

Lexical `signals` are returned separately from the learned label. They are narrow advisory flags for negation, possible injection, explicit human requests, and customer allegations. They are not exhaustive semantic detectors and do not silently override model scores. The service may conservatively use them, but the system benchmark must then evaluate that combined behavior separately.

Raw per-case messages are synthetic and public in the corpus. The aggregate report contains only expected/predicted labels and case IDs, not organizer records. Its per-intent metrics, confusion matrices, failures, language slices, model digest, usage and timing are in [the reproducible evidence](evidence/language-evaluation.json). The resources directory also contains the corpus manifest, release weights, and full development selection results.

## Reproduce and integrate

```bash
uv run --locked python -m factored_banking.evaluation --train
uv run --locked python -m factored_banking.evaluation --output artifacts/language-evaluation.json
# Optional, only with the existing local gemma3:4b model and Ollama running:
uv run --locked python -m factored_banking.evaluation --gemma --output artifacts/language-gemma.json
uv run --locked pytest -q tests/test_language.py
```

Training is an explicit offline command. Runtime caches the JSON artifact and uses the standard scikit-learn transform/predict APIs; no executable pickle, arbitrary model loader, runtime fit, cloud request, or model download is used. The benchmark accesses Ollama only at `127.0.0.1:11434` with the fixed installed local model name. The `--gemma` option does not pull a model.

```python
from factored_banking.language import classify

result = classify("Não reconheço essa cobrança.", language="pt")
# {"intent": "dispute", "confidence": ..., "model_version": ..., "signals": [...]}
```

The 24 component tests verify bilingual demo paths, negation examples, rejection/abstention, model failure, numeric artifact validation, immutable corpus hashes and split isolation. They are engineering regression checks, not additional independently labeled evaluation data.

## Official implementation references reviewed

- [scikit-learn text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction): fitted TF-IDF and n-gram features.
- [scikit-learn logistic regression](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression): learned class probabilities and regularization.
- [scikit-learn leakage pitfalls](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage): fit preprocessing only on training data.
- [Ollama chat API](https://docs.ollama.com/api/chat) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs): local schema-constrained inference, timing and token usage.
- [Gemma 3 model card](https://ai.google.dev/gemma/docs/core/model_card_3): model capabilities and limitations; provider claims are not substituted for this benchmark.
