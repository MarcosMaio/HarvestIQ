from typing import Any, Dict, List, Tuple

from config import PRODUCTIVITY_THRESHOLD


def equipment_maintenance_insight(
    data: Dict[str, Any], productivity_threshold: float = PRODUCTIVITY_THRESHOLD
) -> Tuple[List[str], List[str]]:
    """
    Analyze equipment productivity and recommend maintenance if below threshold.

    Parameters:
        data (dict): Must contain 'productivity_per_hour' (float or int).
        productivity_threshold (float): Minimum acceptable productivity per hour.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []

    if not isinstance(data, dict) or "productivity_per_hour" not in data:
        raise ValueError(
            "Input `data` must be a dict containing the key `productivity_per_hour`."
        )

    prod_hr = data["productivity_per_hour"]

    if not isinstance(prod_hr, (int, float)):
        alert_messages.append("Missing or invalid `productivity_per_hour` value.")
        recommendations.append("Verify input data for equipment productivity.")
        return alert_messages, recommendations

    if prod_hr < productivity_threshold:
        alert_messages.append(f"Low hourly productivity ({prod_hr} t/h).")
        recommendations.append("Schedule preventive maintenance on equipment.")

    return alert_messages, recommendations
