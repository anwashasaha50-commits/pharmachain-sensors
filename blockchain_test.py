
from flask import Flask, request, jsonify
from eth_hash.auto import keccak
from web3 import Web3
import json

app = Flask(__name__)

# Connect to local Hardhat blockchain
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Smart contract address
contract_address = Web3.to_checksum_address(
    "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
)

# Load smart contract ABI
with open(
    "artifacts/contracts/ColdChainAudit.sol/ColdChainAudit.json",
    "r"
) as file:
    contract_json = json.load(file)

contract = w3.eth.contract(
    address=contract_address,
    abi=contract_json["abi"]
)

# Use the first unlocked Hardhat account
account = w3.eth.accounts[0]

# Store batch information in Python memory
batches = {}


def anchor(batch_id, readings, anomaly=False):
    raw_data = f"{batch_id}:{readings}".encode("utf-8")
    data_hash = keccak(raw_data).hex()

    last_tx_hash = None

    for reading in readings:
        temperature = int(round(float(reading.get("temp", 5)) * 100))
        humidity = int(round(float(reading.get("humidity", 60)) * 100))

        tx = contract.functions.logReading(
            batch_id,
            temperature,
            humidity,
            anomaly
        ).transact({"from": account})

        receipt = w3.eth.wait_for_transaction_receipt(tx)
        last_tx_hash = receipt["transactionHash"].hex()

    if batch_id not in batches:
        batches[batch_id] = {"status": "Genuine", "logs": []}

    batches[batch_id]["logs"].append({"data_hash": data_hash})

    return data_hash, last_tx_hash


@app.post("/register-batch")
def register_batch():
    d = request.get_json() or {}
    batch_id = d.get("batch_id")

    if not batch_id:
        return jsonify(ok=False, error="Missing batch_id"), 400

    batches.setdefault(
        batch_id,
        {"status": "Genuine", "logs": []}
    )

    return jsonify(ok=True)


@app.post("/anchor-temp")
def anchor_temp():
    d = request.get_json() or {}
    batch_id = d.get("batch_id")
    readings = d.get("readings")

    if not batch_id or readings is None:
        return jsonify(ok=False, error="Missing parameters"), 400

    try:
        h, tx_hash = anchor(batch_id, readings)

        return jsonify(
            ok=True,
            batch_id=batch_id,
            data_hash=h,
            tx_hash=tx_hash
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.post("/report-anomaly")
def report():
    d = request.get_json() or {}
    batch_id = d.get("batch_id")
    readings = d.get("readings", [])

    if not batch_id:
        return jsonify(ok=False, error="Missing batch_id"), 400

    try:
        h, tx_hash = anchor(batch_id, readings, anomaly=True)

        already = batches[batch_id]["status"] == "Compromised"
        batches[batch_id]["status"] = "Compromised"

        return jsonify(
            ok=True,
            flagged=not already,
            already_compromised=already,
            anchored_hash=h,
            tx_hash=tx_hash
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/verify/<batch_id>")
def verify(batch_id):
    if batch_id not in batches:
        return jsonify(ok=False, error="Batch not found"), 404

    b = batches[batch_id]

    count = contract.functions.getAuditTrailCount(batch_id).call()

    return jsonify(
        ok=True,
        verdict="COMPROMISED" if b["status"] == "Compromised" else "GENUINE",
        logs=b["logs"],
        blockchain_records=count
    )


@app.get("/health")
def health():
    connected = (
        w3.is_connected()
        and w3.eth.get_code(contract_address) != b""
    )

    return jsonify(
        ok=True,
        connected=connected,
        mode="blockchain" if connected else "disconnected"
    )


if __name__ == "__main__":
    app.run(port=5002)
