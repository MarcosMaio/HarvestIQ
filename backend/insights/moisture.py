from typing import Any, Dict, List, Tuple

from config import MOIST_THRESHOLD, MOIST_THRESHOLD_FOR_TEMP, TEMP_THRESHOLD


def moisture_mechanical_insight(
    data: Dict[str, Any], moist_thresh: float = MOIST_THRESHOLD
) -> Tuple[List[str], List[str]]:
    """
    Analyze moisture levels for mechanical harvesting and provide alerts/recommendations.

    Parameters:
        data (dict): Must contain 'moisture_percentage' (float or int) and 'harvest_method' (str).
        moist_thresh (float): Maximum acceptable moisture percentage for mechanical harvesting.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []

    if (
        not isinstance(data, dict)
        or "moisture_percentage" not in data
        or "harvest_method" not in data
    ):
        raise ValueError(
            "Input `data` must be a dict containing 'moisture_percentage' and 'harvest_method'."
        )

    moist = data["moisture_percentage"]
    method = data["harvest_method"]

    if not isinstance(moist, (int, float)):
        alert_messages.append(
            f"Invalid moisture value: {moist}. Please provide a numeric value."
        )
        recommendations.append("Verify input data for moisture percentage.")
        return alert_messages, recommendations

    if moist > moist_thresh and method == "mechanical":
        alert_messages.append("High moisture level for mechanical harvesting.")
        recommendations.append("Consider delaying harvest or using manual harvesting.")

    return alert_messages, recommendations


def temperature_moisture_insight(
    data: Dict[str, Any],
    temp_threshold: float = TEMP_THRESHOLD,
    moist_threshold: float = MOIST_THRESHOLD_FOR_TEMP,
) -> Tuple[List[str], List[str]]:
    """
    Analyze ambient temperature and moisture for spoilage risk.

    Parameters:
        data (dict): Must contain 'ambient_temperature' (float or int) and 'moisture_percentage' (float or int).
        temp_threshold (float): Maximum safe ambient temperature.
        moist_threshold (float): Maximum safe moisture percentage.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []

    if (
        not isinstance(data, dict)
        or "ambient_temperature" not in data
        or "moisture_percentage" not in data
    ):
        raise ValueError(
            "Input `data` must contain 'ambient_temperature' and 'moisture_percentage'."
        )

    temp = data["ambient_temperature"]
    moist = data["moisture_percentage"]

    if isinstance(temp, (int, float)) and isinstance(moist, (int, float)):
        if temp > temp_threshold and moist > moist_threshold:
            alert_messages.append("High temp & moisture: risk of microbial spoilage.")
            recommendations.append(
                "Process cane quickly or lower moisture prior to storage."
            )

    return alert_messages, recommendations
