import os
import tempfile
import logging
from typing import Dict, List, Tuple, Any, Optional
import json
import oracledb
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HISTORY_FILE = Path(os.environ.get("HISTORY_FILE_PATH", "harvest_history.json"))

BRIX_THRESHOLD = 12.0
PRODUCTIVITY_THRESHOLD = 200.0
LOSS_THRESHOLD_FOR_OPERATOR = 15.0
LOSS_THRESHOLD = 10.0
TEMP_THRESHOLD = 35.0
MOIST_THRESHOLD = 20.0
MOIST_THRESHOLD_FOR_TEMP = 20.0


def sugar_quality_insight(data: Dict[str, Any], brix_threshold: float = BRIX_THRESHOLD) -> Tuple[List[str], List[str]]:
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
        raise ValueError("Input `data` must be a dict containing the key `brix_percentage`.")
    alert_messages, recommendations = [], []
    brix = data["brix_percentage"]
    if isinstance(brix, (int, float)):
        if brix < brix_threshold:
            alert_messages.append(f"Low °Brix ({brix}): sugar yield may be sub‑optimal.")
            recommendations.append(f"Consider delaying harvest until Brix ≥ {brix_threshold}.")
    else:
        alert_messages.append(f"Invalid Brix value: {brix}. Please provide a numeric value.")
    return alert_messages, recommendations

def equipment_maintenance_insight(data: Dict[str, Any], productivity_threshold: float = PRODUCTIVITY_THRESHOLD) -> Tuple[List[str], List[str]]:
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
        raise ValueError("Input `data` must be a dict containing the key `productivity_per_hour`.")
        
    prod_hr = data["productivity_per_hour"]
    
    if not isinstance(prod_hr, (int, float)):
        alert_messages.append("Missing or invalid `productivity_per_hour` value.")
        recommendations.append("Verify input data for equipment productivity.")
        return alert_messages, recommendations

    if prod_hr < productivity_threshold:
        alert_messages.append(f"Low hourly productivity ({prod_hr} t/h).")
        recommendations.append("Schedule preventive maintenance on equipment.")

    return alert_messages, recommendations

