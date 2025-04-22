import logging

from .brix import sugar_quality_insight
from .equipment import equipment_maintenance_insight
from .loss import loss_threshold_insight
from .moisture import moisture_mechanical_insight, temperature_moisture_insight
from .operator import operator_performance_insight

INSIGHT_FUNCTIONS = [
    loss_threshold_insight,
    moisture_mechanical_insight,
    temperature_moisture_insight,
    sugar_quality_insight,
    equipment_maintenance_insight,
    operator_performance_insight,
]


def generate_advice(data: dict[str, any]) -> dict[str, str]:
    """
    Aggregates alerts and recommendations from multiple insight functions based on input data.

    Args:
        data (dict[str, any]): Input data to be analyzed by each insight function.

    Returns:
        dict[str, str]: A dictionary containing concatenated alert and recommendation messages.
    """
    alerts, recs = [], []
    for fn in INSIGHT_FUNCTIONS:
        try:
            a, r = fn(data)
            alerts += a
            recs += r
        except Exception as e:
            logging.error(
                f"Error in {getattr(fn, '__name__', repr(fn))}: {e}", exc_info=True
            )
    return {"alert": " ".join(alerts), "recommendation": " ".join(recs)}
