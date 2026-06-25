from __future__ import annotations

import numpy as np
import pandas as pd


MAX_ABS_FEATURE_VALUE = 1_000_000_000.0


def _numeric_frame(X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        frame = X.copy()
    else:
        frame = pd.DataFrame(X)
    return frame.apply(pd.to_numeric, errors="coerce")


def sanitize_features(
    X: pd.DataFrame | np.ndarray,
    *,
    drop_invalid_rows: bool = False,
    fill_value: float = 0.0,
    max_abs_value: float = MAX_ABS_FEATURE_VALUE,
) -> pd.DataFrame:
    """Return numeric, finite model features safe for sklearn input."""
    frame = _numeric_frame(X)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.clip(lower=-max_abs_value, upper=max_abs_value)

    if drop_invalid_rows:
        frame = frame.dropna(axis=0, how="any")
    else:
        frame = frame.fillna(fill_value)

    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(
            "Feature matrix still contains non-finite values after sanitization."
        )
    return frame


def validate_training_matrix(
    X: pd.DataFrame | np.ndarray,
    y: pd.Series | np.ndarray,
    *,
    min_rows: int = 10,
    max_abs_value: float = MAX_ABS_FEATURE_VALUE,
) -> tuple[pd.DataFrame, pd.Series]:
    """Clean X/y together and fail clearly when too little usable data remains."""
    features = sanitize_features(
        X,
        drop_invalid_rows=False,
        max_abs_value=max_abs_value,
    )
    target = pd.Series(
        y.copy() if isinstance(y, pd.Series) else y, index=features.index
    )
    target = pd.to_numeric(target, errors="coerce").replace([np.inf, -np.inf], np.nan)
    target = target.clip(lower=-max_abs_value, upper=max_abs_value)

    combined = features.copy()
    combined["__target__"] = target
    before = len(combined)
    combined = combined.dropna(axis=0, how="any")

    if len(combined) < min_rows:
        raise ValueError(
            f"Not enough finite training rows after ML sanitization: "
            f"{len(combined)} valid rows remain from {before}; need at least {min_rows}."
        )

    clean_X = combined.drop(columns=["__target__"])
    clean_y = combined["__target__"]

    if not np.isfinite(clean_X.to_numpy(dtype=float)).all():
        raise ValueError(
            "Training features contain non-finite values after sanitization."
        )
    if not np.isfinite(clean_y.to_numpy(dtype=float)).all():
        raise ValueError(
            "Training target contains non-finite values after sanitization."
        )

    return clean_X, clean_y
