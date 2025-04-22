from typing import Any, Dict, List, Tuple

from config import BRIX_THRESHOLD


def sugar_quality_insight(
    data: Dict[str, Any], brix_threshold: float = BRIX_THRESHOLD
) -> Tuple[List[str], List[str]]:
    """
    Analyze sugar quality based on Brix percentage.

    Parameters:
        data (dict): Dictionary containing 'brix_percentage' (float or int).
        brix_threshold (float or int, optional): Minimum acceptable Brix percentage. Default is 12.

    Returns:
        tuple: (alert_messages, recommendations) where alert_messages is a list of warning messages and
            recommendations is a list of recommendations.
    """
    if not isinstance(data, dict) or "brix_percentage" not in data:
        raise ValueError(
            "Input `data` must be a dict containing the key `brix_percentage`."
        )
    alert_messages, recommendations = [], []
    brix = data["brix_percentage"]
    if isinstance(brix, (int, float)):
        if brix < brix_threshold:
            alert_messages.append(
                f"Low °Brix ({brix}): sugar yield may be sub‑optimal."
            )
            recommendations.append(
                f"Consider delaying harvest until Brix ≥ {brix_threshold}."
            )
    else:
        alert_messages.append(
            f"Invalid Brix value: {brix}. Please provide a numeric value."
        )
    return alert_messages, recommendations
