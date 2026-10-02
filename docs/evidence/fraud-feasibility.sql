-- Aggregate diagnostics only. Run against artifacts/data-profile.duckdb after make profile.
-- Exploratory full-snapshot analysis, not a held-out model evaluation.
SELECT is_fraud, count(*) AS rows FROM transactions GROUP BY is_fraud ORDER BY is_fraud;

SELECT is_fraud, count(*) AS rows,
       count(try_cast(fraud_score AS DOUBLE)) AS scored,
       min(try_cast(fraud_score AS DOUBLE)) AS minimum,
       max(try_cast(fraud_score AS DOUBLE)) AS maximum
FROM transactions GROUP BY is_fraud ORDER BY is_fraud;

SELECT count(*) AS n, count(*) FILTER (WHERE is_fraud = 'True') AS positives,
       count(*) FILTER (WHERE is_fraud = 'True' AND try_cast(fraud_score AS DOUBLE) > 30) AS tp,
       count(*) FILTER (WHERE is_fraud = 'False' AND try_cast(fraud_score AS DOUBLE) > 30) AS fp,
       count(*) FILTER (WHERE is_fraud = 'True' AND
                       coalesce(try_cast(fraud_score AS DOUBLE), 0) <= 30) AS fn,
       count(*) FILTER (WHERE fraud_score IS NULL) AS missing_score,
       count(*) FILTER (WHERE merchant_name IS NULL) AS missing_merchant
FROM transactions;

-- Proposed partitions only: no model is fitted or evaluated by this query.
SELECT CASE
           WHEN try_cast(transaction_date AS TIMESTAMP) < TIMESTAMP '2026-01-01'
               THEN '1_train_before_2026'
           WHEN try_cast(transaction_date AS TIMESTAMP) < TIMESTAMP '2026-03-01'
               THEN '2_validate_jan_feb_2026'
           WHEN try_cast(transaction_date AS TIMESTAMP) IS NOT NULL
               THEN '3_test_mar_jun_2026'
           ELSE '4_invalid_timestamp'
       END AS split,
       count(*) AS transactions,
       count(*) FILTER (WHERE is_fraud = 'True') AS fraud_labels
FROM transactions GROUP BY split ORDER BY split;

SELECT count(DISTINCT customer_id) AS customers,
       count(DISTINCT customer_id) FILTER (WHERE is_fraud = 'True') AS customers_with_fraud
FROM transactions;
