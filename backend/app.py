import datetime
import logging
import os
from typing import Optional

import oracledb
from flask import Flask, jsonify, request
from insights.__init__ import generate_advice
from metrics import calculate_metrics
from models import HarvestPayload
from persistence.json_store import append_record_json
from persistence.oracle_store import connect_oracle, insert_record_oracle
from pydantic import ValidationError

app = Flask(__name__)

HARVESTS_SELECT_SQL = """
SELECT id, area, production, loss_percentage, lost_tonnage,
net_production, productivity_per_hour, productivity_per_hectare,
alert, recommendation, created_at
FROM harvest
ORDER BY created_at DESC
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
"""


@app.route("/health", methods=["GET"])
def health_check() -> tuple:
    """
    Health check endpoint.
    Checks Oracle DB connectivity.
    Returns JSON response with status and disables caching.
    """
    app.logger.info("Health check requested")
    db_status = "ok"
    try:
        with connect_oracle() as _conn:
            app.logger.debug("Oracle connection opened and will now be closed")
    except Exception as e:
        db_status = "unavailable"
        app.logger.error(f"Oracle DB health check failed: {str(e)}")

    response_data = {"status": "ok", "oracle_db": db_status}
    app.logger.info(f"Health check response: {response_data}")

    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    status_code = 200 if db_status == "ok" else 503
    return response, status_code


@app.route("/harvest", methods=["POST"])
def harvest() -> tuple:
    """
    Handles POST requests to create a new harvest record.
    Validates input, computes metrics and advice, saves to JSON and Oracle DB.
    Returns appropriate JSON responses for success or error conditions.
    """
    conn: Optional[object] = None
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Request body must be JSON."}), 400

        # Strip whitespace from key string fields
        for key in ("operator_id", "equipment_id", "variety"):
            if isinstance(payload.get(key), str):
                payload[key] = payload[key].strip()

        # Validate payload using Pydantic model
        try:
            valid = HarvestPayload(**payload)
        except ValidationError as e:
            errors = {".".join(map(str, err["loc"])): err["msg"] for err in e.errors()}
            return jsonify({"validation_errors": errors}), 422

        data = valid.model_dump()
        data |= calculate_metrics(data)
        data |= generate_advice(data)

        # Ensure harvest_date is ISO formatted string
        harvest_date = data.get("harvest_date")
        if isinstance(harvest_date, (datetime.date, datetime.datetime)):
            data["harvest_date"] = harvest_date.isoformat()

        append_record_json(data)

        try:
            conn = connect_oracle()
            insert_record_oracle(conn, data)
        except oracledb.DatabaseError as db_err:
            logging.error(f"Oracle DB Error: {db_err}")
            return jsonify({"error": "Failed to save to database."}), 500

        return (
            jsonify({"message": "Harvest created successfully", "harvest": data}),
            201,
        )

    except (TypeError, KeyError) as e:
        logging.error(f"Bad Request Error: {e}")
        return jsonify({"error": "Invalid input data."}), 400
    except Exception:
        logging.exception("Internal Server Error")
        return jsonify({"error": "An unexpected internal server error occurred."}), 500
    finally:
        if conn:
            conn.close()


@app.route("/harvests", methods=["GET"])
def get_harvests() -> tuple:
    """
    Retrieves paginated harvest records from the Oracle database and returns them as JSON.
    Query Parameters:
        - page (int): Page number (default: 1)
        - page_size (int): Number of records per page (default: 50)
    Returns:
        - JSON response with list of harvest records and HTTP status code.
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        offset = (page - 1) * page_size

        with connect_oracle() as conn, conn.cursor() as cursor:
            cursor.execute(HARVESTS_SELECT_SQL, {"offset": offset, "limit": page_size})
            columns = [col[0].lower() for col in cursor.description]
            result_list = [
                {
                    col: (
                        val.isoformat()
                        if isinstance(val, (datetime.date, datetime.datetime))
                        else val
                    )
                    for col, val in zip(columns, row)
                }
                for row in cursor.fetchall()
            ]

        return jsonify(result_list), 200

    except oracledb.DatabaseError as db_err:
        logging.error(f"Oracle Database Error on GET /harvests: {db_err}")
        return jsonify({"error": "Failed to retrieve records from database."}), 500
    except ValueError as env_err:
        logging.error(f"Configuration Error: {env_err}")
        return jsonify({"error": "Server configuration error."}), 500
    except Exception as e:
        import traceback

        traceback.print_exc()
        logging.error(f"Unhandled exception on GET /harvests: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
