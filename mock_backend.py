"""Tiny stand-in for Member 2's API so you can work without the blockchain."""
import json
from eth_hash.auto import keccak
from flask import Flask, jsonify, request

app = Flask(__name__)
batches = {}

@app.get("/health")
def health():
    return jsonify(ok=True, connected=True, contract="mock")

@app.post("/register-batch")
def register():
    d = request.get_json()
    if d["batch_id"] in batches:
        return jsonify(ok=False, error="Batch already registered"), 400
    batches[d["batch_id"]] = {"status": "Active", "logs": []}
    return jsonify(ok=True, batch_id=d["batch_id"], tx_hash="0xmock")

def anchor(batch_id, readings):
    payload = json.dumps(readings, separators=(",", ""), sort_keys=True)
    h = "0x" + keccak(payload.encode()).hex()
    batches[batch_id]["logs"].append({"data_hash": h})
    return h

@app.post("/anchor-temp")
def anchor_temp():
    d = request.get_json()
    return jsonify(
        ok=True,
        batch_id=d["batch_id"],
        data_hash=anchor(d["batch_id"], d["readings"]),
        tx_hash="0xmock",
    )

@app.post("/report-anomaly")
def report():
    d = request.get_json()
    h = anchor(d["batch_id"], d["readings"]) if d.get("readings") else None
    already = batches[d["batch_id"]]["status"] == "Compromised"
    batches[d["batch_id"]]["status"] = "Compromised"
    return jsonify(
        ok=True,
        flagged=not already,
        already_compromised=already,
        anchored_hash=h,
        tx_hash="0xmock",
    )

@app.get("/verify/<batch_id>")
def verify(batch_id):
    b = batches.get(batch_id)
    if not b:
        return jsonify(ok=False, verdict="NOT_FOUND", error="Batch not found"), 404
    return jsonify(
        ok=True,
        verdict="COMPROMISED" if b["status"] == "Compromised" else "GENUINE",
        temp_logs=b["logs"],
    )

if __name__ == "__main__":
    app.run(port=5000)