def operator_performance_insight(data: Dict[str, Any], loss_threshold: float = LOSS_THRESHOLD_FOR_OPERATOR) -> Tuple[List[str], List[str]]:
    """
    Analyze operator performance based on loss percentage.

    Parameters:
        data (dict): Must contain 'loss_percentage' (float or int) and 'operator_id' (str or int).
        loss_threshold (float): Maximum acceptable loss percentage.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []
    
    if not isinstance(data, dict) or "loss_percentage" not in data or "operator_id" not in data:
        raise ValueError("Input `data` must contain 'loss_percentage' and 'operator_id'.")
        
    loss = data["loss_percentage"]
    op = data["operator_id"]
    
    if isinstance(loss, (int, float)) and loss > loss_threshold:
        alert_messages.append(f"Operator {op} exceeded loss threshold ({loss}%).")
        recommendations.append("Recommend operator retraining or review procedure.")
        
    return alert_messages, recommendations

def temperature_moisture_insight(data: Dict[str, Any], temp_threshold: float = TEMP_THRESHOLD, moist_threshold: float = MOIST_THRESHOLD_FOR_TEMP) -> Tuple[List[str], List[str]]:
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
    
    if not isinstance(data, dict) or "ambient_temperature" not in data or "moisture_percentage" not in data:
        raise ValueError("Input `data` must contain 'ambient_temperature' and 'moisture_percentage'.")
        
    temp = data["ambient_temperature"]
    moist = data["moisture_percentage"]
    
    if isinstance(temp, (int, float)) and isinstance(moist, (int, float)):
        if temp > temp_threshold and moist > moist_threshold:
            alert_messages.append("High temp & moisture: risk of microbial spoilage.")
            recommendations.append("Process cane quickly or lower moisture prior to storage.")
            
    return alert_messages, recommendations

def loss_threshold_insight(data: Dict[str, Any], loss_threshold: float = LOSS_THRESHOLD) -> Tuple[List[str], List[str]]:
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
        raise ValueError("Input `data` must be a dict containing the key `loss_percentage`.")
        
    loss = data["loss_percentage"]
    
    if not isinstance(loss, (int, float)):
        alert_messages.append(f"Invalid loss value: {loss}. Please provide a numeric value.")
        recommendations.append("Verify input data for process loss.")
        return alert_messages, recommendations
        
    if loss > loss_threshold:
        alert_messages.append(f"Losses exceed the expected threshold ({loss_threshold}%).")
        recommendations.append("Check cutter bar pressure.")
        
    return alert_messages, recommendations

def moisture_mechanical_insight(data: Dict[str, Any], moist_thresh: float = MOIST_THRESHOLD) -> Tuple[List[str], List[str]]:
    """
    Analyze moisture levels for mechanical harvesting and provide alerts/recommendations.

    Parameters:
        data (dict): Must contain 'moisture_percentage' (float or int) and 'harvest_method' (str).
        moist_thresh (float): Maximum acceptable moisture percentage for mechanical harvesting.

    Returns:
        Tuple[List[str], List[str]]: (alert_messages, recommendations)
    """
    alert_messages, recommendations = [], []
    
    if not isinstance(data, dict) or "moisture_percentage" not in data or "harvest_method" not in data:
        raise ValueError("Input `data` must be a dict containing 'moisture_percentage' and 'harvest_method'.")
        
    moist = data["moisture_percentage"]
    method = data["harvest_method"]
    
    if not isinstance(moist, (int, float)):
        alert_messages.append(f"Invalid moisture value: {moist}. Please provide a numeric value.")
        recommendations.append("Verify input data for moisture percentage.")
        return alert_messages, recommendations
        
    if moist > moist_thresh and method == "mechanical":
        alert_messages.append("High moisture level for mechanical harvesting.")
        recommendations.append("Consider delaying harvest or using manual harvesting.")
        
    return alert_messages, recommendations

INSIGHT_FUNCTIONS = [
    loss_threshold_insight,
    moisture_mechanical_insight,
    sugar_quality_insight,
    equipment_maintenance_insight,
    operator_performance_insight,
    temperature_moisture_insight
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
            logging.error(f"Error in {getattr(fn, '__name__', repr(fn))}: {e}", exc_info=True)
    return {
        "alert": " ".join(alerts),
        "recommendation": " ".join(recs)
    }

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
        dict: Calculated metrics including lost_tonnage, net_production, productivity_per_hour, and productivity_per_hectare.
    """
    required_keys = ["loss_percentage", "production", "duration_hours", "area"]
    for key in required_keys:
        if key not in data or not isinstance(data[key], (int, float)):
            raise ValueError(f"Missing or invalid value for `{key}`")
    lost_tonnage = (data["loss_percentage"] / 100) * data["production"]
    net_production = data["production"] - lost_tonnage
    productivity_per_hour = net_production / data["duration_hours"] if data["duration_hours"] else 0.0
    productivity_per_hectare = net_production / data["area"] if data["area"] else 0.0
    return {
        "lost_tonnage": round(lost_tonnage, precision),
        "net_production": round(net_production, precision),
        "productivity_per_hour": round(productivity_per_hour, precision),
        "productivity_per_hectare": round(productivity_per_hectare, precision)
    }

