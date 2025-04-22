import json
import logging
import os
import tempfile

from config import HISTORY_FILE


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
        logging.warning(
            f"Could not read history file {history_file}: {e}. Starting fresh."
        )
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
            mode="w", dir=HISTORY_FILE.parent, delete=False, encoding="utf-8"
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
