import logging
import os
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import oracledb


def connect_oracle(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    service: Optional[str] = None,
    **kwargs: Any,
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
        msg = (
            "Missing required Oracle connection parameters "
            "(ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_SERVICE_NAME)"
        )
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
        "area",
        "production",
        "loss_percentage",
        "lost_tonnage",
        "net_production",
        "productivity_per_hour",
        "productivity_per_hectare",
        "alert",
        "recommendation",
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
        "created_at": now_sp,
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
