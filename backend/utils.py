import os
import json
import oracledb
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HISTORY_FILE = Path(os.environ.get("HISTORY_FILE_PATH", "harvest_history.json"))

def sugar_quality_insight(data):
    alerts, recs = [], []
    brix = data["brix_percentage"]
    if brix < 12:
        alerts.append(f"Low °Brix ({brix}): sugar yield may be sub‑optimal.")
        recs.append("Consider delaying harvest until Brix ≥ 12.")
    return alerts, recs

def equipment_maintenance_insight(data):
    alerts, recs = [], []
    prod_hr = data["productivity_per_hour"]
    if prod_hr < 200:
        alerts.append(f"Low hourly productivity ({prod_hr} t/h).")
        recs.append("Schedule preventive maintenance on equipment.")
    return alerts, recs

def operator_performance_insight(data):
    alerts, recs = [], []
    loss = data["loss_percentage"]
    op = data["operator_id"]
    if loss > 15:
        alerts.append(f"Operator {op} exceeded loss threshold ({loss}%).")
        recs.append("Recommend operator retraining or review procedure.")
    return alerts, recs

def temperature_moisture_insight(data):
    alerts, recs = [], []
    temp = data["ambient_temperature"]
    moist = data["moisture_percentage"]
    if temp > 35 and moist > 20:
        alerts.append("High temp & moisture: risk of microbial spoilage.")
        recs.append("Process cane quickly or lower moisture prior to storage.")
    return alerts, recs


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
    alerts, recs = [], []

    if data["loss_percentage"] > 10:
        alerts.append("Losses exceed the expected threshold (10%).")
        recs.append("Check cutter bar pressure.")
    if data["moisture_percentage"] > 20 and data["harvest_method"] == "mechanical":
        alerts.append("High moisture level for mechanical harvesting.")
        recs.append("Consider delaying harvest or using manual harvesting.")

    for fn in [
        sugar_quality_insight,
        equipment_maintenance_insight,
        operator_performance_insight,
        temperature_moisture_insight
    ]:
        a, r = fn(data)
        alerts.extend(a)
        recs.extend(r)

    return {
        "alert": " ".join(alerts),
        "recommendation": " ".join(recs)
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

    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        connection.commit()
    finally:
        cursor.close()