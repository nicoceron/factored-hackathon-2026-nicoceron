# Fraud model evaluation and release decision

**No learned fraud detector was promoted.** Logistic regression and CatBoost were trained on organizer records and compared with a constant population prior and an amount-history rule. Neither learned candidate passed the development promotion gate. The released runtime artifact reports the historical population baseline explicitly; it cannot distinguish fraud, dismiss a customer's allegation, or authorize an action.

This negative result is a technical decision supported by measurement. It does not prove that no future model could learn useful signal. It avoids turning an unexplained supplied-score shortcut or a small fluctuation above chance into a claim of fraud detection.

The complete aggregate receipt is [ml-evaluation.json](evidence/ml-evaluation.json), including probabilities, calibration deciles, capacity metrics, confidence intervals, slices, hashes, library versions and exact hyperparameters. The [serving-data report](DATA_PIPELINE.md) describes the source contracts. All candidate artifacts and row-level features remain local.

## Experiment design

The task is retrospective support triage after the transaction becomes available in a conservative replay. It is not a pre-authorization detector. The availability clock is `max(event timestamp, process date + 1 day)` because process dates lack time-of-day. Prior history ends strictly before this timestamp. Transactions at the same availability time cannot see one another. The absence of source timezones and adjudication timestamps remains an explicit limitation.

| Partition | Availability period | Population rows | Fraud labels |
| --- | --- | ---: | ---: |
| Train | Before January 1, 2026 | 3,735,596 | 3,712 |
| Calibration | January 2026 | 123,215 | 109 |
| Candidate selection | February 2026 | 114,374 | 86 |
| Final test | March through the June snapshot | 451,823 | 409 |

The final test prevalence is **0.090522%**. These counts differ from the earlier event-time feasibility counts because they use the availability clock. Earlier full-snapshot audits examined aggregate distributions and the supplied-score shortcut; this is an out-of-time holdout, **not an externally blinded benchmark**. No final-test labels enter training, calibration, candidate selection or hyperparameter tuning. The script fixes the development decision before scoring the final test.

Training retains every positive and a reproducible one-eighth sample of negatives based on a transaction-ID hash: **471,012 fitted rows**, including all 3,712 positives. Negative examples receive weight 8 to restore population weighting. Hashes and IDs are never predictor inputs. Calibration, selection and test retain their full natural prevalence; there is no balanced test set or synthetic oversampling. Label availability at training time is assumed, because the organizer schema does not contain adjudication timestamps.

Features are log amount, event hour and ISO weekday, log count in the customer's strict-prior 30-day same-currency history, log amount/prior-mean ratio, currency, transaction type/category, channel and transaction country. Current customer/product snapshots, gender, customer IDs, transaction IDs, response/status fields, the target, supplied fraud score, amount-USD conversion, unrelated transcripts and unlinked digital sessions are excluded. Categories are fit on training only. Customer country/gender snapshots appear only in post hoc aggregate slices, not model inputs.

## Candidates and selection

- **Constant:** full training-population prevalence, 0.099368%.
- **Amount-history rule:** a fixed anomaly flag when amount exceeds three times the prior same-currency mean; its heuristic score is not a calibrated probability.
- **Logistic regression:** train-fitted scaling and one-hot categories, unknown-category handling, L2 regularization, natural-population weights.
- **CatBoost:** 180 CPU boosting iterations, depth 5, learning rate 0.05, L2 leaf regularization 8, seed 20261002, four threads, no paid service.

Each learned candidate receives a sigmoid calibrator fitted on January only. February selects a candidate only if its average precision exceeds 1.2 times the constant baseline **and** the 95% Wilson lower bound of precision at 1% review capacity exceeds February prevalence. No candidate passed. Hyperparameters were fixed for this bounded comparison; no broad optimization or tabular foundation-model experiment is claimed.

CatBoost provides a capable nonlinear tabular challenger. Adding graph models, language-derived transaction features or heavier foundation models without validated relationships and labels would not establish stronger evidence. The customer-service language component is evaluated separately; transaction risk and customer allegations have different meanings.

## Final test results

Average precision is the scikit-learn non-interpolated precision-recall summary (AP), not trapezoidal PR area. Accuracy is deliberately omitted because an always-negative classifier would exceed 99.9%.

