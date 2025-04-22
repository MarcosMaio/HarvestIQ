from typing import Any, Dict


def calculate_metrics(data: Dict[str, Any], precision: int = 2) -> Dict[str, float]:
    """
    Args:
        data (dict): Dictionary with the following keys:
            - loss_percentage (float): Percentage of loss (0-100).
            - production (float): Total production value.
            - duration_hours (float): Duration in hours.
            - area (float): Area in hectares.
        precision (int, optional): Number of decimal places to round results to. Defaults to 2.

    Returns:
        dict: Calculated metrics including lost_tonnage, net_production,
        productivity_per_hour, and productivity_per_hectare.
    """
    required_keys = ["loss_percentage", "production", "duration_hours", "area"]
    for key in required_keys:
        if key not in data or not isinstance(data[key], (int, float)):
            raise ValueError(f"Missing or invalid value for `{key}`")
    lost_tonnage = (data["loss_percentage"] / 100) * data["production"]
    net_production = data["production"] - lost_tonnage
    productivity_per_hour = (
        net_production / data["duration_hours"] if data["duration_hours"] else 0.0
    )
    productivity_per_hectare = net_production / data["area"] if data["area"] else 0.0
    return {
        "lost_tonnage": round(lost_tonnage, precision),
        "net_production": round(net_production, precision),
        "productivity_per_hour": round(productivity_per_hour, precision),
        "productivity_per_hectare": round(productivity_per_hectare, precision),
    }
