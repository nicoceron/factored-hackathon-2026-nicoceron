import duckdb

from factored_banking.profile import load_table, profile_table, relation_quality


def test_audit_preserves_duplicate_and_null_keys(tmp_path):
    path = tmp_path / "customers.csv"
    path.write_text(
        "customer_id,country,segment,last_updated\n"
        "DEMO-1,Colombia,Basic,2026-06-01\n"
        "DEMO-1,Colombia,Basic,2026-06-01\n"
        ",Colombia,Basic,broken-date\n",
        encoding="utf-8-sig",
    )
    with duckdb.connect() as con:
        load_table(con, "customers", [path])
        report = profile_table(con, "customers")
    assert report["rows"] == 3
    assert report["duplicate_key_excess_rows"] == 1
    assert report["null_key_rows"] == 1
    assert report["last_updated_quality"]["invalid_rows"] == 1
    assert report["contract_status"] == "failed"


def test_missing_columns_fail_contract(tmp_path):
    path = tmp_path / "customers.csv"
    path.write_text("customer_id\nDEMO-1\n")
    with duckdb.connect() as con:
        load_table(con, "customers", [path])
        report = profile_table(con, "customers")
    assert report["contract_status"] == "failed"
    assert "country" in report["missing_required_columns"]


def test_duplicate_parents_do_not_inflate_join_coverage():
    with duckdb.connect() as con:
        con.execute("CREATE TABLE customers AS SELECT * FROM (VALUES ('A'), ('A')) t(customer_id)")
        con.execute(
            "CREATE TABLE products AS SELECT * FROM (VALUES ('A'), ('B'), (NULL)) t(customer_id)"
        )
        result = relation_quality(con, {"customers", "products"})
    assert result["products.customer_id->customers.customer_id"] == {
        "child_rows": 3,
        "null_fk_rows": 1,
        "unmatched_nonnull_rows": 1,
    }


def test_existing_product_id_is_not_proof_of_matching_customer():
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE products AS SELECT * FROM (VALUES ('P1', 'A', 'COP')) "
            "t(product_id, customer_id, currency)"
        )
        con.execute(
            "CREATE TABLE transactions AS SELECT * FROM "
            "(VALUES ('P1', 'A', 'COP'), ('P1', 'B', 'COP'), ('P1', 'A', 'USD')) "
            "t(product_id, customer_id, currency)"
        )
        result = relation_quality(con, {"transactions", "products"})
    assert result["transactions.product_id->products.product_id"]["unmatched_nonnull_rows"] == 0
    assert result["transaction_product_consistency"] == {
        "transaction_rows": 3,
        "rows_with_matching_product_customer_currency": 1,
    }
