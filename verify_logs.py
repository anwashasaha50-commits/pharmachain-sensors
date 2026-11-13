
import argparse
import os
import sys
import requests
import json
import hashlib


from eth_hash.auto import keccak

def window_hash(batch_id, readings):
    raw_data = f"{batch_id}:{readings}".encode("utf-8")
    return keccak(raw_data).hex()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--batch", required=True)
    parser.add_argument("--backend", default="http://127.0.0.1:5001")
    parser.add_argument("--file", default="metrics.json")
    parser.add_argument("--tamper", action="store_true")

    a = parser.parse_args()

    # Check whether the JSON file exists
    if not os.path.exists(a.file):
        sys.exit(
            f"No {a.file} found. Run simulator.py first."
        )

    # Read saved windows from JSON file
    with open(a.file, "r") as f:
        data = json.load(f)

    windows = [
        w for w in data
        if isinstance(w, dict) and w.get("batch_id") == a.batch
    ]

    if not windows:
        sys.exit(
            f"No saved windows for batch {a.batch} in {a.file}"
        )

    # Fetch verification results from Flask backend
    try:
        response = requests.get(
            f"{a.backend}/verify/{a.batch}",
            timeout=10
        )
        response.raise_for_status()
        res = response.json()

    except requests.exceptions.RequestException as e:
        sys.exit(f"Backend connection error: {e}")

    except ValueError:
        sys.exit("Backend did not return valid JSON.")

    # Check backend response
    if not res.get("ok"):
        sys.exit(f"Backend says: {res.get('error', 'Unknown error')}")

    # Get hashes stored by the backend
    on_chain = {
        row["data_hash"].lower()
        for row in res.get("logs", [])
        if "data_hash" in row
    }

    print(f"Batch: {a.batch}")
    print(f"Backend verdict: {res.get('verdict', 'UNKNOWN')}")
    print(f"Stored hashes found: {len(on_chain)}")

    # Optional tampering test
    if a.tamper:
        windows[0]["readings"][0]["temp"] = 5.0
        print("Tamper mode: first reading changed to 5.0")

    # Verify each saved window
    bad = 0

    for i, w in enumerate(windows, 1):
        h = window_hash(a.batch, w["readings"]).lower()
        ok = h in on_chain

        if not ok:
            bad += 1

        print(
            f"Window {i}: {h[:22]}... "
            f"{'MATCH' if ok else 'MISMATCH'}"
        )

    # Final result
    if bad == 0:
        print("All logs match the stored hashes.")
    else:
        print(f"{bad} window(s) do NOT match.")
        print("The logs may have been altered or the hash calculation differs.")


if __name__ == "__main__":
    main()
