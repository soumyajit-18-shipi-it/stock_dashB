from importlib import import_module
from typing import Any


__all__ = [
    "BaseModel",
    "LinearRegressionModel",
    "RandomForestModel",
    "StockPredictor",
    "arbitrate",
    "EnsembleResult",
]

_EXPORTS = {
    "BaseModel": ("ml.base_model", "BaseModel"),
    "LinearRegressionModel": ("ml.linear_model", "LinearRegressionModel"),
    "RandomForestModel": ("ml.random_forest_model", "RandomForestModel"),
    "StockPredictor": ("ml.predictor", "StockPredictor"),
    "arbitrate": ("ml.ensemble", "arbitrate"),
    "EnsembleResult": ("ml.ensemble", "EnsembleResult"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
