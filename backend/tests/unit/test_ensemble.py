from ml.ensemble import arbitrate, MIN_GAP


def test_arbitrate_agreement_up() -> None:
    # Both models predict UP (price >= last_close)
    linear_price = 105.0
    rf_price = 103.0
    linear_conf = 0.8
    rf_conf = 0.6
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is True
    assert res.model_used == "ensemble"
    # Weighted calculation:
    # total_conf = 1.4
    # w_lin = 0.8 / 1.4 = 0.5714
    # w_rf = 0.6 / 1.4 = 0.4286
    # predicted = 0.5714 * 105 + 0.4286 * 103 = 60.0 + 44.1458 = 104.1429
    assert res.predicted_price == 104.1429
    assert res.low_confidence is False


def test_arbitrate_agreement_down() -> None:
    # Both models predict DOWN
    linear_price = 95.0
    rf_price = 97.0
    linear_conf = 0.5
    rf_conf = 0.5
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is True
    assert res.predicted_price == 96.0
    assert res.low_confidence is True  # gap is 0 < MIN_GAP


def test_arbitrate_agreement_zero_conf() -> None:
    linear_price = 105.0
    rf_price = 103.0
    linear_conf = 0.0
    rf_conf = 0.0
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is True
    assert res.predicted_price == 104.0  # (105 + 103) / 2 = 104.0
    assert res.low_confidence is True  # gap = 0 < MIN_GAP


def test_arbitrate_disagreement_linear_wins() -> None:
    # Linear predicts UP, RF predicts DOWN. Linear confidence is higher.
    linear_price = 105.0
    rf_price = 95.0
    linear_conf = 0.9
    rf_conf = 0.4
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is False
    assert res.model_used == "linear"
    assert res.predicted_price == 105.0
    assert res.low_confidence is False  # gap = 0.5 >= MIN_GAP


def test_arbitrate_disagreement_rf_wins() -> None:
    # Linear predicts DOWN, RF predicts UP. RF confidence is higher.
    linear_price = 95.0
    rf_price = 105.0
    linear_conf = 0.3
    rf_conf = 0.8
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is False
    assert res.model_used == "random_forest"
    assert res.predicted_price == 105.0
    assert res.low_confidence is False  # gap = 0.5 >= MIN_GAP


def test_arbitrate_disagreement_low_confidence() -> None:
    # Disagreement but gap < MIN_GAP (e.g. 0.01)
    linear_price = 105.0
    rf_price = 95.0
    linear_conf = 0.6
    rf_conf = 0.59
    last_close = 100.0

    res = arbitrate(
        linear_price,
        rf_price,
        linear_conf,
        rf_conf,
        last_close,
    )

    assert res.agreement is False
    assert res.low_confidence is True
    assert res.model_used == "linear"