def load_history(history_file=HISTORY_FILE) -> list:
    """
    Loads history from a JSON file, ensuring secure permissions.
    Returns an empty list if the file is missing, unreadable, or contains invalid JSON.
    """
    if not history_file.exists():
        return []
    try:
        os.chmod(history_file, 0o600) 
        return json.loads(history_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        logging.warning(f"Could not decode JSON from {history_file}. Starting fresh.")
    except OSError as e:
        logging.warning(f"Could not read history file {history_file}: {e}. Starting fresh.")
    return []

def save_history(history: object) -> None:
    """
    Safely serialize and save the history object as JSON to HISTORY_FILE.
    Uses a temporary file for atomic write. Logs errors on failure.
    """
    try:
        json_str = json.dumps(history, indent=4)
    except (TypeError, ValueError) as e:
        logging.error("Error: Provided history data is not serializable: %s", e)
        return

    try:
        with tempfile.NamedTemporaryFile(
            mode='w', dir=HISTORY_FILE.parent, delete=False, encoding="utf-8"
        ) as tf:
            tf.write(json_str)
            tempname = tf.name
        os.replace(tempname, HISTORY_FILE)
    except OSError as e:
        logging.error("Error: Could not write history file %s: %s", HISTORY_FILE, e)


def append_record_json(record: dict) -> None:
    """
    Append a new record to the JSON-based history.

    Args:
        record (dict): The data to append to the history.
    """
    history = load_history()
    history.append(record)
    save_history(history)

def connect_oracle(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    service: Optional[str] = None,
    **kwargs: Any
):
    """
    Establishes a connection to an Oracle database using provided credentials or environment variables.

    Args:
        user (str, optional): Oracle username.
        password (str, optional): Oracle password.
        host (str, optional): Oracle host address.
        port (int, optional): Oracle port number.
        service (str, optional): Oracle service name.
        **kwargs: Additional keyword arguments for oracledb.connect.

    Returns:
        connection: Oracle database connection object.

    Raises:
        ValueError: If required parameters are missing or invalid.
        Exception: If connection fails.
    """
    logger = logging.getLogger(__name__)

    user = user or os.environ.get("ORACLE_USER")
    password = password or os.environ.get("ORACLE_PASSWORD")
    host = host or os.environ.get("ORACLE_HOST")
    service = service or os.environ.get("ORACLE_SERVICE_NAME")
    port = port or os.environ.get("ORACLE_PORT", "1521")

    if not all([user, password, host, service]):
        msg = ("Missing required Oracle connection parameters "
               "(ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_SERVICE_NAME)")
        logger.error(msg)
        raise ValueError(msg)

    try:
        port = int(port)
    except (TypeError, ValueError):
        msg = f"Invalid ORACLE_PORT value: {port}. Must be an integer."
        logger.error(msg)
        raise ValueError(msg)

    dsn = f"{host}:{port}/{service}"
    logger.info(f"Attempting to connect to Oracle DB at {dsn}")

    try:
        connection = oracledb.connect(user=user, password=password, dsn=dsn, **kwargs)
        logger.info("Oracle DB connection established successfully.")
        return connection
    except Exception:
        logger.exception("Failed to connect to Oracle DB.")
        raise

def insert_record_oracle(connection, record):
    """
    Insert a record into the Oracle 'harvest' table with robust transaction handling.

    Args:
        connection: Oracle database connection object.
        record (dict): Dictionary containing required fields for the harvest table.

    Raises:
        ValueError: If required keys are missing in the record.
        oracledb.DatabaseError: If the insert fails.
    """
    now_sp = datetime.now(ZoneInfo("America/Sao_Paulo"))

    sql = """
    INSERT INTO harvest (
      area, production, loss_percentage,
      lost_tonnage, net_production,
      productivity_per_hour, productivity_per_hectare,
      alert, recommendation,
      created_at
    ) VALUES (
      :area, :production, :loss_percentage,
      :lost_tonnage, :net_production,
      :productivity_per_hour, :productivity_per_hectare,
      :alert, :recommendation,
      :created_at
    )
    """

    required_keys = [
        "area", "production", "loss_percentage", "lost_tonnage", "net_production",
        "productivity_per_hour", "productivity_per_hectare", "alert", "recommendation"
    ]
    missing_keys = [k for k in required_keys if k not in record]
    if missing_keys:
        raise ValueError(f"Missing required keys in record: {missing_keys}")

    params = {
        "area": record["area"],
        "production": record["production"],
        "loss_percentage": record["loss_percentage"],
        "lost_tonnage": record["lost_tonnage"],
        "net_production": record["net_production"],
        "productivity_per_hour": record["productivity_per_hour"],
        "productivity_per_hectare": record["productivity_per_hectare"],
        "alert": record["alert"],
        "recommendation": record["recommendation"],
        "created_at": now_sp 
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        connection.commit()
        logging.info("Record successfully inserted into Oracle DB")
    except oracledb.DatabaseError as e:
        logging.error(f"Failed to insert record into Oracle DB: {e}")
        try:
            connection.rollback()
            logging.info("Transaction rolled back successfully")
        except Exception as rollback_err:
            logging.error(f"Rollback failed: {rollback_err}")
        raise
