# Dataset findings — September 27, 2026

These are measured findings from the full downloaded S3 inventory, not the documentation's advertised row counts or a model evaluation. Reproduce with `make data-sync` followed by `make profile`. The [aggregate JSON receipt](evidence/data-profile-summary.json) contains the audit results; raw rows and the audit database remain excluded from Git.

## Coverage

- All **7,671 objects** present, with **zero missing files or byte-size mismatches** against the S3 inventory captured during setup.
- **5,349,322,481 bytes**, about **5.35 GB** of source CSVs.
- **23,495,188 rows** across **13 tables**. The documentation says approximately 19 million, so use measured counts in the presentation.
- Each raw file has a SHA-256 hash in the local manifest. Manifest digest: `eaa9e657c1636059d77bd48a26fbdd839e155aac04fac92c73d38296e86b144d`.
- DuckDB version: `1.5.5`. Audit timestamp: `2026-09-27T21:26:59.574112+00:00`.

| Table | Measured rows | CSV files |
| --- | ---: | ---: |
| `customers` | 150,000 | 1 |
| `products` | 400,000 | 1 |
| `branches` | 350 | 1 |
| `service_agents` | 1,200 | 1 |
| `marketing_campaigns` | 200 | 1 |
| `transactions` | 4,425,008 | 1,097 |
| `call_center_interactions` | 686,296 | 1,097 |
| `call_transcripts` | 171,321 | 1,097 |
| `satisfaction_surveys` | 212,759 | 1,097 |
| `digital_events` | 15,620,994 | 1,097 |
| `complaints` | 67,095 | 1,097 |
| `campaign_sends` | 1,746,801 | 1,083 |
| `daily_exchange_rates` | 13,164 | 1 |

## Transcript evidence is highly repetitive

There are **171,321 transcripts**, but only **546 distinct full transcripts** and **42 distinct customer-text strings**. All 171,321 rows have detected language `es`; this metadata does not establish Portuguese support.

Every customer-text row contains the substring `saldo`. All 42 distinct customer-text strings occur under more than one contact-reason category. Among joined transcript rows, **29,198** have interaction category `Queja`, and all 29,198 still contain `saldo` in customer text. This demonstrates that the category cannot safely be treated as a text-intent ground-truth label. Substring checks alone do not fully characterize conversation intent.

A limited case-insensitive lexical probe over full text (`fraud`, `no reconoz`, `no autoriz`, `duplicad`, `reembolso`, `devoluci`, `disputa`) found **zero matching rows**. This is an exploratory check, not proof that every possible dispute expression was exhaustively searched. No additional transcript source was demonstrated by the inspected inventory/documents.

Implications:

- Group by repeated/related templates before splitting. A random row split would leak highly similar wording.
- Review labels independently. Do not train a classifier on noisy `reason_category` labels and report its accuracy as real intent understanding.
- Create clearly labeled, reviewed Spanish/Portuguese evaluation scenarios for the actual workflow; report them separately from organizer-data measurements.
- Balance inquiries are represented in text; more complex payment questions and dispute handoffs still need a valid evaluation set.

## Demand metadata supports a narrow starting point

`Transaccional` is the largest interaction category: **240,056 / 686,296 (34.98%)**. The remaining categories are Producto, Queja, Técnico, Comercial, and Retención. `contact_reason` and `reason_category` have the same category totals in this snapshot; these fields are broad rather than precise request labels.

Transcript rows are about **24.96%** of interaction rows. This row-count ratio is not a validated sampling design and must not be used as a multiplier for real production traffic. Historical resolution/escalation flags describe the supplied synthetic data, not our proposed system's performance.

## Core record joins are usable in the measured snapshot

All tested non-null core FKs match: products to customers; transactions to customers and products; interactions to customers; transcripts to customers and interactions; complaints to customers. All **171,321 transcript rows** agree with the linked interaction's customer ID.

All **4,425,008 transaction rows** have a matching product with the same customer and currency. These checks support account/payment record lookup. They do not replace customer-scoped authorization in the service.

Every one of the **67,095 complaints** has a null `origin_interaction_id`. Complaint customer IDs match the customer table, but customer identity alone does not identify which interaction caused a complaint. Do not force a complaint/transcript match through customer ID alone.

The primary-key audit found zero null keys and zero excess duplicate keys in all 13 tables, including the composite exchange-rate key. This differs from the approximate duplicate rate in the documentation. It is not proof that all business fields or every documented constraint are valid.

## Date and currency limitations

**1,106,307 / 4,425,008 transactions (25.00%)** have an event **calendar date** after `process_date`. The latest parsed transaction timestamp is **2026-06-18 05:59:41**, while the documented range ends June 17. These facts do not establish a timezone or ingestion explanation. Keep both fields and flag the discrepancy; do not silently adjust timestamps.

In the downloaded `transactions` table, currencies are USD, COP, and ARS. MXN does not occur in that field in this snapshot, despite the documentation listing it. Complaint currencies include MXN as well as COP, ARS, USD, and null. Query each field's actual values and preserve currency with every amount.

The campaign send-cost/conversion-value currency remains unspecified by the dictionary; do not assume USD. Do not present historical June 2026 balances as live September balances.

## Recommended decision

Build **account/payment inquiry support with a safe dispute handoff** as the provisional workflow. The verified product/transaction ownership relationships provide useful structured evidence, and balance language is present in the transcript corpus. The stronger evaluation story is to expose and handle the limitations, then test a learned multilingual component on independently reviewed held-out scenarios.

This is an engineering recommendation, not an organizer rule or a measured model result. Remaining data work includes full serving contracts, freshness policy, conflict/quarantine handling, valid labels, and permission-compatible record projections.
