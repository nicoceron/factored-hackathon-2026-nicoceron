import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("catboost", reason="Run uv run --group ml pytest for offline ML checks")

from factored_banking.train_fraud import capacity, metrics, wilson  # noqa: E402


def test_review_capacity_preserves_prevalence_and_ties_are_label_independent():
    y = np.array([1, 0, 0, 1, 0])
    scores = np.full(5, 0.001)
    keys = np.array(["e", "d", "c", "b", "a"])
    result = capacity(y, scores, keys, 0.4)
    assert result["reviewed"] == 2
    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert capacity(y[::-1], scores, keys[::-1], 0.4) == result


def test_no_positive_slice_is_explicit_and_calibration_bins_cover_all_rows():
    result = metrics(np.zeros(20), np.full(20, 0.001), np.arange(20))
    assert result["average_precision"] is None
    assert result["roc_auc"] is None
    assert result["capacity_1pct"]["recall"] is None
    assert sum(part["rows"] for part in result["calibration_deciles"]) == 20
    assert wilson(0, 0) is None
