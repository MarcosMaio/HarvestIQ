from typing import Any, Dict, List, Tuple

from config import LOSS_THRESHOLD_FOR_OPERATOR


def operator_performance_insight(
    data: Dict[str, Any], loss_threshold: float = LOSS_THRESHOLD_FOR_OPERATOR
) -> Tuple[List[str], List[str]]:
    """
    Analyze operator performance based on loss percentage.

    Parameters:
        data (dict): Must contain 'loss_percentage' (float or int) and 'operator_id' (str or int).
        loss_threshold (float): Maximum acceptable loss percentage.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []

    if (
        not isinstance(data, dict)
        or "loss_percentage" not in data
        or "operator_id" not in data
    ):
        raise ValueError(
            "Input `data` must contain 'loss_percentage' and 'operator_id'."
        )

    loss = data["loss_percentage"]
    op = data["operator_id"]

    if isinstance(loss, (int, float)) and loss > loss_threshold:
        alert_messages.append(f"Operator {op} exceeded loss threshold ({loss}%).")
        recommendations.append("Recommend operator retraining or review procedure.")

    return alert_messages, recommendations
