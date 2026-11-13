import argparse
import os
import sys
import json
import requests
from web3 import Web3


def window_hash(readings):
    payload = json.dumps(
        readings,
        separators=(",", ":"),
        sort_keys=True
    )
    return Web3.keccak(text=payload).hex().lower().removeprefix("0x")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument(
        "--backend",
        default="http://127.0.0.1:5003"
    )
    parser.add_argument(
        "--file",
        default="anchored_windows.json"
    )
    parser.add_argument("--tamper", action="store_true")
    a = parser.parse_args()

    if not os.path.exists(a.file):
        sys.exit(f"No {a.file} found. Run simulator.py first.")

    with open(a.file, "r") as f:
        data = json.load(f)

    windows = [
        w for w in data
        if isinstance(w, dict)
        and w.get("batch_id") == a.batch
    ]

    if not windows:
        sys.exit(f"No saved windows for batch {a.batch}")

    try:
        response = requests.get(
            f"{a.backend}/verify/{a.batch}",
            timeout=10
        )
        response.raise_for_status()
        res = response.json()
    except requests.exceptions.RequestException as e:
        sys.exit(f"Backend connection error: {e}")

    if not res.get("ok"):
        sys.exit(f"Backend says: {res.get('error', 'Unknown error')}")

    on_chain = {
        row["data_hash"].lower().removeprefix("0x")
        for row in res.get("temp_logs", [])
        if "data_hash" in row
    }

    print(f"Batch: {a.batch}")
    print(f"Backend verdict: {res.get('verdict', 'UNKNOWN')}")
    print(f"Stored hashes found: {len(on_chain)}")

    if a.tamper:
        windows[0]["readings"][0]["temp"] = 5.0
        print("Tamper mode: first reading changed to 5.0")

    bad = 0

    for i, w in enumerate(windows, 1):
        h = window_hash(w["readings"])
        ok = h in on_chain

        if not ok:
            bad += 1

        print(
            f"Window {i}: {h[:22]}... "
            f"{'MATCH' if ok else 'MISMATCH'}"
        )

    if bad == 0:
        print("All logs match the stored blockchain hashes.")
    else:
        print(f"{bad} window(s) do NOT match.")
        print("The logs may have been altered.")


if __name__ == "__main__":
    main()
