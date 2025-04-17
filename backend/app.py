import os
import json
import datetime
import oracledb
from pathlib import Path
from flask import Flask, request, jsonify
from models import HarvestPayload
from pydantic import ValidationError
from utils import calculate_metrics, generate_advice, append_record_json, connect_oracle, insert_record_oracle

app = Flask(__name__)

# --- Health check ---
@app.route("/health", methods=["GET"])
def health_check():
    # Basic health check: checks if the Flask app is running
    # More advanced checks could try connecting to the DB
    return jsonify({"status": "ok"}), 200

@app.route("/harvest", methods=["POST"])
def harvest():
    conn = None
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Request body must be JSON."}), 400

        try:
            valid = HarvestPayload(**payload)
        except ValidationError as e:
            errors = {
                ".".join(str(loc) for loc in err["loc"]): err["msg"]
                for err in e.errors()
            }
            return jsonify({"validation_errors": errors}), 422

        data = valid.model_dump()

        data.update(calculate_metrics(data))
        data.update(generate_advice(data))

        if isinstance(data.get("harvest_date"), (datetime.date, datetime.datetime)):
            data["harvest_date"] = data["harvest_date"].isoformat()

        append_record_json(data)
        
        try:
            conn = connect_oracle()
            insert_record_oracle(conn, data)
        except oracledb.DatabaseError as db_err:
            print(f"Oracle DB Error: {db_err}")
            return jsonify({"error": "Failed to save to database."}), 500
        finally:
            if conn:
                conn.close()

        return jsonify({"message": "Harvest created successfully"}), 201

    except Exception as e:
        print(f"Internal Server Error: {e}")
        return jsonify({"error": "An unexpected internal server error occurred."}), 500


@app.route("/harvests", methods=["GET"]) 
def get_harvests():
    conn = None
    cursor = None
    try:
        conn = connect_oracle()
        cursor = conn.cursor()

        sql = """
        SELECT id, area, production, loss_percentage, lost_tonnage,
               net_production, productivity_per_hour, productivity_per_hectare,
               alert, recommendation, created_at
        FROM harvest
        ORDER BY created_at DESC
        """
        cursor.execute(sql)

        rows = cursor.fetchall()

        columns = [col[0].lower() for col in cursor.description]

        result_list = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                if isinstance(value, (datetime.date, datetime.datetime)):
                    row_dict[col_name] = value.isoformat()
                else:
                    row_dict[col_name] = value
            result_list.append(row_dict)


        return jsonify(result_list), 200

    except oracledb.DatabaseError as db_err:
        print(f"Oracle Database Error on GET /harvests: {db_err}")
        return jsonify({"error": "Failed to retrieve records from database."}), 500
    except ValueError as env_err:
         print(f"Configuration Error: {env_err}")
         return jsonify({"error": "Server configuration error."}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()   # Isso vai aparecer nos logs do Docker
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
