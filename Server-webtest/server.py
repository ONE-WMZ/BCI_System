from datetime import datetime
import logging
from uuid import uuid4

from flask import Flask, jsonify, render_template, request


app = Flask(__name__, template_folder=".")
records = []


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/data")
def get_data():
    return jsonify({"items": records, "count": len(records)})


@app.post("/api/data")
def data():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Send JSON data in the request body."}), 400
    record = {
        "id": uuid4().hex,
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    print(f"[{record['received_at']}] API Received data : {payload}", flush=True)
    records.insert(0, record)
    del records[100:]
    return jsonify({"status": "received", "id": record["id"]}), 201


if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print("\n")
    print("-"*70)
    print("page running:            | http://127.0.0.1:5000")
    print("HTTP Data receive API:   | http://127.0.0.1:5000/api/data")
    print("-"*70)
    print("\n")
    app.run(host="0.0.0.0", port=5000)
