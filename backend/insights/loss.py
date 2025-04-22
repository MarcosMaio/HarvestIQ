from typing import Any, Dict, List, Tuple

from config import LOSS_THRESHOLD


def loss_threshold_insight(
    data: Dict[str, Any], loss_threshold: float = LOSS_THRESHOLD
) -> Tuple[List[str], List[str]]:
    """
    Analyze process loss percentage and provide alerts/recommendations if above threshold.

    Parameters:
        data (dict): Must contain 'loss_percentage' (float or int).
        loss_threshold (float): Maximum acceptable loss percentage.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []

    if not isinstance(data, dict) or "loss_percentage" not in data:
        raise ValueError(
            "Input `data` must be a dict containing the key `loss_percentage`."
        )

    loss = data["loss_percentage"]

    if not isinstance(loss, (int, float)):
        alert_messages.append(
            f"Invalid loss value: {loss}. Please provide a numeric value."
        )
        recommendations.append("Verify input data for process loss.")
        return alert_messages, recommendations

    if loss > loss_threshold:
        alert_messages.append(
            f"Losses exceed the expected threshold ({loss_threshold}%)."
        )
        recommendations.append("Check cutter bar pressure.")

    return alert_messages, recommendations
