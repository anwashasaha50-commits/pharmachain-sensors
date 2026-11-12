"""Stream simulated readings, detect breaches, and report to the backend API."""
import argparse
import json
import os
import sys
import time
import requests
from detector import BreachDetector
from sensor_sim import SensorSimulator, DEFAULT_DURATION

WINDOWS_FILE = "anchored_windows.json"

def call(method, base, path, payload=None):
    try:
        r = requests.request(method, base + path, json=payload, timeout=15)
    except requests.exceptions.ConnectionError:
        sys.exit("Cannot reach the backend at %s. Is app.py running?" % base)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"ok": False, "error": r.text[:200]}

def save_window(batch_id, data_hash, readings):
    windows = []
    if os.path.exists(WINDOWS_FILE):
        with open(WINDOWS_FILE) as f:
            windows = json.load(f)
    windows.append({"batch_id": batch_id, "data_hash": data_hash, "readings": readings})
    with open(WINDOWS_FILE, "w") as f:
        json.dump(windows, f, indent=2)

def read_sensor(sim):
    """Swap this for real hardware later (see the guide). Must return the same dict."""
    return sim.read()

def main():
    p = argparse.ArgumentParser(description="PharmaChain cold-chain monitor")
    p.add_argument("--batch", required=True, help="batch ID to monitor, e.g. VAX-001")
    p.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://127.0.0.1:5000"))
    p.add_argument("--scenario", default="none", choices=["none"] + sorted(DEFAULT_DURATION))
    p.add_argument("--start-after", type=int, default=15, help="readings before the scenario begins")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    p.add_argument("--anchor-every", type=int, default=10, help="readings per anchored hash")
    p.add_argument("--max-readings", type=int, default=20)
    p.add_argument("--drug", default="Vaccine")
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()

    status, health = call("GET", a.backend, "/health")
    if not health.get("connected"):
        sys.exit("Backend is up but the blockchain is not connected: %s" % health)

    status, res = call(
        "POST",
        a.backend,
        "/register-batch",
        {"batch_id": a.batch, "drug_name": a.drug, "location": "Cold storage, Kolkata"},
    )
    if res.get("ok"):
        print("Registered batch %s on the ledger" % a.batch)
    elif "already registered" in res.get("error", ""):
        print("Batch is already registered, continuing")
    else:
        sys.exit("Could not register batch: %s" % res.get("error"))

    sim = SensorSimulator(seed=a.seed)
    if a.scenario != "none":
        sim.set_scenario(a.scenario, a.start_after)
    det = BreachDetector()
    window = []

    print("Monitoring %s (scenario: %s). Safe range 2-8 C.\n" % (a.batch, a.scenario))
    for n in range(1, a.max_readings + 1):
        reading = read_sensor(sim)
        anomalous, breach, forest, out_of_range = det.check(reading)
        window.append(reading)

        mark = "ANOMALY" if anomalous else "ok"
        why = (
            "(forest)"
            if forest and not out_of_range
            else (
                "(out of range)"
                if out_of_range and not forest
                else ("(forest+range)" if forest else "")
            )
        )
        print(
            "#%03d  %5.2f C  %4.1f%%  %-15s %s"
            % (n, reading["temp"], reading["humidity"], mark, why if anomalous else "")
        )

        if breach:
            recent = window[-a.anchor_every:]
            reason = (
                "Cold-chain breach: %d anomalous readings in a row, latest %.2fC"
                % (det.run, reading["temp"])
            )
            status, res = call(
                "POST",
                a.backend,
                "/report-anomaly",
                {"batch_id": a.batch, "reason": reason, "readings": recent},
            )
            if res.get("ok"):
                save_window(a.batch, res.get("anchored_hash"), recent)
                print("\nBREACH reported. Batch flagged on-chain: %s" % res.get("flagged"))
                print("Evidence hash anchored: %s" % res.get("anchored_hash"))
            else:
                print("\nCould not report breach: %s" % res.get("error"))
            return

        if n % a.anchor_every == 0:
            recent = window[-a.anchor_every:]
            status, res = call(
                "POST", a.backend, "/anchor-temp", {"batch_id": a.batch, "readings": recent}
            )
            if res.get("ok"):
                save_window(a.batch, res.get("data_hash"), recent)
                print("  -> anchored hash %s..." % res.get("data_hash")[:18])
            else:
                print("  -> anchor failed: %s" % res.get("error"))

        time.sleep(a.interval)

    print("\nFinished %d readings with no breach." % a.max_readings)

if __name__ == "__main__":
    main()
