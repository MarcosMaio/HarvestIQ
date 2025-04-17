import os
import json
import oracledb
from pathlib import Path

HISTORY_FILE = Path(os.environ.get("HISTORY_FILE_PATH", "harvest_history.json"))

def extract_and_validate(payload):
    try:
        area = float(payload["area"])
        production = float(payload["production"])
        loss_percentage = float(payload["loss_percentage"])
    except (KeyError, ValueError):
        raise ValueError("Missing or invalid required fields.")
      
    duration_hours = float(payload.get("duration_hours", 1.0))
    harvest_method = payload.get("harvest_method", "mechanical")
    moisture_percentage = float(payload.get("moisture_percentage", 0.0))
    
    return {
        "area": area,
        "production": production,
        "loss_percentage": loss_percentage,
        "duration_hours": duration_hours,
        "harvest_method": harvest_method,
        "moisture_percentage": moisture_percentage
    }


def calculate_metrics(data):
    lost_tonnage = (data["loss_percentage"] / 100) * data["production"]
    net_production = data["production"] - lost_tonnage
    productivity_per_hour = net_production / data["duration_hours"]
    productivity_per_hectare = net_production / data["area"]
    return {
        "lost_tonnage": round(lost_tonnage, 2),
        "net_production": round(net_production, 2),
        "productivity_per_hour": round(productivity_per_hour, 2),
        "productivity_per_hectare": round(productivity_per_hectare, 2)
    }


def generate_advice(data):
    alerts = []
    recommendations = []
    if data["loss_percentage"] > 10:
        alerts.append("Losses exceed the expected threshold (10%).")
        recommendations.append("Check cutter bar pressure.")
    if data["moisture_percentage"] > 20 and data["harvest_method"] == "mechanical":
        alerts.append("High moisture level for mechanical harvesting.")
        recommendations.append("Consider delaying harvest or using manual harvesting.")
    return {
        "alert": " ".join(alerts),
        "recommendation": " ".join(recommendations)
    }


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {HISTORY_FILE}. Starting fresh.")
            return []
        except OSError as e:
            print(f"Warning: Could not read history file {HISTORY_FILE}: {e}. Starting fresh.")
            return []
    return []


def save_history(history):
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=4), encoding="utf-8")
    except OSError as e:
        print(f"Error: Could not write history file {HISTORY_FILE}: {e}")


def append_record_json(record):
    history = load_history()
    history.append(record)
    save_history(history)


def connect_oracle():
    user = os.environ.get("ORACLE_USER")
    password = os.environ.get("ORACLE_PASSWORD")
    host = os.environ.get("ORACLE_HOST")
    port = os.environ.get("ORACLE_PORT", "1521") 
    service = os.environ.get("ORACLE_SERVICE_NAME")

    if not all([user, password, host, service]):
        raise ValueError("Missing required Oracle environment variables (ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_SERVICE_NAME)")

    dsn = f"{host}:{port}/{service}"

    return oracledb.connect(user=user, password=password, dsn=dsn)


def insert_record_oracle(connection, record):
    sql_params = {
        "area": record.get("area"),
        "production": record.get("production"),
        "loss_percentage": record.get("loss_percentage"),
        "lost_tonnage": record.get("lost_tonnage"),
        "net_production": record.get("net_production"),
        "productivity_per_hour": record.get("productivity_per_hour"),
        "productivity_per_hectare": record.get("productivity_per_hectare"),
        "alert": record.get("alert"), # Added alert
        "recommendation": record.get("recommendation") 
    }

    sql = """
    INSERT INTO harvest
      (area, production, loss_percentage, lost_tonnage, net_production,
       productivity_per_hour, productivity_per_hectare, alert, recommendation)
    VALUES
      (:area, :production, :loss_percentage, :lost_tonnage, :net_production,
       :productivity_per_hour, :productivity_per_hectare, :alert, :recommendation)
    """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, sql_params)
        connection.commit()
    finally:
        cursor.close() 