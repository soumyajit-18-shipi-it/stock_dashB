"""
ensemble.py
-----------
Arbitration logic for when Linear and Random Forest models disagree
on the direction of the next price move.

Design decisions
~~~~~~~~~~~~~~~~
1. **Agreement → weighted average**
   When both models predict the same direction, blend their predictions
   weighted by relative confidence.  This gives a single point estimate
   that benefits from both signals.

2. **Disagreement → higher-confidence model wins**
   When the models predict opposite directions (one UP, one DOWN), we
   trust the model with the higher confidence score entirely rather than
   averaging — an average of +2% and -1% producing +0.5% would be
   misleading and directionally ambiguous.

3. **Confidence gap threshold**
   If the confidence gap between the two models is very small (< MIN_GAP),
   even the "winner" is treated as low-confidence and the result is flagged.

Indian-market note
~~~~~~~~~~~~~~~~~~
Indian equity markets (NSE/BSE) are heavily influenced by:
  - FII (Foreign Institutional Investor) flow data released EOD
  - RBI monetary policy announcements (every ~6 weeks)
  - Global cues from SGX Nifty / Dow futures overnight
These factors create sharp gap-up/gap-down opens that purely
technical models cannot predict.  The `low_confidence` flag in
`EnsembleResult` surfaces this uncertainty to the UI so users
are not given a falsely precise prediction.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


# Minimum confidence gap for the winner to be "trusted"
MIN_GAP = 0.05


@dataclass
class EnsembleResult:
    predicted_price: float
    confidence: float
    model_used: str          # "linear" | "random_forest" | "ensemble"
    agreement: bool
    low_confidence: bool
    linear_price: float
    rf_price: float
    linear_confidence: float
    rf_confidence: float
    arbitration_reason: str = ""


def arbitrate(
    linear_price: float,
    rf_price: float,
    linear_confidence: float,
    rf_confidence: float,
    last_close: float,
) -> EnsembleResult:
    """
    Core arbitration function.

    Parameters
    ----------
    linear_price, rf_price          : next-day price predictions
    linear_confidence, rf_confidence: confidence scores ∈ [0, 1]
    last_close                      : most recent closing price

    Returns
    -------
    EnsembleResult with a single predicted_price and metadata.
    """
    linear_up = linear_price >= last_close
    rf_up = rf_price >= last_close
    agreement = linear_up == rf_up

    gap = abs(linear_confidence - rf_confidence)
    low_confidence = gap < MIN_GAP

    if agreement:
        # Weighted blend — both point the same way
        total_conf = linear_confidence + rf_confidence
        if total_conf == 0:
            w_lin = w_rf = 0.5
        else:
            w_lin = linear_confidence / total_conf
            w_rf = rf_confidence / total_conf

        predicted = w_lin * linear_price + w_rf * rf_price
        blended_conf = (linear_confidence * w_lin + rf_confidence * w_rf)
        reason = (
            f"Both models agree ({'UP' if linear_up else 'DOWN'}). "
            f"Blended {w_lin:.0%} linear + {w_rf:.0%} RF."
        )
        return EnsembleResult(
            predicted_price=round(predicted, 4),
            confidence=round(blended_conf, 4),
            model_used="ensemble",
            agreement=True,
            low_confidence=low_confidence,
            linear_price=linear_price,
            rf_price=rf_price,
            linear_confidence=linear_confidence,
            rf_confidence=rf_confidence,
            arbitration_reason=reason,
        )

    # Disagreement — pick the winner
    if linear_confidence >= rf_confidence:
        winner_price = linear_price
        winner_conf = linear_confidence
        winner_name = "linear"
        loser_direction = "UP" if rf_up else "DOWN"
        winner_direction = "UP" if linear_up else "DOWN"
    else:
        winner_price = rf_price
        winner_conf = rf_confidence
        winner_name = "random_forest"
        loser_direction = "UP" if linear_up else "DOWN"
        winner_direction = "UP" if rf_up else "DOWN"

    reason = (
        f"Models disagree (Linear: {'UP' if linear_up else 'DOWN'}, "
        f"RF: {'UP' if rf_up else 'DOWN'}). "
        f"Using {winner_name} (conf={winner_conf:.3f}) over the other "
        f"(conf={min(linear_confidence, rf_confidence):.3f}). "
        f"Gap={gap:.3f}."
    )

    return EnsembleResult(
        predicted_price=round(winner_price, 4),
        confidence=round(winner_conf, 4),
        model_used=winner_name,
        agreement=False,
        low_confidence=low_confidence,
        linear_price=linear_price,
        rf_price=rf_price,
        linear_confidence=linear_confidence,
        rf_confidence=rf_confidence,
        arbitration_reason=reason,
    )