| Candidate | AP | ROC AUC | Brier score | True positives / 4,519 reviewed | Precision at 1% | Recall at 1% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant | 0.0009052 | 0.5000 | 0.00090441 | 4 | 0.0885% | 0.9780% |
| Amount-history rule | 0.0008857 | 0.4869 | 0.00091692 | 6 | 0.1328% | 1.4670% |
| Logistic, calibrated | 0.0009415 | 0.4992 | 0.00090454 | 4 | 0.0885% | 0.9780% |
| CatBoost, calibrated | 0.0009381 | 0.5223 | 0.00090441 | 4 | 0.0885% | 0.9780% |

The 1% capacity budget reviews 4,519 records. Logistic and CatBoost each produce **4,515 false positives** and miss **405 of 409** fraud labels within this budget. Their 0.978% recall has an approximate 95% Wilson interval of **0.381%–2.487%**; precision has interval **0.0344%–0.2274%**. These wide intervals do not establish useful enrichment. Wilson intervals treat observations as independent; they do not adjust for customer clustering.

The rule's slightly larger capacity count is not supported by overall AP improvement. Constant-score ties, as well as candidate ties, use a label-independent transaction hash; the constant ranking is arbitrary and is not a fraud detector. Capacity metrics model a bounded review queue, not a validated production score threshold. The report also includes 5% capacity results.

Calibration is evaluated with Brier score, log loss, mean probability and ten equal-size score bins. Test observed prevalence is 0.090522%; mean calibrated logistic probability is approximately 0.091064%, and CatBoost is approximately 0.089260%. Near-correct average prevalence does not imply useful individual ranking. Decile bins may split tied scores and use hash ordering; this is especially relevant to the constant baseline.

## Shortcut comparator, slices and limitations

On the same final test, supplied `fraud_score > 30` yields 236 true positives, zero false positives and 173 false negatives; 90,393 scores are missing. Its unknown generation/availability and unexplained label separation make it unsuitable as an independent learned-model result. It is reported separately and is excluded from features and serving evidence.

The receipt includes selected-release slices by currency, channel, customer country, gender, timestamp anomaly and prior customer exposure. The test gender snapshots contain 152,403 F rows/151 positives, 149,621 M rows/121 positives, and 149,799 O rows/137 positives. These are the organizer's categories, not inferred identities. Current snapshots are imperfect historical audit attributes. No group is used to gate customer access or the right to report a dispute.

**Every final-test customer appeared in training history.** The unseen-customer slice has zero rows; there is no evidence of unseen-customer generalization. Small per-slice fraud counts and synthetic data prevent a fairness or production-safety certification. The selected constant gives every applicable record the same prior, so its per-slice review outcomes reflect prevalence and arbitrary tie ordering rather than a learned decision policy.

There is no evidence of prevented fraud losses, production savings, live-bank accuracy or customer outcomes. Model association never establishes guilt or liability. The customer's unrecognized-payment/scam report remains actionable even when numerical risk is low or unavailable.

## Runtime contract and reproduction

`factored_banking.fraud.assess(transaction)` returns status, nullable probability, model/feature versions, reasons and limitations. The selected JSON artifact is safe to load without pickle or executable model deserialization. An organizer-domain record receives `population_baseline`; a public team-generated fixture receives `out_of_domain` and **no probability**. Unknown currencies fail applicability. Missing model/validated features fail to `unavailable`, never zero risk. Every result is `review_only`; service authorization and workflow policy remain independent.

The logistic export path was also checked against the fitted sklearn pipeline/calibrator on 200 validation rows; maximum absolute probability error was below **2e-18**. A future CatBoost promotion uses the native CatBoost loader and requires the optional ML runtime dependencies; no handwritten tree engine is used. The current constant release does not require them.

```bash
uv run --locked python -m factored_banking.data_pipeline --export-sqlite
uv run --locked --group ml python -m factored_banking.train_fraud
uv run --locked --group ml pytest tests/test_data_pipeline.py tests/test_fraud.py tests/test_train_fraud.py
```

The report records the exact input feature hash, training source hash, selected artifact hash, pinned library versions, seeds, sampling, and CPU fit times. Runtime artifact metadata is versioned as `fraud-cpu-20261002-v1`; feature definitions are `strict-prior-30d-v1`. Public metrics contain no record IDs, names, contacts or raw rows. Reproduction changes machine-dependent timings; exact artifact receipts identify the measured run.

Implementation follows the documented [scikit-learn evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html), [probability calibration](https://scikit-learn.org/stable/modules/calibration.html), and [CatBoost classifier](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier.md). Those documents describe APIs and methodology; the numbers above are our local experiment results.
